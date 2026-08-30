#!/usr/bin/env node

/**
 * Production visual regression gate for the 65 managed child-service pages.
 *
 * The runner intentionally has no package.json dependency. It first tries the
 * Playwright bundled with Codex and then launches an installed Chrome/Edge.
 * Default run: 65 manifest URLs x desktop/mobile = 130 full-page screenshots.
 */

import assert from "node:assert/strict";
import { constants as fsConstants } from "node:fs";
import { access, mkdir, readFile, rename, rm, stat, writeFile } from "node:fs/promises";
import { createRequire } from "node:module";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";

const SCRIPT_PATH = fileURLToPath(import.meta.url);
const REPO_ROOT = path.resolve(path.dirname(SCRIPT_PATH), "..");
const EXPECTED_CHILD_COUNT = 65;
const DEFAULT_MANIFEST_PATH = path.join(
  REPO_ROOT,
  "seo-content",
  "service-hubs",
  "release-manifest.json",
);
const VIEWPORTS = Object.freeze([
  Object.freeze({ name: "desktop", width: 1440, height: 900, isMobile: false }),
  Object.freeze({ name: "mobile", width: 390, height: 844, isMobile: true }),
]);
const DEFAULT_TIMEOUT_MS = 45_000;
const DEFAULT_CONCURRENCY = 3;
const LAZY_IMAGE_WAIT_MAX_MS = 8_000;
const LAZY_IMAGE_POLL_MS = 100;

const FAILURE = Object.freeze({
  NAVIGATION: "navigation_failed",
  WRONG_ROUTE: "wrong_route",
  DOCUMENT_OVERFLOW: "document_overflow",
  SECTION_WIDTH: "section_not_full_width",
  SEO_WIDTH: "seo_width_mismatch",
  BACKGROUND_ALTERNATION: "background_not_alternating",
  FIXED_BACKGROUND: "fixed_background",
  FIXED_OR_STICKY: "unexpected_fixed_or_sticky",
  RELATED_GAP: "related_heading_gap",
  PRICE_READABILITY: "price_text_unreadable",
  CTA_MISSING: "cta_missing",
  CTA_LABEL: "cta_unlabelled",
  CTA_CARD: "cta_card_invalid",
  CTA_LAYOUT: "cta_layout_invalid",
  CTA_MOBILE_CONTROL: "cta_mobile_control_invalid",
  OVERLAP: "content_overlap",
  CONSOLE: "console_error",
  PAGE_ERROR: "page_error",
  REQUEST_FAILED: "request_failed",
  RESOURCE_HTTP: "resource_http_error",
  FAQ_MISSING: "faq_missing",
  FAQ_OPEN: "faq_not_opened",
  LAZY_IMAGE: "lazy_image_failed",
  SCREENSHOT: "screenshot_failed",
  AUDIT: "audit_exception",
});

function usage() {
  return `Usage: node tools/run_managed_child_visual_qa.mjs [options]

Runs the 65 child_service URLs from release-manifest.json at 1440x900 and
390x844, writes 130 full-page JPEGs, per-case checkpoints, and summary.json.

Options:
  --manifest PATH             Manifest path (default: ${DEFAULT_MANIFEST_PATH})
  --output-dir PATH           Artifact directory (default: timestamped)
  --base-url URL              Replace canonical origin, useful for staging
  --browser-executable PATH   Chrome/Edge/Chromium executable
  --concurrency N             Parallel pages (default: ${DEFAULT_CONCURRENCY})
  --timeout-ms N              Navigation timeout (default: ${DEFAULT_TIMEOUT_MS})
  --limit N                   Run the first N children (smoke/debug only)
  --headful                   Show browser windows
  --self-test                 Run deterministic unit checks and exit
  --help                      Show this message

Exit codes: 0 = all cases pass, 1 = visual/runtime RED, 2 = infrastructure error.`;
}

function timestampSlug(date = new Date()) {
  return date.toISOString().replace(/[:.]/g, "-");
}

function defaultOutputDir() {
  return path.join(
    REPO_ROOT,
    ".release-artifacts",
    `managed-child-visual-qa-${timestampSlug()}`,
  );
}

function parsePositiveInteger(value, optionName) {
  const parsed = Number(value);
  if (!Number.isSafeInteger(parsed) || parsed < 1) {
    throw new Error(`${optionName} must be a positive integer, got: ${value}`);
  }
  return parsed;
}

function parseArgs(argv) {
  const options = {
    manifestPath: DEFAULT_MANIFEST_PATH,
    outputDir: null,
    baseUrl: null,
    browserExecutable: null,
    concurrency: DEFAULT_CONCURRENCY,
    timeoutMs: DEFAULT_TIMEOUT_MS,
    limit: null,
    headless: true,
    selfTest: false,
    help: false,
  };

  const takeValue = (index, optionName) => {
    const value = argv[index + 1];
    if (!value || value.startsWith("--")) {
      throw new Error(`${optionName} requires a value`);
    }
    return value;
  };

  for (let index = 0; index < argv.length; index += 1) {
    const argument = argv[index];
    switch (argument) {
      case "--manifest":
        options.manifestPath = path.resolve(takeValue(index, argument));
        index += 1;
        break;
      case "--output-dir":
        options.outputDir = path.resolve(takeValue(index, argument));
        index += 1;
        break;
      case "--base-url": {
        const candidate = new URL(takeValue(index, argument));
        if (!/^https?:$/.test(candidate.protocol)) {
          throw new Error("--base-url must use http or https");
        }
        options.baseUrl = candidate.toString();
        index += 1;
        break;
      }
      case "--browser-executable":
        options.browserExecutable = path.resolve(takeValue(index, argument));
        index += 1;
        break;
      case "--concurrency":
        options.concurrency = parsePositiveInteger(takeValue(index, argument), argument);
        index += 1;
        break;
      case "--timeout-ms":
        options.timeoutMs = parsePositiveInteger(takeValue(index, argument), argument);
        index += 1;
        break;
      case "--limit":
        options.limit = parsePositiveInteger(takeValue(index, argument), argument);
        index += 1;
        break;
      case "--headful":
        options.headless = false;
        break;
      case "--self-test":
        options.selfTest = true;
        break;
      case "--help":
      case "-h":
        options.help = true;
        break;
      default:
        throw new Error(`Unknown option: ${argument}`);
    }
  }

  options.outputDir ||= defaultOutputDir();
  return options;
}

function normalizePathname(value) {
  const decoded = decodeURIComponent(value || "/");
  return decoded === "/" ? decoded : decoded.replace(/\/+$/, "");
}

function validateManagedChildInventory(manifest, expectedCount = EXPECTED_CHILD_COUNT) {
  if (!manifest || !Array.isArray(manifest.managed_pages)) {
    throw new Error("Manifest must contain a managed_pages array");
  }
  const children = manifest.managed_pages.filter(
    (page) => page && page.page_role === "child_service",
  );
  if (children.length !== expectedCount) {
    throw new Error(`Expected exactly ${expectedCount} child_service pages, found ${children.length}`);
  }

  const pageKeys = new Set();
  const canonicals = new Set();
  for (const [index, page] of children.entries()) {
    for (const field of ["page_key", "service_id", "canonical"]) {
      if (typeof page[field] !== "string" || page[field].trim() === "") {
        throw new Error(`child_service[${index}] has no valid ${field}`);
      }
    }
    let canonical;
    try {
      canonical = new URL(page.canonical);
    } catch {
      throw new Error(`Invalid canonical for ${page.page_key}: ${page.canonical}`);
    }
    if (!/^https?:$/.test(canonical.protocol)) {
      throw new Error(`Canonical must use http(s) for ${page.page_key}`);
    }
    if (pageKeys.has(page.page_key)) {
      throw new Error(`Duplicate child page_key: ${page.page_key}`);
    }
    const identity = `${canonical.origin}${normalizePathname(canonical.pathname)}`;
    if (canonicals.has(identity)) {
      throw new Error(`Duplicate child canonical: ${page.canonical}`);
    }
    pageKeys.add(page.page_key);
    canonicals.add(identity);
  }
  return children;
}

function sanitizeFilename(value) {
  const safe = String(value)
    .normalize("NFKD")
    .replace(/[^a-zA-Z0-9._-]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 120);
  return safe || "page";
}

function buildTestUrl(canonical, baseUrl) {
  const source = new URL(canonical);
  if (!baseUrl) return source.toString();
  const base = new URL(baseUrl);
  base.pathname = source.pathname;
  base.search = source.search;
  base.hash = source.hash;
  return base.toString();
}

function parseCssColor(value) {
  if (typeof value !== "string") return null;
  const match = value.trim().match(
    /^rgba?\(\s*([\d.]+)[,\s]+([\d.]+)[,\s]+([\d.]+)(?:\s*[,/]\s*([\d.]+))?\s*\)$/i,
  );
  if (!match) return null;
  return {
    r: Number(match[1]),
    g: Number(match[2]),
    b: Number(match[3]),
    a: match[4] === undefined ? 1 : Number(match[4]),
  };
}

function relativeLuminance(color) {
  const linearize = (channel) => {
    const normalized = channel / 255;
    return normalized <= 0.04045
      ? normalized / 12.92
      : ((normalized + 0.055) / 1.055) ** 2.4;
  };
  return 0.2126 * linearize(color.r)
    + 0.7152 * linearize(color.g)
    + 0.0722 * linearize(color.b);
}

function contrastRatio(first, second) {
  const high = Math.max(relativeLuminance(first), relativeLuminance(second));
  const low = Math.min(relativeLuminance(first), relativeLuminance(second));
  return (high + 0.05) / (low + 0.05);
}

function rectIntersectionArea(first, second) {
  const width = Math.max(0, Math.min(first.right, second.right) - Math.max(first.left, second.left));
  const height = Math.max(0, Math.min(first.bottom, second.bottom) - Math.max(first.top, second.top));
  return width * height;
}

function backgroundAlternationFailures(tokens) {
  const failures = [];
  if (tokens.length < 2 || new Set(tokens).size < 2) {
    failures.push("backgrounds_have_no_visual_variation");
  }
  for (let index = 1; index < tokens.length; index += 1) {
    if (tokens[index] === tokens[index - 1]) {
      failures.push(`sections_${index}_and_${index + 1}_repeat_surface`);
    }
  }
  return failures;
}

async function fileExists(candidate) {
  if (!candidate) return false;
  try {
    await access(candidate, fsConstants.X_OK);
    return (await stat(candidate)).isFile();
  } catch {
    return false;
  }
}

function playwrightModuleCandidates() {
  const candidates = ["playwright", path.resolve(
    path.dirname(process.execPath),
    "..",
    "node_modules",
    "playwright",
  )];
  for (const moduleRoot of (process.env.NODE_PATH || "").split(path.delimiter)) {
    if (moduleRoot.trim()) candidates.push(path.join(moduleRoot, "playwright"));
  }
  return [...new Set(candidates)];
}

function loadPlaywright() {
  const require = createRequire(import.meta.url);
  const failures = [];
  for (const candidate of playwrightModuleCandidates()) {
    try {
      return require(candidate);
    } catch (error) {
      failures.push(`${candidate}: ${error.code || error.message}`);
    }
  }
  throw new Error(
    `Playwright is unavailable. Tried:\n${failures.map((item) => `  - ${item}`).join("\n")}`,
  );
}

async function launchChromium(playwright, options) {
  const launchAttempts = [];
  const executableCandidates = [];
  if (options.browserExecutable) {
    if (!(await fileExists(options.browserExecutable))) {
      throw new Error(`Browser executable does not exist: ${options.browserExecutable}`);
    }
    executableCandidates.push({ executablePath: options.browserExecutable });
  } else {
    const bundledExecutable = playwright.chromium.executablePath();
    if (await fileExists(bundledExecutable)) {
      executableCandidates.push({ executablePath: bundledExecutable });
    }
    for (const systemExecutable of [
      "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
      "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
      "/usr/bin/google-chrome",
      "/usr/bin/chromium",
      "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    ]) {
      if (await fileExists(systemExecutable)) {
        executableCandidates.push({ executablePath: systemExecutable });
      }
    }
    executableCandidates.push({ channel: "chrome" }, { channel: "msedge" });
  }
  for (const candidate of executableCandidates) {
    try {
      const browser = await playwright.chromium.launch({
        ...candidate,
        headless: options.headless,
        args: ["--disable-dev-shm-usage", "--no-default-browser-check"],
      });
      return { browser, launchConfig: candidate };
    } catch (error) {
      launchAttempts.push(`${JSON.stringify(candidate)}: ${error.message}`);
    }
  }
  throw new Error(
    `Unable to launch Chromium/Chrome/Edge:\n${launchAttempts.map((item) => `  - ${item}`).join("\n")}`,
  );
}

async function writeJsonAtomic(targetPath, value) {
  await mkdir(path.dirname(targetPath), { recursive: true });
  const temporaryPath = `${targetPath}.${process.pid}.${Date.now()}.tmp`;
  try {
    await writeFile(temporaryPath, `${JSON.stringify(value, null, 2)}\n`, "utf8");
    await rename(temporaryPath, targetPath);
  } catch (error) {
    await rm(temporaryPath, { force: true }).catch(() => {});
    throw error;
  }
}

function uniqueFailures(failures) {
  const seen = new Set();
  return failures.filter((failure) => {
    const identity = `${failure.code}\u0000${failure.message}`;
    if (seen.has(identity)) return false;
    seen.add(identity);
    return true;
  });
}

function addFailure(failures, code, message, details = undefined) {
  failures.push({ code, message, ...(details === undefined ? {} : { details }) });
}

function lazyImageWaitBudget(timeoutMs) {
  return Math.max(1, Math.min(timeoutMs, LAZY_IMAGE_WAIT_MAX_MS));
}

function isDeferredImageState(state) {
  return Boolean(
    state.dataSrc
    || state.dataSrcset
    || state.lazyClass
    || state.lazyLoadedClass
    || state.nativeLazy
    || state.pictureDataSrcset,
  );
}

function pendingLazyImageStates(states) {
  return states.filter((state) => (
    state.rendered
    && state.deferred
    && (
      state.lazyClassPending
      || !state.complete
      || state.naturalWidth <= 1
      || state.naturalHeight <= 1
      || !state.currentSrc
      || /^data:image\//i.test(state.currentSrc)
    )
  ));
}

async function collectLazyImageStates(page) {
  const states = await page.evaluate(() => Array.from(document.images)
    .map((image, index) => {
      const classList = image.classList;
      const style = getComputedStyle(image);
      const rect = image.getBoundingClientRect();
      const currentSrc = image.currentSrc || image.getAttribute("src") || "";
      const dataSrc = image.getAttribute("data-src") || "";
      const dataSrcset = image.getAttribute("data-srcset") || "";
      return {
        index,
        label: image.getAttribute("alt") || dataSrc || currentSrc || `img[${index}]`,
        rendered: rect.width > 0
          && rect.height > 0
          && rect.right > 0
          && rect.left < window.innerWidth
          && style.display !== "none"
          && style.visibility !== "hidden",
        dataSrc,
        dataSrcset,
        lazyClass: classList.contains("lazyload"),
        lazyLoadedClass: classList.contains("lazyloaded"),
        nativeLazy: image.loading === "lazy",
        pictureDataSrcset: Boolean(
          image.closest("picture")?.querySelector("source[data-srcset]"),
        ),
        lazyClassPending: classList.contains("lazyload")
          && !classList.contains("lazyloaded"),
        complete: image.complete,
        currentSrc,
        naturalWidth: image.naturalWidth,
        naturalHeight: image.naturalHeight,
      };
    }));
  return states
    .map((state) => ({ ...state, deferred: isDeferredImageState(state) }))
    .filter((state) => state.deferred);
}

async function decodeLazyImages(page, timeoutMs) {
  return page.evaluate(async (waitMs) => {
    const images = Array.from(document.images).filter((image) => {
      const style = getComputedStyle(image);
      const rect = image.getBoundingClientRect();
      const currentSrc = image.currentSrc || image.getAttribute("src") || "";
      const deferred = image.hasAttribute("data-src")
        || image.hasAttribute("data-srcset")
        || image.classList.contains("lazyload")
        || image.classList.contains("lazyloaded")
        || image.loading === "lazy"
        || Boolean(image.closest("picture")?.querySelector("source[data-srcset]"));
      return deferred
        && rect.width > 0
        && rect.height > 0
        && rect.right > 0
        && rect.left < window.innerWidth
        && style.display !== "none"
        && style.visibility !== "hidden"
        && image.complete
        && image.naturalWidth > 1
        && image.naturalHeight > 1
        && !/^data:image\//i.test(currentSrc);
    });
    let timeoutId;
    const decodeResults = Promise.allSettled(images.map((image) => (
      typeof image.decode === "function" ? image.decode() : Promise.resolve()
    ))).then((results) => ({
      timedOut: false,
      rejected: results.filter((result) => result.status === "rejected").length,
    }));
    const timeout = new Promise((resolve) => {
      timeoutId = setTimeout(() => resolve({ timedOut: true, rejected: 0 }), waitMs);
    });
    const outcome = await Promise.race([decodeResults, timeout]);
    clearTimeout(timeoutId);
    return {
      candidateCount: images.length,
      ...outcome,
    };
  }, timeoutMs);
}

async function waitForLazyImages(page, timeoutMs) {
  const budgetMs = lazyImageWaitBudget(timeoutMs);
  const deadline = Date.now() + budgetMs;
  let states = [];

  while (true) {
    states = await collectLazyImageStates(page);
    const pending = pendingLazyImageStates(states);
    if (pending.length === 0) break;
    const remainingMs = deadline - Date.now();
    if (remainingMs <= 0) {
      const labels = pending.slice(0, 5).map((state) => state.label).join("; ");
      throw new Error(
        `Lazy images did not resolve within ${budgetMs} ms: ${labels}`,
      );
    }
    await page.waitForTimeout(Math.min(LAZY_IMAGE_POLL_MS, remainingMs));
  }

  const remainingMs = deadline - Date.now();
  if (remainingMs <= 0 && states.length > 0) {
    throw new Error(`Lazy image decode exceeded ${budgetMs} ms`);
  }
  const decode = await decodeLazyImages(page, Math.max(1, remainingMs));
  if (decode.timedOut) {
    throw new Error(`Lazy image decode exceeded ${budgetMs} ms`);
  }
  if (decode.rejected > 0) {
    throw new Error(`${decode.rejected} lazy image decode operation(s) failed`);
  }
  return {
    candidates: states.length,
    decoded: decode.candidateCount,
  };
}

async function preparePage(page, timeoutMs = DEFAULT_TIMEOUT_MS) {
  await page.addStyleTag({
    content: `
      *, *::before, *::after {
        animation-delay: 0s !important;
        animation-duration: 0s !important;
        caret-color: transparent !important;
        scroll-behavior: auto !important;
        transition: none !important;
      }
      [data-aos] {
        opacity: 1 !important;
        transform: none !important;
        visibility: visible !important;
      }
    `,
  });
  await page.evaluate(async () => {
    if (document.fonts?.ready) await document.fonts.ready;
    const step = Math.max(300, Math.floor(window.innerHeight * 0.75));
    for (let offset = 0; offset < document.documentElement.scrollHeight; offset += step) {
      window.scrollTo(0, offset);
      await new Promise((resolve) => setTimeout(resolve, 50));
    }
  });
  const lazyImages = await waitForLazyImages(page, timeoutMs);
  await page.evaluate(() => {
    window.scrollTo(0, 0);
  });
  await page.waitForTimeout(150);
  return lazyImages;
}

async function openFirstFaq(page) {
  const selector = [
    ".service-faq-item .service-faq-question",
    ".service-faq-item > summary",
    ".service-v2__faq-item > summary",
    "[data-qa='faq-item'] > summary",
  ].join(", ");
  const candidates = page.locator(selector);
  const count = await candidates.count();
  let trigger = null;
  for (let index = 0; index < count; index += 1) {
    const candidate = candidates.nth(index);
    if (await candidate.isVisible().catch(() => false)) {
      trigger = candidate;
      break;
    }
  }
  if (!trigger) return { present: false, opened: false, reason: "no visible FAQ trigger" };

  const readState = (element) => {
    const details = element.closest("details");
    const answer = details
      ? Array.from(details.children).find((child) => child !== element && child.tagName !== "SUMMARY")
      : element.nextElementSibling;
    const rect = answer?.getBoundingClientRect();
    return {
      detailsOpen: details?.open ?? null,
      answerVisible: Boolean(
        answer
        && rect
        && rect.height > 0
        && getComputedStyle(answer).display !== "none"
        && getComputedStyle(answer).visibility !== "hidden"
      ),
      answerHeight: rect?.height ?? 0,
    };
  };
  const before = await trigger.evaluate(readState);
  await trigger.click({ timeout: 5_000 });
  await page.waitForTimeout(120);
  const after = await trigger.evaluate(readState);
  return {
    present: true,
    opened: after.detailsOpen === true || after.answerVisible === true,
    before,
    after,
  };
}

async function collectDomAudit(page, mode) {
  return page.evaluate(({ auditMode }) => {
    const failures = [];
    const add = (code, message, details) => {
      failures.push({ code, message, ...(details === undefined ? {} : { details }) });
    };
    const round = (value, digits = 2) => Number(Number(value).toFixed(digits));
    const rectOf = (element) => {
      if (!element) return null;
      const rect = element.getBoundingClientRect();
      return {
        left: round(rect.left),
        right: round(rect.right),
        top: round(rect.top),
        bottom: round(rect.bottom),
        width: round(rect.width),
        height: round(rect.height),
      };
    };
    const isVisible = (element) => {
      if (!element) return false;
      const style = getComputedStyle(element);
      const rect = element.getBoundingClientRect();
      return rect.width > 0
        && rect.height > 0
        && style.display !== "none"
        && style.visibility !== "hidden"
        && Number.parseFloat(style.opacity || "1") > 0.01;
    };
    const describe = (element) => {
      if (!element) return "missing";
      if (element.id) return `${element.tagName.toLowerCase()}#${element.id}`;
      const classes = [...element.classList].slice(0, 3).join(".");
      return `${element.tagName.toLowerCase()}${classes ? `.${classes}` : ""}`;
    };
    const parseColor = (value) => {
      const match = String(value || "").trim().match(
        /^rgba?\(\s*([\d.]+)[,\s]+([\d.]+)[,\s]+([\d.]+)(?:\s*[,/]\s*([\d.]+))?\s*\)$/i,
      );
      if (!match) return null;
      return {
        r: Number(match[1]),
        g: Number(match[2]),
        b: Number(match[3]),
        a: match[4] === undefined ? 1 : Number(match[4]),
      };
    };
    const luminance = (color) => {
      const linearize = (channel) => {
        const normalized = channel / 255;
        return normalized <= 0.04045
          ? normalized / 12.92
          : ((normalized + 0.055) / 1.055) ** 2.4;
      };
      return 0.2126 * linearize(color.r)
        + 0.7152 * linearize(color.g)
        + 0.0722 * linearize(color.b);
    };
    const contrast = (first, second) => {
      const firstLum = luminance(first);
      const secondLum = luminance(second);
      return (Math.max(firstLum, secondLum) + 0.05) / (Math.min(firstLum, secondLum) + 0.05);
    };
    const intersectionArea = (first, second) => {
      if (!first || !second) return 0;
      const width = Math.max(0, Math.min(first.right, second.right) - Math.max(first.left, second.left));
      const height = Math.max(0, Math.min(first.bottom, second.bottom) - Math.max(first.top, second.top));
      return width * height;
    };
    const checkNoOverlap = (first, second, label) => {
      if (!isVisible(first) || !isVisible(second)) return;
      const firstRect = rectOf(first);
      const secondRect = rectOf(second);
      const area = intersectionArea(firstRect, secondRect);
      if (area > 2) {
        add("content_overlap", `${label} overlap by ${round(area)}px2`, {
          first: firstRect,
          second: secondRect,
        });
      }
    };
    const effectiveSurface = (element, boundary) => {
      for (let current = element; current; current = current.parentElement) {
        const style = getComputedStyle(current);
        const background = parseColor(style.backgroundColor);
        const hasImage = style.backgroundImage !== "none";
        if (hasImage && (!background || background.a < 0.92)) {
          return {
            safe: false,
            reason: `pattern/image without opaque text surface at ${describe(current)}`,
            backgroundImage: style.backgroundImage,
            backgroundColor: style.backgroundColor,
          };
        }
        if (background && background.a >= 0.92) {
          return { safe: true, color: background, source: describe(current) };
        }
        if (current === boundary) break;
      }
      const bodyBackground = parseColor(getComputedStyle(document.body).backgroundColor);
      if (bodyBackground && bodyBackground.a >= 0.92) {
        return { safe: true, color: bodyBackground, source: "body" };
      }
      return { safe: false, reason: "no opaque background surface found" };
    };
    const labelled = (control) => {
      if (!control) return false;
      if (control.labels && [...control.labels].some((label) => label.textContent.trim())) return true;
      if (control.getAttribute("aria-label")?.trim()) return true;
      const labelledBy = control.getAttribute("aria-labelledby");
      return Boolean(
        labelledBy
        && labelledBy.split(/\s+/).some((id) => document.getElementById(id)?.textContent.trim()),
      );
    };

    const root = document.querySelector(".managed-service-child");
    if (!root) {
      add("managed_child_template_missing", "Expected .managed-service-child root was not rendered");
      return {
        failures,
        metrics: {
          viewport: { width: innerWidth, height: innerHeight },
          document: {
            clientWidth: document.documentElement.clientWidth,
            scrollWidth: document.documentElement.scrollWidth,
          },
        },
      };
    }

    const viewportWidth = document.documentElement.clientWidth;
    const documentWidth = document.documentElement.scrollWidth;
    if (documentWidth > viewportWidth + 2) {
      add(
        "document_overflow",
        `Document is ${round(documentWidth - viewportWidth)}px wider than the viewport`,
        { viewportWidth, documentWidth },
      );
    }

    let sections = [...root.querySelectorAll(":scope > section.managed-service-child__section")]
      .filter(isVisible);
    if (sections.length === 0) {
      sections = [...root.querySelectorAll("section.managed-service-child__section")].filter(isVisible);
    }
    const sectionMetrics = sections.map((section, index) => {
      const style = getComputedStyle(section);
      const rect = rectOf(section);
      const widthRatio = rect.width / viewportWidth;
      const backgroundKind = style.backgroundImage !== "none" ? "pattern" : "solid";
      if (widthRatio < 0.95 || rect.left > 3 || rect.right < viewportWidth - 3) {
        add(
          "section_not_full_width",
          `Section ${index + 1} (${describe(section)}) covers only ${round(widthRatio * 100)}% of viewport`,
          { rect, viewportWidth, widthRatio: round(widthRatio, 4) },
        );
      }
      if (style.backgroundAttachment.split(",").some((value) => value.trim() === "fixed")) {
        add(
          "fixed_background",
          `Section ${index + 1} uses background-attachment: fixed`,
          { selector: describe(section), backgroundAttachment: style.backgroundAttachment },
        );
      }
      return {
        index: index + 1,
        selector: describe(section),
        rect,
        widthRatio: round(widthRatio, 4),
        backgroundKind,
        backgroundToken: `${style.backgroundImage}|${style.backgroundColor}`,
        backgroundColor: style.backgroundColor,
        backgroundImage: style.backgroundImage,
        backgroundAttachment: style.backgroundAttachment,
      };
    });

    const backgroundKinds = sectionMetrics.map((section) => section.backgroundKind);
    const backgroundTokens = sectionMetrics.map((section) => section.backgroundToken);
    if (backgroundKinds.length < 2 || new Set(backgroundKinds).size < 2) {
      add(
        "background_not_alternating",
        "Managed sections do not contain both plain and patterned surfaces",
        { backgroundKinds },
      );
    }
    for (let index = 1; index < backgroundTokens.length; index += 1) {
      if (backgroundTokens[index] === backgroundTokens[index - 1]) {
        add(
          "background_not_alternating",
          `Sections ${index} and ${index + 1} repeat the same background surface`,
          { previous: sectionMetrics[index - 1], current: sectionMetrics[index] },
        );
      }
    }

    const solution = root.querySelector(".solution-block");
    const seo = root.querySelector(".seo-text");
    let seoWidth = null;
    if (!isVisible(solution) || !isVisible(seo)) {
      add("seo_width_mismatch", "Both .solution-block and .seo-text must be visible");
    } else {
      const solutionRect = rectOf(solution);
      const seoRect = rectOf(seo);
      const ratio = seoRect.width / solutionRect.width;
      const edgeTolerance = auditMode === "mobile" ? 4 : 8;
      seoWidth = {
        solution: solutionRect,
        seo: seoRect,
        ratio: round(ratio, 4),
        leftDelta: round(Math.abs(seoRect.left - solutionRect.left)),
        rightDelta: round(Math.abs(seoRect.right - solutionRect.right)),
      };
      if (ratio < 0.95 || seoWidth.leftDelta > edgeTolerance || seoWidth.rightDelta > edgeTolerance) {
        add(
          "seo_width_mismatch",
          `.seo-text is ${round(ratio * 100)}% of .solution-block width or has mismatched edges`,
          seoWidth,
        );
      }
    }

    const positioned = [...root.querySelectorAll("*")]
      .filter(isVisible)
      .filter((element) => ["fixed", "sticky"].includes(getComputedStyle(element).position))
      .map((element) => ({
        selector: describe(element),
        position: getComputedStyle(element).position,
        text: element.textContent.trim().slice(0, 100),
      }));
    if (positioned.length > 0) {
      add(
        "unexpected_fixed_or_sticky",
        `${positioned.length} visible managed-content element(s) use fixed/sticky positioning`,
        positioned.slice(0, 20),
      );
    }

    for (let index = 1; index < sections.length; index += 1) {
      checkNoOverlap(sections[index - 1], sections[index], `sections ${index}/${index + 1}`);
    }
    for (const grid of root.querySelectorAll(".services__cards, [data-qa='card-grid']")) {
      const cards = [...grid.children].filter(isVisible);
      for (let first = 0; first < cards.length; first += 1) {
        for (let second = first + 1; second < cards.length; second += 1) {
          checkNoOverlap(cards[first], cards[second], `${describe(grid)} cards ${first + 1}/${second + 1}`);
        }
      }
    }

    const related = root.querySelector(
      ".service-related-services, [data-section='related-services'], .managed-child-related-services",
    );
    let relatedGap = null;
    if (!isVisible(related)) {
      add("related_heading_gap", "Related-services section is missing or hidden");
    } else {
      const heading = related.querySelector(":scope > h2, [data-qa='related-heading']");
      const grid = related.querySelector(".services__cards, [data-qa='related-grid']");
      if (!isVisible(heading) || !isVisible(grid)) {
        add("related_heading_gap", "Related-services heading or grid is missing");
      } else {
        const headingRect = rectOf(heading);
        const gridRect = rectOf(grid);
        const gap = gridRect.top - headingRect.bottom;
        const minimumGap = auditMode === "mobile" ? 16 : 24;
        relatedGap = {
          gap: round(gap),
          minimumGap,
          heading: headingRect,
          grid: gridRect,
        };
        if (gap < minimumGap) {
          add(
            "related_heading_gap",
            `Related heading-to-grid gap is ${round(gap)}px; expected at least ${minimumGap}px`,
            relatedGap,
          );
        }
        checkNoOverlap(heading, grid, "related heading/grid");
      }
    }

    const priceSection = root.querySelector(
      ".service-price-section, [data-section='price'], .managed-child-price",
    );
    const priceReadability = [];
    if (!isVisible(priceSection)) {
      add("price_text_unreadable", "Price section is missing or hidden");
    } else {
      const priceTexts = [
        priceSection.querySelector("h2, [data-qa='price-heading']"),
        priceSection.querySelector(".service-price-factors__lead, [data-qa='price-lead']"),
      ].filter(isVisible);
      if (priceTexts.length < 2) {
        add("price_text_unreadable", "Visible price heading and lead are both required");
      }
      for (const textElement of priceTexts) {
        const style = getComputedStyle(textElement);
        const foreground = parseColor(style.color);
        const surface = effectiveSurface(textElement, priceSection);
        const fontSize = Number.parseFloat(style.fontSize);
        const fontWeight = Number.parseInt(style.fontWeight, 10) || 400;
        const isLarge = fontSize >= 24 || (fontSize >= 18.66 && fontWeight >= 700);
        const requiredContrast = isLarge ? 3 : 4.5;
        const ratio = surface.safe && foreground ? contrast(foreground, surface.color) : null;
        const metric = {
          selector: describe(textElement),
          foreground: style.color,
          fontSize: round(fontSize),
          fontWeight,
          requiredContrast,
          contrastRatio: ratio === null ? null : round(ratio),
          surface,
        };
        priceReadability.push(metric);
        if (!surface.safe || !foreground || ratio < requiredContrast) {
          add(
            "price_text_unreadable",
            `${describe(textElement)} lacks a readable opaque surface or sufficient contrast`,
            metric,
          );
        }
      }
      const priceHeading = priceSection.querySelector("h2, [data-qa='price-heading']");
      const priceLead = priceSection.querySelector(".service-price-factors__lead, [data-qa='price-lead']");
      const priceFactors = priceSection.querySelector(".service-price-factors, [data-qa='price-grid']");
      checkNoOverlap(priceHeading, priceLead, "price heading/lead");
      checkNoOverlap(priceLead, priceFactors, "price lead/factors");
    }

    const faqSection = root.querySelector(".service-faq-section, [data-section='faq']");
    if (isVisible(faqSection)) {
      checkNoOverlap(
        faqSection.querySelector(".service-faq-title, :scope > h2"),
        faqSection.querySelector(".service-faq-list, [data-qa='faq-list']"),
        "FAQ heading/list",
      );
    }

    const cta = root.querySelector(
      ".service-v2__cta, .managed-child-cta, .managed-service-cta, [data-section='cta']",
    );
    const ctaMetrics = { present: isVisible(cta) };
    if (!isVisible(cta)) {
      add("cta_missing", "Managed child CTA section is missing or hidden");
    } else {
      const inner = cta.querySelector(
        ".service-v2__cta-inner, .managed-child-cta__inner, .managed-service-cta__inner, [data-qa='cta-inner']",
      );
      const copy = cta.querySelector(
        ".managed-service-child__cta-copy, .managed-child-cta__copy, .managed-service-cta__copy, [data-qa='cta-copy'], .service-v2__cta-inner > div:first-child",
      );
      const card = cta.querySelector(
        ".service-v2__form-wrapper, .managed-child-cta__form-card, .managed-service-cta__form-card, [data-qa='cta-card'], .formWrapper",
      );
      const form = cta.querySelector("form.service-v2__form, form.cta-form, form");
      const nameInput = form?.querySelector("input[name='name'], input[autocomplete='name']");
      const phoneInput = form?.querySelector("input[name='phone'], input[type='tel'], input[autocomplete='tel']");
      const consent = form?.querySelector("input[name='consent'], input[type='checkbox']");
      const submit = form?.querySelector("button[type='submit'], input[type='submit']");
      const requiredElements = { inner, copy, card, form, nameInput, phoneInput, consent, submit };
      const missing = Object.entries(requiredElements)
        .filter(([, element]) => !isVisible(element))
        .map(([name]) => name);
      if (missing.length > 0) {
        add("cta_missing", `CTA lacks visible required elements: ${missing.join(", ")}`, { missing });
      }

      const unlabelled = [nameInput, phoneInput, consent]
        .filter((control) => isVisible(control) && !labelled(control))
        .map(describe);
      if (unlabelled.length > 0) {
        add(
          "cta_unlabelled",
          `CTA controls need visible/accessible labels: ${unlabelled.join(", ")}`,
          { unlabelled },
        );
      }

      if (isVisible(card)) {
        const style = getComputedStyle(card);
        const background = parseColor(style.backgroundColor);
        const padding = [style.paddingTop, style.paddingRight, style.paddingBottom, style.paddingLeft]
          .map(Number.parseFloat);
        const framed = style.boxShadow !== "none"
          || [style.borderTopWidth, style.borderRightWidth, style.borderBottomWidth, style.borderLeftWidth]
            .some((value) => Number.parseFloat(value) > 0);
        ctaMetrics.card = {
          backgroundColor: style.backgroundColor,
          padding: padding.map((value) => round(value)),
          boxShadow: style.boxShadow,
          framed,
        };
        if (!background || background.a < 0.9 || Math.min(...padding) < 16 || !framed) {
          add(
            "cta_card_invalid",
            "CTA form must sit on an opaque, padded, visibly framed card",
            ctaMetrics.card,
          );
        }
      }

      if (isVisible(inner) && isVisible(copy) && isVisible(card)) {
        const innerStyle = getComputedStyle(inner);
        const copyRect = rectOf(copy);
        const cardRect = rectOf(card);
        const innerRect = rectOf(inner);
        ctaMetrics.layout = {
          display: innerStyle.display,
          inner: innerRect,
          copy: copyRect,
          card: cardRect,
        };
        if (!["grid", "flex", "inline-grid", "inline-flex"].includes(innerStyle.display)) {
          add("cta_layout_invalid", `CTA inner display is ${innerStyle.display}, expected grid/flex`);
        }
        checkNoOverlap(copy, card, "CTA copy/card");
        if (auditMode === "desktop") {
          const horizontalGap = Math.max(cardRect.left - copyRect.right, copyRect.left - cardRect.right);
          if (horizontalGap < 16 || copyRect.width < innerRect.width * 0.25 || cardRect.width < innerRect.width * 0.25) {
            add(
              "cta_layout_invalid",
              "Desktop CTA copy and form card must form two substantial columns with >=16px gap",
              { horizontalGap: round(horizontalGap), ...ctaMetrics.layout },
            );
          }
        } else {
          const verticalGap = cardRect.top - copyRect.bottom;
          if (verticalGap < 16 || cardRect.top <= copyRect.top) {
            add(
              "cta_layout_invalid",
              "Mobile CTA form card must stack below copy with >=16px gap",
              { verticalGap: round(verticalGap), ...ctaMetrics.layout },
            );
          }
        }
      }

      if (auditMode === "mobile" && isVisible(form)) {
        const formRect = rectOf(form);
        const controls = [nameInput, phoneInput, submit].filter(isVisible);
        const invalidControls = controls.map((control) => {
          const rect = rectOf(control);
          return {
            selector: describe(control),
            rect,
            widthRatio: round(rect.width / formRect.width, 4),
            valid: rect.width / formRect.width >= 0.9 && rect.height >= 44,
          };
        }).filter((control) => !control.valid);
        ctaMetrics.mobileControls = controls.length;
        if (invalidControls.length > 0 || controls.length < 3) {
          add(
            "cta_mobile_control_invalid",
            "Mobile name/phone/submit controls must be >=90% form width and >=44px high",
            { form: formRect, invalidControls, controlsFound: controls.length },
          );
        }
      }
    }

    return {
      failures,
      metrics: {
        viewport: { width: innerWidth, height: innerHeight, mode: auditMode },
        document: {
          clientWidth: viewportWidth,
          scrollWidth: documentWidth,
          scrollHeight: document.documentElement.scrollHeight,
        },
        managedSections: sectionMetrics,
        seoWidth,
        positioned,
        relatedGap,
        priceReadability,
        cta: ctaMetrics,
      },
    };
  }, { auditMode: mode });
}

function attachTelemetry(page, testUrl) {
  const targetOrigin = new URL(testUrl).origin;
  const telemetry = {
    consoleErrors: [],
    pageErrors: [],
    requestFailures: [],
    httpErrors: [],
  };
  page.on("console", (message) => {
    if (message.type() === "error") {
      telemetry.consoleErrors.push({ text: message.text(), location: message.location() });
    }
  });
  page.on("pageerror", (error) => {
    telemetry.pageErrors.push({ name: error.name, message: error.message, stack: error.stack });
  });
  page.on("requestfailed", (request) => {
    try {
      if (new URL(request.url()).origin === targetOrigin) {
        telemetry.requestFailures.push({
          url: request.url(),
          method: request.method(),
          failure: request.failure()?.errorText || "unknown request failure",
        });
      }
    } catch {
      // Ignore browser-internal or malformed URLs.
    }
  });
  page.on("response", (response) => {
    try {
      if (new URL(response.url()).origin === targetOrigin && response.status() >= 400) {
        telemetry.httpErrors.push({ url: response.url(), status: response.status() });
      }
    } catch {
      // Ignore browser-internal or malformed URLs.
    }
  });
  return telemetry;
}

function telemetryFailures(telemetry) {
  const failures = [];
  if (telemetry.consoleErrors.length > 0) {
    addFailure(
      failures,
      FAILURE.CONSOLE,
      `${telemetry.consoleErrors.length} console error(s)`,
      telemetry.consoleErrors,
    );
  }
  if (telemetry.pageErrors.length > 0) {
    addFailure(
      failures,
      FAILURE.PAGE_ERROR,
      `${telemetry.pageErrors.length} uncaught page error(s)`,
      telemetry.pageErrors,
    );
  }
  if (telemetry.requestFailures.length > 0) {
    addFailure(
      failures,
      FAILURE.REQUEST_FAILED,
      `${telemetry.requestFailures.length} first-party request failure(s)`,
      telemetry.requestFailures,
    );
  }
  if (telemetry.httpErrors.length > 0) {
    addFailure(
      failures,
      FAILURE.RESOURCE_HTTP,
      `${telemetry.httpErrors.length} first-party HTTP error response(s)`,
      telemetry.httpErrors,
    );
  }
  return failures;
}

async function runCase(browser, job, options, outputPaths) {
  const startedAt = new Date();
  const testUrl = buildTestUrl(job.page.canonical, options.baseUrl);
  const screenshotFilename = `${String(job.order).padStart(3, "0")}-${sanitizeFilename(job.page.page_key)}-${job.viewport.name}.jpg`;
  const checkpointFilename = screenshotFilename.replace(/\.jpg$/, ".json");
  const screenshotPath = path.join(outputPaths.screenshots, screenshotFilename);
  const checkpointPath = path.join(outputPaths.checkpoints, checkpointFilename);
  const failures = [];
  let context;
  let page;
  let responseStatus = null;
  let finalUrl = null;
  let metrics = null;
  let faq = null;
  let telemetry = {
    consoleErrors: [],
    pageErrors: [],
    requestFailures: [],
    httpErrors: [],
  };
  let screenshotCreated = false;

  try {
    context = await browser.newContext({
      viewport: { width: job.viewport.width, height: job.viewport.height },
      deviceScaleFactor: 1,
      locale: "ru-RU",
      colorScheme: "light",
      reducedMotion: "reduce",
      serviceWorkers: "block",
      ignoreHTTPSErrors: false,
      isMobile: false,
      hasTouch: job.viewport.isMobile,
    });
    page = await context.newPage();
    page.setDefaultTimeout(Math.min(options.timeoutMs, 15_000));
    telemetry = attachTelemetry(page, testUrl);

    let response;
    try {
      response = await page.goto(testUrl, {
        waitUntil: "domcontentloaded",
        timeout: options.timeoutMs,
      });
      responseStatus = response?.status() ?? null;
      finalUrl = page.url();
      if (!response || responseStatus < 200 || responseStatus >= 400) {
        addFailure(
          failures,
          FAILURE.NAVIGATION,
          `Navigation returned ${responseStatus ?? "no HTTP response"}`,
        );
      }
    } catch (error) {
      finalUrl = page.url();
      addFailure(failures, FAILURE.NAVIGATION, error.message);
    }

    if (finalUrl && /^https?:/i.test(finalUrl)) {
      const expectedPath = normalizePathname(new URL(testUrl).pathname);
      const actualPath = normalizePathname(new URL(finalUrl).pathname);
      if (actualPath !== expectedPath) {
        addFailure(
          failures,
          FAILURE.WRONG_ROUTE,
          `Expected route ${expectedPath}, landed on ${actualPath}`,
          { expectedPath, actualPath, finalUrl },
        );
      }
    }

    if (!failures.some((failure) => failure.code === FAILURE.NAVIGATION)) {
      await page.waitForLoadState("networkidle", { timeout: Math.min(options.timeoutMs, 8_000) })
        .catch(() => {});
      try {
        await preparePage(page, options.timeoutMs);
      } catch (error) {
        addFailure(failures, FAILURE.LAZY_IMAGE, error.message, { stack: error.stack });
        await page.evaluate(() => window.scrollTo(0, 0)).catch(() => {});
        await page.waitForTimeout(150).catch(() => {});
      }
      faq = await openFirstFaq(page).catch((error) => ({
        present: true,
        opened: false,
        reason: error.message,
      }));
      if (!faq.present) {
        addFailure(failures, FAILURE.FAQ_MISSING, faq.reason);
      } else if (!faq.opened) {
        addFailure(failures, FAILURE.FAQ_OPEN, faq.reason || "FAQ answer did not become visible");
      }

      try {
        const domAudit = await collectDomAudit(page, job.viewport.name);
        metrics = domAudit.metrics;
        failures.push(...domAudit.failures);
      } catch (error) {
        addFailure(failures, FAILURE.AUDIT, error.message, { stack: error.stack });
      }
    }

    failures.push(...telemetryFailures(telemetry));
  } catch (error) {
    addFailure(failures, FAILURE.AUDIT, error.message, { stack: error.stack });
  } finally {
    if (page) {
      try {
        await page.screenshot({
          path: screenshotPath,
          type: "jpeg",
          quality: 82,
          fullPage: true,
          animations: "disabled",
          timeout: options.timeoutMs,
        });
        screenshotCreated = true;
      } catch (error) {
        addFailure(failures, FAILURE.SCREENSHOT, error.message);
      }
    } else {
      addFailure(failures, FAILURE.SCREENSHOT, "Page was not created");
    }
    await context?.close().catch(() => {});
  }

  const finishedAt = new Date();
  const result = {
    pageKey: job.page.page_key,
    serviceId: job.page.service_id,
    canonical: job.page.canonical,
    testUrl,
    mode: job.viewport.name,
    viewport: { width: job.viewport.width, height: job.viewport.height },
    status: responseStatus,
    finalUrl,
    startedAt: startedAt.toISOString(),
    finishedAt: finishedAt.toISOString(),
    durationMs: finishedAt.getTime() - startedAt.getTime(),
    pass: false,
    screenshotCreated,
    screenshot: path.relative(options.outputDir, screenshotPath).replaceAll("\\", "/"),
    checkpoint: path.relative(options.outputDir, checkpointPath).replaceAll("\\", "/"),
    failures: uniqueFailures(failures),
    faq,
    metrics,
    telemetry,
  };
  result.pass = result.failures.length === 0 && result.screenshotCreated;
  await writeJsonAtomic(checkpointPath, result);
  return result;
}

function buildJobs(pages) {
  const jobs = [];
  let order = 1;
  for (const page of pages) {
    for (const viewport of VIEWPORTS) {
      jobs.push({ order, page, viewport });
      order += 1;
    }
  }
  return jobs;
}

async function runWorkerPool(jobs, concurrency, handler) {
  const results = new Array(jobs.length);
  let nextIndex = 0;
  async function worker() {
    while (true) {
      const index = nextIndex;
      nextIndex += 1;
      if (index >= jobs.length) return;
      results[index] = await handler(jobs[index], index);
    }
  }
  await Promise.all(
    Array.from({ length: Math.min(concurrency, jobs.length) }, () => worker()),
  );
  return results;
}

function summarizeResults(results, context) {
  const finishedAt = new Date();
  const failureCodes = {};
  for (const result of results) {
    for (const failure of result.failures) {
      failureCodes[failure.code] = (failureCodes[failure.code] || 0) + 1;
    }
  }
  const passed = results.filter((result) => result.pass).length;
  const screenshotsCreated = results.filter((result) => result.screenshotCreated).length;
  return {
    schemaVersion: 1,
    runner: "tools/run_managed_child_visual_qa.mjs",
    releaseId: context.releaseId,
    startedAt: context.startedAt.toISOString(),
    finishedAt: finishedAt.toISOString(),
    durationMs: finishedAt.getTime() - context.startedAt.getTime(),
    manifestPath: context.manifestPath,
    baseUrl: context.baseUrl,
    browser: context.browser,
    inventory: {
      manifestChildServices: context.inventoryCount,
      selectedChildServices: context.selectedCount,
      viewports: VIEWPORTS.map(({ name, width, height }) => ({ name, width, height })),
      expectedCases: context.selectedCount * VIEWPORTS.length,
      fullReleaseExpectedCases: EXPECTED_CHILD_COUNT * VIEWPORTS.length,
    },
    completedCases: results.length,
    passedCases: passed,
    failedCases: results.length - passed,
    screenshotsExpected: results.length,
    screenshotsCreated,
    failureCodes,
    pass: results.length === context.selectedCount * VIEWPORTS.length
      && passed === results.length
      && screenshotsCreated === results.length,
    cases: results,
  };
}

async function readManifest(manifestPath) {
  let source;
  try {
    source = await readFile(manifestPath, "utf8");
  } catch (error) {
    throw new Error(`Cannot read manifest ${manifestPath}: ${error.message}`);
  }
  try {
    return JSON.parse(source);
  } catch (error) {
    throw new Error(`Invalid JSON in ${manifestPath}: ${error.message}`);
  }
}

async function runSelfTest() {
  const options = parseArgs([
    "--manifest", "relative-manifest.json",
    "--output-dir", "relative-output",
    "--concurrency", "4",
    "--limit", "2",
    "--timeout-ms", "1000",
    "--base-url", "https://staging.example.test/",
  ]);
  assert.equal(options.concurrency, 4);
  assert.equal(options.limit, 2);
  assert.equal(options.timeoutMs, 1_000);
  assert.equal(options.baseUrl, "https://staging.example.test/");
  assert.equal(sanitizeFilename("S1 / strange:? key"), "S1-strange-key");
  assert.equal(normalizePathname("/some/path///"), "/some/path");
  assert.equal(
    buildTestUrl("https://exp76.ru/path/?q=1", "https://stage.example.test/"),
    "https://stage.example.test/path/?q=1",
  );

  const black = parseCssColor("rgb(0, 0, 0)");
  const white = parseCssColor("rgba(255, 255, 255, 1)");
  assert.ok(black && white);
  assert.ok(Math.abs(contrastRatio(black, white) - 21) < 0.001);
  assert.equal(
    rectIntersectionArea(
      { left: 0, right: 10, top: 0, bottom: 10 },
      { left: 5, right: 15, top: 5, bottom: 15 },
    ),
    25,
  );
  assert.deepEqual(
    backgroundAlternationFailures(["none|white", "sb5|soft", "none|white", "casebg|soft"]),
    [],
  );
  assert.equal(backgroundAlternationFailures(["none|white", "none|white"]).length, 2);

  const lazyImageStates = [
    {
      label: "viewport placeholder",
      rendered: true,
      deferred: true,
      lazyClassPending: true,
      complete: true,
      currentSrc: "data:image/gif;base64,placeholder",
      naturalWidth: 1,
      naturalHeight: 1,
    },
    {
      label: "decoded image",
      rendered: true,
      deferred: true,
      lazyClassPending: false,
      complete: true,
      currentSrc: "https://example.test/ready.webp",
      naturalWidth: 1600,
      naturalHeight: 1000,
    },
    {
      label: "hidden admin image",
      rendered: false,
      deferred: true,
      lazyClassPending: true,
      complete: true,
      currentSrc: "data:image/gif;base64,placeholder",
      naturalWidth: 1,
      naturalHeight: 1,
    },
  ];
  assert.deepEqual(
    pendingLazyImageStates(lazyImageStates).map((state) => state.label),
    ["viewport placeholder"],
  );
  assert.equal(lazyImageWaitBudget(45_000), 8_000);
  assert.equal(lazyImageWaitBudget(1_250), 1_250);
  assert.equal(isDeferredImageState({ nativeLazy: true }), true);
  assert.equal(isDeferredImageState({ pictureDataSrcset: true }), true);
  assert.equal(isDeferredImageState({}), false);

  const actualManifest = await readManifest(DEFAULT_MANIFEST_PATH);
  const children = validateManagedChildInventory(actualManifest);
  assert.equal(children.length, EXPECTED_CHILD_COUNT);
  assert.equal(new Set(children.map((page) => page.page_key)).size, EXPECTED_CHILD_COUNT);

  const invalidManifest = {
    managed_pages: [
      {
        page_role: "child_service",
        page_key: "same",
        service_id: "S",
        canonical: "https://example.test/a",
      },
      {
        page_role: "child_service",
        page_key: "same",
        service_id: "S",
        canonical: "https://example.test/b",
      },
    ],
  };
  assert.throws(() => validateManagedChildInventory(invalidManifest, 2), /Duplicate child page_key/);
  process.stdout.write(`SELF-TEST PASS: manifest contains ${children.length} unique managed child pages\n`);
}

async function run(options) {
  const startedAt = new Date();
  const outputPaths = {
    screenshots: path.join(options.outputDir, "screenshots", "children"),
    checkpoints: path.join(options.outputDir, "checkpoints"),
    summary: path.join(options.outputDir, "summary.json"),
  };
  await Promise.all([
    mkdir(outputPaths.screenshots, { recursive: true }),
    mkdir(outputPaths.checkpoints, { recursive: true }),
  ]);

  const manifest = await readManifest(options.manifestPath);
  const allChildren = validateManagedChildInventory(manifest);
  const selectedChildren = options.limit
    ? allChildren.slice(0, Math.min(options.limit, allChildren.length))
    : allChildren;
  const jobs = buildJobs(selectedChildren);
  let browser;
  let launchConfig = null;

  try {
    const playwright = loadPlaywright();
    const launched = await launchChromium(playwright, options);
    browser = launched.browser;
    launchConfig = launched.launchConfig;
  } catch (error) {
    const infrastructureSummary = {
      schemaVersion: 1,
      runner: "tools/run_managed_child_visual_qa.mjs",
      startedAt: startedAt.toISOString(),
      finishedAt: new Date().toISOString(),
      manifestPath: options.manifestPath,
      outputDir: options.outputDir,
      inventory: {
        manifestChildServices: allChildren.length,
        selectedChildServices: selectedChildren.length,
        expectedCases: jobs.length,
      },
      pass: false,
      infrastructureError: error.message,
    };
    await writeJsonAtomic(outputPaths.summary, infrastructureSummary);
    throw Object.assign(error, { exitCode: 2 });
  }

  process.stdout.write(
    `Managed child visual QA: ${selectedChildren.length} pages x ${VIEWPORTS.length} viewports = ${jobs.length} cases\n`,
  );
  process.stdout.write(`Artifacts: ${options.outputDir}\n`);

  let results;
  try {
    results = await runWorkerPool(jobs, options.concurrency, async (job, index) => {
      const prefix = `[${String(index + 1).padStart(String(jobs.length).length, " ")}/${jobs.length}]`;
      const result = await runCase(browser, job, options, outputPaths);
      const state = result.pass ? "PASS" : "RED";
      const codes = result.failures.map((failure) => failure.code).join(", ");
      process.stdout.write(
        `${prefix} ${state} ${job.page.page_key} ${job.viewport.name}${codes ? ` [${codes}]` : ""}\n`,
      );
      return result;
    });
  } finally {
    await browser.close().catch(() => {});
  }

  const summary = summarizeResults(results, {
    startedAt,
    releaseId: manifest.release_id || null,
    manifestPath: options.manifestPath,
    baseUrl: options.baseUrl,
    browser: launchConfig,
    inventoryCount: allChildren.length,
    selectedCount: selectedChildren.length,
  });
  await writeJsonAtomic(outputPaths.summary, summary);
  process.stdout.write(
    `Summary: ${summary.passedCases} PASS, ${summary.failedCases} RED, ${summary.screenshotsCreated}/${summary.screenshotsExpected} screenshots\n`,
  );
  process.stdout.write(`JSON: ${outputPaths.summary}\n`);
  return summary.pass ? 0 : 1;
}

async function main() {
  let options;
  try {
    options = parseArgs(process.argv.slice(2));
  } catch (error) {
    process.stderr.write(`${error.message}\n\n${usage()}\n`);
    return 2;
  }
  if (options.help) {
    process.stdout.write(`${usage()}\n`);
    return 0;
  }
  if (options.selfTest) {
    await runSelfTest();
    return 0;
  }
  return run(options);
}

if (process.argv[1] && path.resolve(process.argv[1]) === SCRIPT_PATH) {
  try {
    process.exitCode = await main();
  } catch (error) {
    process.stderr.write(`FATAL: ${error.stack || error.message}\n`);
    process.exitCode = error.exitCode || 2;
  }
}
