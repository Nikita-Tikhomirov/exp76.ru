import fs from "node:fs/promises";
import path from "node:path";

import { FileBlob, SpreadsheetFile, Workbook } from "@oai/artifact-tool";


const SHEET_NAMES = [
  "scope_urls",
  "keywords_raw",
  "keywords_clean",
  "minus_words",
  "frozen_collisions",
  "serp_results",
  "clusters",
  "url_map",
  "content_briefs",
  "launch_monitoring",
  "qa_log",
];

const HEADER_FILL = "#14532D";
const HEADER_FONT = "#FFFFFF";
const FROZEN_FILL = "#FFC7CE";
const MANUAL_FILL = "#FFEB9C";
const ACCEPTED_FILL = "#C6EFCE";

const INTEGER_HEADERS = new Set([
  "current_status",
  "webmaster_impressions",
  "webmaster_clicks",
  "broad_frequency",
  "phrase_frequency",
  "exact_frequency",
  "impressions",
  "clicks",
  "rank",
  "candidate_count",
  "baseline_impressions",
  "baseline_28d_impressions",
  "baseline_clicks",
  "leads",
  "calls",
]);
const DECIMAL_HEADERS = new Set([
  "avg_position",
  "baseline_position",
  "serp_cohesion",
]);
const PERCENT_HEADERS = new Set(["ctr", "baseline_ctr"]);
const BOOLEAN_HEADERS = new Set(["frozen", "frozen_collision"]);
const DATE_HEADERS = new Set([
  "collected_at",
  "checked_at",
  "launch_date",
  "start_date",
  "check_14d",
  "check_30d",
  "check_60d",
]);

function argumentValue(name) {
  const index = process.argv.indexOf(name);
  if (index < 0 || index + 1 >= process.argv.length) {
    throw new Error(`missing argument ${name}`);
  }
  return process.argv[index + 1];
}

function columnName(index) {
  let value = index + 1;
  let result = "";
  while (value > 0) {
    value -= 1;
    result = String.fromCharCode(65 + (value % 26)) + result;
    value = Math.floor(value / 26);
  }
  return result;
}

function parseBoolean(value) {
  return ["1", "true", "yes", "да"].includes(String(value).trim().toLowerCase());
}

function typedValue(header, value) {
  if (value === null || value === undefined || String(value).trim() === "") {
    return null;
  }
  if (DATE_HEADERS.has(header) && value instanceof Date) {
    return header.endsWith("_at")
      ? new Date(value.getTime() + 3 * 60 * 60 * 1000)
      : value;
  }
  const text = String(value).trim();
  if (BOOLEAN_HEADERS.has(header)) {
    return parseBoolean(text);
  }
  if (PERCENT_HEADERS.has(header)) {
    const parsed = Number(text.replace(",", "."));
    return Number.isFinite(parsed) ? parsed / 100 : text;
  }
  if (INTEGER_HEADERS.has(header) || DECIMAL_HEADERS.has(header)) {
    const parsed = Number(text.replace(",", "."));
    return Number.isFinite(parsed) ? parsed : text;
  }
  if (DATE_HEADERS.has(header)) {
    const parts = text.match(
      /^(\d{4})-(\d{2})-(\d{2})(?:[T ](\d{2}):(\d{2})(?::(\d{2}))?)?/,
    );
    const parsed = parts
      ? new Date(
          Date.UTC(
            Number(parts[1]),
            Number(parts[2]) - 1,
            Number(parts[3]),
            Number(parts[4] ?? 0),
            Number(parts[5] ?? 0),
            Number(parts[6] ?? 0),
          ),
        )
      : new Date(text);
    return Number.isNaN(parsed.getTime()) ? text : parsed;
  }
  return text.startsWith("=") ? `'${text}` : text;
}

function isUrlHeader(header) {
  return header === "url" || header.endsWith("_url") || header.endsWith("_links");
}

function tableName(index, sheetName) {
  const suffix = sheetName
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join("");
  return `T${String(index + 1).padStart(2, "0")}${suffix}`;
}

function applyConditionalFormatting(sheet, headers, rowCount, columnCount) {
  if (rowCount < 2) {
    return;
  }
  const dataRange = sheet.getRange(`A2:${columnName(columnCount - 1)}${rowCount}`);
  const headerIndex = (name) => headers.indexOf(name);
  const acceptedColumns = [headerIndex("validation_status"), headerIndex("review_status")]
    .filter((index) => index >= 0)
    .map((index) => `$${columnName(index)}2`);

  if (sheet.name === "clusters" && acceptedColumns.length > 0) {
    const tests = acceptedColumns.flatMap((cell) => [
      `${cell}="accepted"`,
      `${cell}="verified"`,
      `${cell}="reviewed"`,
    ]);
    dataRange.conditionalFormats.addCustom(`=OR(${tests.join(",")})`, { fill: ACCEPTED_FILL });
  }

  const reviewColumns = [headerIndex("review_status"), headerIndex("validation_status"), headerIndex("status")]
    .filter((index, position, values) => index >= 0 && values.indexOf(index) === position)
    .map((index) => `$${columnName(index)}2`);
  if (reviewColumns.length > 0) {
    const tests = reviewColumns.flatMap((cell) => [
      `${cell}="manual_review"`,
      `${cell}="pending"`,
      `${cell}="pending_serp"`,
      `${cell}="needs_review"`,
    ]);
    dataRange.conditionalFormats.addCustom(`=OR(${tests.join(",")})`, { fill: MANUAL_FILL });
  }

  const frozenIndex = headerIndex("frozen_collision");
  if (frozenIndex >= 0) {
    dataRange.conditionalFormats.addCustom(`=$${columnName(frozenIndex)}2=TRUE`, {
      fill: FROZEN_FILL,
      font: { color: "#9C0006" },
    });
  }
}

async function formatSheet(sheet, sheetIndex, originalRows) {
  const usedRange = sheet.getUsedRange();
  const imported = usedRange.values;
  if (!imported || imported.length === 0 || imported[0].length === 0) {
    throw new Error(`CSV for ${sheet.name} has no header row`);
  }
  const headers = imported[0].map((value) => String(value ?? "").trim());
  const rowCount = imported.length;
  const columnCount = headers.length;
  const values = imported.map((row, rowIndex) =>
    row.map((value, columnIndex) =>
      rowIndex === 0 ? headers[columnIndex] : typedValue(headers[columnIndex], value),
    ),
  );
  usedRange.values = values;

  const lastColumn = columnName(columnCount - 1);
  const headerRange = sheet.getRange(`A1:${lastColumn}1`);
  headerRange.format = {
    fill: HEADER_FILL,
    font: { bold: true, color: HEADER_FONT },
    horizontalAlignment: "center",
    verticalAlignment: "center",
    wrapText: true,
    borders: { preset: "outside", style: "thin", color: "#0B3D24" },
  };
  headerRange.format.rowHeight = 30;
  if (rowCount > 1) {
    const dataRange = sheet.getRange(`A2:${lastColumn}${rowCount}`);
    dataRange.format = {
      verticalAlignment: "top",
      wrapText: true,
      borders: {
        insideHorizontal: { style: "thin", color: "#DDE7DF" },
      },
    };
    const rowHeights = {
      scope_urls: 36,
      clusters: 42,
      url_map: 36,
      content_briefs: 48,
      qa_log: 36,
    };
    dataRange.format.rowHeight = rowHeights[sheet.name] ?? 22;
  }

  for (let columnIndex = 0; columnIndex < columnCount; columnIndex += 1) {
    const header = headers[columnIndex];
    const letter = columnName(columnIndex);
    const sourceWidth = Math.max(
      header.length,
      ...originalRows.slice(1).map((row) => String(row[columnIndex] ?? "").length),
    );
    const width = Math.min(60, Math.max(10, sourceWidth + 2));
    sheet.getRange(`${letter}1:${letter}${rowCount}`).format.columnWidth = width;
    if (rowCount > 1 && PERCENT_HEADERS.has(header)) {
      sheet.getRange(`${letter}2:${letter}${rowCount}`).format.numberFormat = "0.0%";
    } else if (rowCount > 1 && INTEGER_HEADERS.has(header)) {
      sheet.getRange(`${letter}2:${letter}${rowCount}`).format.numberFormat = "#,##0";
    } else if (rowCount > 1 && DECIMAL_HEADERS.has(header)) {
      sheet.getRange(`${letter}2:${letter}${rowCount}`).format.numberFormat = "0.0";
    } else if (rowCount > 1 && DATE_HEADERS.has(header)) {
      const format = header.endsWith("_at") ? "yyyy-mm-dd hh:mm" : "yyyy-mm-dd";
      sheet.getRange(`${letter}2:${letter}${rowCount}`).format.numberFormat = format;
    }
    if (rowCount > 1 && isUrlHeader(header)) {
      sheet.getRange(`${letter}2:${letter}${rowCount}`).format.font = { color: "#0563C1" };
    }
  }

  sheet.showGridLines = false;
  const table = sheet.tables.add(`A1:${lastColumn}${rowCount}`, true, tableName(sheetIndex, sheet.name));
  table.style = "TableStyleMedium4";
  table.showFilterButton = true;
  applyConditionalFormatting(sheet, headers, rowCount, columnCount);
  await sheet.freezePanes.freezeRows(1);
}

async function buildWorkbook(dataDir, outputPath) {
  const workbook = Workbook.create();
  for (let index = 0; index < SHEET_NAMES.length; index += 1) {
    const sheetName = SHEET_NAMES[index];
    const csvText = await fs.readFile(path.join(dataDir, `${sheetName}.csv`), "utf8");
    const parsed = await Workbook.fromCSV(csvText, { sheetName });
    const originalRows = parsed.worksheets.getItem(sheetName).getUsedRange().values;
    const sheet = workbook.worksheets.add(sheetName);
    sheet.getRangeByIndexes(0, 0, originalRows.length, originalRows[0].length).values = originalRows;
    await formatSheet(sheet, index, originalRows);
  }
  await fs.mkdir(path.dirname(outputPath), { recursive: true });
  const output = await SpreadsheetFile.exportXlsx(workbook);
  await output.save(outputPath);
}

function rowsFromSheet(sheet) {
  const range = sheet.getUsedRange();
  if (!range) {
    return [];
  }
  const values = range.values ?? [];
  const formulas = range.formulas ?? [];
  if (values.length === 0) {
    return [];
  }
  const headers = values[0].map((value) => String(value ?? "").trim());
  return values.slice(1).map((row, rowIndex) => {
    const record = {};
    for (let columnIndex = 0; columnIndex < headers.length; columnIndex += 1) {
      const header = headers[columnIndex];
      const formula = formulas[rowIndex + 1]?.[columnIndex] ?? "";
      let value = row[columnIndex];
      const match = String(formula).match(/^=?HYPERLINK\("((?:""|[^"])*)"/i);
      if (match) {
        value = match[1].replaceAll('""', '"');
      }
      record[header] = value ?? "";
    }
    return record;
  });
}

function splitQueryIds(value) {
  return String(value ?? "")
    .split("|")
    .map((item) => item.trim())
    .filter(Boolean);
}

function canonicalCell(value) {
  if (value === null || value === undefined || value === "") {
    return null;
  }
  if (value instanceof Date) {
    const excelSerial = (value.getTime() - Date.UTC(1899, 11, 30)) / (24 * 60 * 60 * 1000);
    return `number:${Number(excelSerial.toPrecision(14))}`;
  }
  if (typeof value === "number") {
    return `number:${Number(value.toPrecision(14))}`;
  }
  if (typeof value === "boolean") {
    return `boolean:${value}`;
  }
  return `text:${String(value)}`;
}

async function sourceWorkbookErrors(workbook, dataDir) {
  if (!dataDir) {
    return [];
  }
  const errors = [];
  const actualSheetNames = new Set(workbook.worksheets.items.map((sheet) => sheet.name));
  for (const sheetName of SHEET_NAMES) {
    if (!actualSheetNames.has(sheetName)) {
      continue;
    }
    const csvText = await fs.readFile(path.join(dataDir, `${sheetName}.csv`), "utf8");
    const parsed = await Workbook.fromCSV(csvText, { sheetName });
    const sourceRows = parsed.worksheets.getItem(sheetName).getUsedRange().values ?? [];
    const actualRows = workbook.worksheets.getItem(sheetName).getUsedRange().values ?? [];
    const headers = (sourceRows[0] ?? []).map((value) => String(value ?? "").trim());
    const expected = sourceRows.map((row, rowIndex) =>
      row.map((value, columnIndex) =>
        canonicalCell(rowIndex === 0 ? headers[columnIndex] : typedValue(headers[columnIndex], value)),
      ),
    );
    const actual = actualRows.map((row) => row.map((value) => canonicalCell(value)));
    if (expected.length !== actual.length) {
      errors.push(`source_sheet_mismatch:${sheetName}:row_count`);
      continue;
    }
    let mismatch = "";
    for (let rowIndex = 0; rowIndex < expected.length && !mismatch; rowIndex += 1) {
      if (expected[rowIndex].length !== actual[rowIndex].length) {
        mismatch = `row_${rowIndex + 1}_column_count`;
        break;
      }
      for (let columnIndex = 0; columnIndex < expected[rowIndex].length; columnIndex += 1) {
        if (expected[rowIndex][columnIndex] !== actual[rowIndex][columnIndex]) {
          mismatch = `cell_${columnName(columnIndex)}${rowIndex + 1}`;
          break;
        }
      }
    }
    if (mismatch) {
      errors.push(`source_sheet_mismatch:${sheetName}:${mismatch}`);
    }
  }
  return errors;
}

function workbookErrors(workbook) {
  const errors = [];
  const names = workbook.worksheets.items.map((sheet) => sheet.name);
  for (const required of SHEET_NAMES) {
    if (!names.includes(required)) {
      errors.push(`missing_sheet:${required}`);
    }
  }
  for (const actual of names) {
    if (!SHEET_NAMES.includes(actual)) {
      errors.push(`unexpected_sheet:${actual}`);
    }
  }
  if (errors.length > 0) {
    return [...new Set(errors)].sort();
  }

  const clusters = rowsFromSheet(workbook.worksheets.getItem("clusters"));
  const urlMap = rowsFromSheet(workbook.worksheets.getItem("url_map"));
  const keywords = rowsFromSheet(workbook.worksheets.getItem("keywords_clean"));
  const frozen = rowsFromSheet(workbook.worksheets.getItem("frozen_collisions"));

  const ownersByCluster = new Map();
  for (const row of urlMap) {
    const clusterId = String(row.cluster_id ?? "").trim();
    if (!clusterId) {
      continue;
    }
    const target = String(row.target_url ?? "").trim();
    if (!ownersByCluster.has(clusterId)) {
      ownersByCluster.set(clusterId, new Set());
    }
    ownersByCluster.get(clusterId).add(target);
  }
  for (const [clusterId, targets] of ownersByCluster) {
    if (targets.size > 1) {
      errors.push(`duplicate_cluster_owner:${clusterId}`);
    }
  }

  const clusterById = new Map();
  const clusterIdByQuery = new Map();
  for (const cluster of clusters) {
    const clusterId = String(cluster.cluster_id ?? "").trim();
    clusterById.set(clusterId, cluster);
    for (const queryId of splitQueryIds(cluster.query_ids)) {
      clusterIdByQuery.set(queryId, clusterId);
    }
    const intent = String(cluster.intent ?? "").trim();
    const action = String(cluster.url_action ?? "").trim();
    const accepted = [
      "keep_enhance",
      "new_child_candidate",
      "new_url",
      "create",
      "hub",
      "child",
      "merge",
    ].includes(action);
    if (
      ["commercial_research", "transactional"].includes(intent)
      && accepted
      && !String(cluster.target_url ?? "").trim()
    ) {
      errors.push(`blank_target_url:${clusterId}`);
    }
  }
  const hasReviewedBrandOwner = (() => {
    const row = clusterById.get("SPECIAL-BRAND-HOMEPAGE");
    return row && String(row.review_status ?? "").trim() === "reviewed";
  })();

  for (const keyword of keywords) {
    const keywordId = String(keyword.keyword_id ?? "").trim();
    const clicks = Number(keyword.clicks ?? 0);
    const decision = String(keyword.final_decision ?? "").trim();
    const intent = String(keyword.intent ?? "").trim();
    const coveredByBrandOwner = intent === "brand_navigation" && hasReviewedBrandOwner;
    if (
      clicks > 0
      && !["exclude", "frozen_owner"].includes(decision)
      && !clusterIdByQuery.has(keywordId)
      && !coveredByBrandOwner
    ) {
      errors.push(`clicked_query_without_cluster:${keywordId}`);
    }
  }

  const mapByCluster = new Map();
  for (const row of urlMap) {
    const clusterId = String(row.cluster_id ?? "").trim();
    if (!mapByCluster.has(clusterId)) {
      mapByCluster.set(clusterId, row);
    }
  }
  for (const row of frozen) {
    const keywordId = String(row.keyword_id ?? "").trim();
    const isFrozen = row.frozen_collision === true || parseBoolean(row.frozen_collision);
    const clusterId = clusterIdByQuery.get(keywordId);
    if (!isFrozen || !clusterId) {
      continue;
    }
    const mapped = mapByCluster.get(clusterId) ?? {};
    const ownerUrl = String(row.owner_url ?? "").trim();
    const targetUrl = String(mapped.target_url ?? clusterById.get(clusterId)?.target_url ?? "").trim();
    const action = String(mapped.url_action ?? clusterById.get(clusterId)?.url_action ?? "").trim();
    if (
      targetUrl
      && targetUrl !== ownerUrl
      && ["new_child_candidate", "new_url", "create", "child"].includes(action)
    ) {
      errors.push(`frozen_collision_assigned_new_url:${keywordId}`);
    }
  }
  return [...new Set(errors)].sort();
}

async function loadWorkbook(inputPath) {
  const input = await FileBlob.load(inputPath);
  return SpreadsheetFile.importXlsx(input);
}

async function validateWorkbook(inputPath, dataDir = "") {
  const workbook = await loadWorkbook(inputPath);
  return [...new Set([
    ...workbookErrors(workbook),
    ...(await sourceWorkbookErrors(workbook, dataDir)),
  ])].sort();
}

async function renderWorkbook(inputPath, outputDir) {
  const workbook = await loadWorkbook(inputPath);
  await fs.mkdir(outputDir, { recursive: true });
  const rendered = [];
  for (let index = 0; index < SHEET_NAMES.length; index += 1) {
    const sheetName = SHEET_NAMES[index];
    const sheet = workbook.worksheets.getItem(sheetName);
    const usedValues = sheet.getUsedRange().values ?? [];
    const columnCount = usedValues[0]?.length ?? 1;
    const previewRows = Math.max(1, Math.min(20, usedValues.length));
    const previewRange = `A1:${columnName(columnCount - 1)}${previewRows}`;
    const preview = await workbook.render({
      sheetName,
      range: previewRange,
      scale: 1,
      format: "png",
    });
    const outputPath = path.join(outputDir, `${String(index + 1).padStart(2, "0")}-${sheetName}.png`);
    await fs.writeFile(outputPath, new Uint8Array(await preview.arrayBuffer()));
    rendered.push(outputPath);
  }
  return rendered;
}

async function main() {
  const command = process.argv[2];
  if (command === "build") {
    await buildWorkbook(argumentValue("--data-dir"), argumentValue("--output"));
    return;
  }
  if (command === "validate") {
    const dataDirIndex = process.argv.indexOf("--data-dir");
    const dataDir = dataDirIndex >= 0 ? argumentValue("--data-dir") : "";
    const errors = await validateWorkbook(argumentValue("--input"), dataDir);
    console.log(`VALIDATION_JSON:${JSON.stringify(errors)}`);
    return;
  }
  if (command === "render") {
    const rendered = await renderWorkbook(argumentValue("--input"), argumentValue("--output-dir"));
    console.log(`RENDER_JSON:${JSON.stringify(rendered)}`);
    return;
  }
  throw new Error(`unsupported command: ${command ?? ""}`);
}

await main();
