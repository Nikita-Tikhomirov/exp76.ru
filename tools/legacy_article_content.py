"""Validate production article JSON for the audited S9-S15 architecture."""

from __future__ import annotations

import argparse
import copy
import html
import json
import re
from pathlib import Path
from typing import Any, Iterable, Sequence

from tools.seo_semantics.legacy_article_architecture import build_legacy_article_rows


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ARTICLE_DIR = REPOSITORY_ROOT / "seo-content" / "legacy-articles" / "articles"
DEFAULT_IMPORT_PATH = (
    REPOSITORY_ROOT
    / "seo-content"
    / "legacy-articles"
    / "import"
    / "legacy-services-blog-import.json"
)

TOP_LEVEL_FIELDS = (
    "schema_version",
    "destination_id",
    "service_id",
    "slug",
    "canonical",
    "post_title",
    "post_excerpt",
    "post_content",
    "featured_image_url",
    "acf",
    "internal_links",
    "sources",
)

ACF_FIELDS = (
    "blogseo_hero_title",
    "blogseo_hero_subtitle",
    "blogseo_lead",
    "blogseo_main_image_url",
    "blogseo_main_image_alt",
    "blogseo_sections",
    "blogseo_cta_title",
    "blogseo_cta_text",
    "blogseo_cta_button_text",
    "blogseo_cta_button_url",
    "blogseo_faq_items",
    "blogseo_related_service_slugs",
    "blogseo_seo_title",
    "blogseo_seo_description",
)

WORD_PATTERN = re.compile(r"[A-Za-zА-Яа-яЁё0-9]+(?:[-–—][A-Za-zА-Яа-яЁё0-9]+)*")
TAG_PATTERN = re.compile(r"<[^>]+>")


class ArticleValidationError(ValueError):
    """Raised when an article cannot safely enter the import package."""


def _require_non_empty_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ArticleValidationError(f"{label} must be a non-empty string")
    return value.strip()


def _plain_text(value: str) -> str:
    return html.unescape(TAG_PATTERN.sub(" ", value))


def article_word_count(article: dict[str, Any]) -> int:
    """Count meaningful article words across visible production fields."""

    acf = article["acf"]
    chunks = [acf["blogseo_lead"]]
    for section in acf["blogseo_sections"]:
        chunks.extend((section["heading"], section["body"]))
        for point in section["points"]:
            chunks.extend((point["title"], point["text"]))
    for item in acf["blogseo_faq_items"]:
        chunks.extend((item["question"], item["answer"]))
    return len(WORD_PATTERN.findall(_plain_text(" ".join(chunks))))


def _validate_sections(sections: Any, destination_id: str) -> None:
    if not isinstance(sections, list) or len(sections) < 6:
        raise ArticleValidationError(f"{destination_id}: at least 6 article sections required")
    headings: set[str] = set()
    for index, section in enumerate(sections, start=1):
        if not isinstance(section, dict):
            raise ArticleValidationError(f"{destination_id}: section {index} must be an object")
        heading = _require_non_empty_string(section.get("heading"), f"{destination_id}: section {index} heading")
        if heading.casefold() in headings:
            raise ArticleValidationError(f"{destination_id}: duplicate section heading {heading!r}")
        headings.add(heading.casefold())
        body = _require_non_empty_string(section.get("body"), f"{destination_id}: section {index} body")
        if len(_plain_text(body)) < 220:
            raise ArticleValidationError(f"{destination_id}: section {index} body is too short")
        points = section.get("points")
        if not isinstance(points, list):
            raise ArticleValidationError(f"{destination_id}: section {index} points must be a list")
        for point_index, point in enumerate(points, start=1):
            if not isinstance(point, dict):
                raise ArticleValidationError(
                    f"{destination_id}: section {index} point {point_index} must be an object"
                )
            _require_non_empty_string(
                point.get("title"), f"{destination_id}: section {index} point {point_index} title"
            )
            _require_non_empty_string(
                point.get("text"), f"{destination_id}: section {index} point {point_index} text"
            )


def _validate_faq(items: Any, destination_id: str) -> None:
    if not isinstance(items, list) or len(items) < 5:
        raise ArticleValidationError(f"{destination_id}: at least 5 FAQ items required")
    questions: set[str] = set()
    for index, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            raise ArticleValidationError(f"{destination_id}: FAQ item {index} must be an object")
        question = _require_non_empty_string(item.get("question"), f"{destination_id}: FAQ {index} question")
        _require_non_empty_string(item.get("answer"), f"{destination_id}: FAQ {index} answer")
        if question.casefold() in questions:
            raise ArticleValidationError(f"{destination_id}: duplicate FAQ question {question!r}")
        questions.add(question.casefold())


def _validate_links(article: dict[str, Any]) -> None:
    destination_id = article["destination_id"]
    service_id = article["service_id"]
    links = article["internal_links"]
    if not isinstance(links, list) or len(links) < 2:
        raise ArticleValidationError(f"{destination_id}: at least two internal links required")
    keys: set[str] = set()
    section_html = " ".join(section["body"] for section in article["acf"]["blogseo_sections"])
    for index, link in enumerate(links, start=1):
        if not isinstance(link, dict):
            raise ArticleValidationError(f"{destination_id}: internal link {index} must be an object")
        page_key = _require_non_empty_string(link.get("page_key"), f"{destination_id}: link {index} page_key")
        url = _require_non_empty_string(link.get("url"), f"{destination_id}: link {index} url")
        _require_non_empty_string(link.get("anchor"), f"{destination_id}: link {index} anchor")
        if not url.startswith("https://exp76.ru/"):
            raise ArticleValidationError(f"{destination_id}: internal link must use exp76.ru")
        if url not in section_html:
            raise ArticleValidationError(f"{destination_id}: internal link {url} is not rendered in a section body")
        keys.add(page_key)
    if f"{service_id}-HUB" not in keys:
        raise ArticleValidationError(f"{destination_id}: parent hub link missing")
    if not any(page_key.startswith(f"{service_id}-CHILD-") for page_key in keys):
        raise ArticleValidationError(f"{destination_id}: child service link missing")


def _validate_sources(article: dict[str, Any]) -> None:
    destination_id = article["destination_id"]
    sources = article["sources"]
    if not isinstance(sources, list):
        raise ArticleValidationError(f"{destination_id}: sources must be a list")
    if article["service_id"] == "S15" and len(sources) < 2:
        raise ArticleValidationError(f"{destination_id}: legal demolition article needs at least two sources")
    for index, source in enumerate(sources, start=1):
        if not isinstance(source, dict):
            raise ArticleValidationError(f"{destination_id}: source {index} must be an object")
        _require_non_empty_string(source.get("title"), f"{destination_id}: source {index} title")
        url = _require_non_empty_string(source.get("url"), f"{destination_id}: source {index} url")
        if not url.startswith("https://"):
            raise ArticleValidationError(f"{destination_id}: source {index} must use HTTPS")
        checked_date = _require_non_empty_string(
            source.get("checked_date"), f"{destination_id}: source {index} checked_date"
        )
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", checked_date):
            raise ArticleValidationError(f"{destination_id}: source {index} date must be YYYY-MM-DD")


def validate_article(article: dict[str, Any], *, expected: dict[str, str] | None = None) -> None:
    """Validate one article against content and architecture requirements."""

    for field in TOP_LEVEL_FIELDS:
        if field not in article:
            raise ArticleValidationError(f"missing top-level field {field}")
    if article["schema_version"] != 1:
        raise ArticleValidationError("schema_version must be 1")

    destination_id = _require_non_empty_string(article["destination_id"], "destination_id")
    service_id = _require_non_empty_string(article["service_id"], f"{destination_id}: service_id")
    if not re.fullmatch(r"S(?:9|1[0-5])-ARTICLE-[A-Z0-9-]+", destination_id):
        raise ArticleValidationError(f"{destination_id}: invalid destination_id")
    if not re.fullmatch(r"S(?:9|1[0-5])", service_id):
        raise ArticleValidationError(f"{destination_id}: invalid service_id")
    if not destination_id.startswith(f"{service_id}-ARTICLE-"):
        raise ArticleValidationError(f"{destination_id}: service_id does not own destination")

    slug = _require_non_empty_string(article["slug"], f"{destination_id}: slug")
    canonical = _require_non_empty_string(article["canonical"], f"{destination_id}: canonical")
    if canonical != f"https://exp76.ru/{slug}/":
        raise ArticleValidationError(f"{destination_id}: canonical does not match slug")
    for field in ("post_title", "post_excerpt", "post_content", "featured_image_url"):
        _require_non_empty_string(article[field], f"{destination_id}: {field}")
    if len(article["post_excerpt"]) < 90:
        raise ArticleValidationError(f"{destination_id}: post_excerpt is too short")
    if not article["featured_image_url"].startswith("https://exp76.ru/wp-content/uploads/"):
        raise ArticleValidationError(f"{destination_id}: featured image must reuse audited site media")

    if expected is not None:
        if service_id != expected["service_id"]:
            raise ArticleValidationError(f"{destination_id}: service differs from architecture")
        if slug != expected["canonical_url"].rstrip("/").rsplit("/", 1)[-1]:
            raise ArticleValidationError(f"{destination_id}: slug differs from architecture")
        if canonical != expected["canonical_url"]:
            raise ArticleValidationError(f"{destination_id}: canonical differs from architecture")
        if article["post_title"] != expected["title"]:
            raise ArticleValidationError(f"{destination_id}: title differs from architecture")

    acf = article["acf"]
    if not isinstance(acf, dict):
        raise ArticleValidationError(f"{destination_id}: acf must be an object")
    for field in ACF_FIELDS:
        if field not in acf:
            raise ArticleValidationError(f"{destination_id}: missing ACF field {field}")
    for field in ACF_FIELDS:
        if field not in {"blogseo_sections", "blogseo_faq_items", "blogseo_related_service_slugs"}:
            _require_non_empty_string(acf[field], f"{destination_id}: {field}")
    if acf["blogseo_main_image_url"] != article["featured_image_url"]:
        raise ArticleValidationError(f"{destination_id}: ACF and featured images differ")

    seo_title = acf["blogseo_seo_title"].strip()
    seo_description = acf["blogseo_seo_description"].strip()
    if not 35 <= len(seo_title) <= 65:
        raise ArticleValidationError(f"{destination_id}: SEO title must contain 35-65 characters")
    if not 90 <= len(seo_description) <= 180:
        raise ArticleValidationError(f"{destination_id}: SEO description must contain 90-180 characters")

    _validate_sections(acf["blogseo_sections"], destination_id)
    _validate_faq(acf["blogseo_faq_items"], destination_id)
    related = acf["blogseo_related_service_slugs"]
    if not isinstance(related, list) or len(related) < 2 or not all(isinstance(item, str) and item for item in related):
        raise ArticleValidationError(f"{destination_id}: at least two related service slugs required")
    _validate_links(article)
    _validate_sources(article)
    if article_word_count(article) < 800:
        raise ArticleValidationError(f"{destination_id}: production article must contain at least 800 words")


def load_and_validate_articles(
    article_dir: Path = DEFAULT_ARTICLE_DIR,
    *,
    require_complete: bool = False,
) -> list[dict[str, Any]]:
    """Load deterministic article files and validate architecture coverage."""

    architecture = {row["destination_id"]: row for row in build_legacy_article_rows()}
    articles: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    seen_urls: set[str] = set()
    for path in sorted(article_dir.glob("*.json")):
        article = json.loads(path.read_text(encoding="utf-8"))
        destination_id = article.get("destination_id")
        if destination_id not in architecture:
            raise ArticleValidationError(f"{path.name}: destination is absent from article architecture")
        if path.name != f"{destination_id}.json":
            raise ArticleValidationError(f"{path.name}: filename must equal destination_id")
        validate_article(article, expected=architecture[destination_id])
        if destination_id in seen_ids:
            raise ArticleValidationError(f"duplicate destination {destination_id}")
        if article["canonical"] in seen_urls:
            raise ArticleValidationError(f"duplicate canonical {article['canonical']}")
        seen_ids.add(destination_id)
        seen_urls.add(article["canonical"])
        articles.append(article)

    if require_complete:
        missing = sorted(set(architecture) - seen_ids)
        extra = sorted(seen_ids - set(architecture))
        if missing or extra:
            raise ArticleValidationError(f"article package differs: missing={missing}, extra={extra}")
    return articles


def build_blog_import_payload(articles: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """Render the exact post shape accepted by import-drenazh-blog.php.

    Category 72 is the existing generic blog category. Direction-specific
    drainage category 87 is deliberately omitted because these articles belong
    to seven different service hubs.
    """

    architecture_rows = build_legacy_article_rows()
    architecture = {row["destination_id"]: row for row in architecture_rows}
    articles_by_id: dict[str, dict[str, Any]] = {}
    for article in articles:
        destination_id = article.get("destination_id")
        if destination_id not in architecture:
            raise ArticleValidationError(f"unknown article destination {destination_id!r}")
        if destination_id in articles_by_id:
            raise ArticleValidationError(f"duplicate article destination {destination_id}")
        validate_article(article, expected=architecture[destination_id])
        articles_by_id[destination_id] = article

    posts: list[dict[str, Any]] = []
    for row in architecture_rows:
        article = articles_by_id.get(row["destination_id"])
        if article is None:
            continue
        posts.append(
            {
                "slug": article["slug"],
                "post_title": article["post_title"],
                "post_excerpt": article["post_excerpt"],
                "post_content": article["post_content"],
                "menu_order": len(posts),
                "categories": [72],
                "featured_image_url": article["featured_image_url"],
                "acf": copy.deepcopy(article["acf"]),
            }
        )

    return {
        "type": "legacy_services_blog_posts",
        "category_ids": [72],
        "posts": posts,
    }


def write_blog_import_payload(path: Path, articles: Iterable[dict[str, Any]]) -> int:
    """Write a deterministic UTF-8 payload without invoking WordPress."""

    payload = build_blog_import_payload(articles)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return len(payload["posts"])


def render_summary(articles: Iterable[dict[str, Any]]) -> str:
    rows = [f"{article['destination_id']}: {article_word_count(article)} words" for article in articles]
    return "\n".join(rows)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate production S9-S15 article JSON.")
    parser.add_argument("--article-dir", type=Path, default=DEFAULT_ARTICLE_DIR)
    parser.add_argument("--complete", action="store_true", help="Require all 11 reviewed destinations")
    parser.add_argument(
        "--render-import",
        nargs="?",
        type=Path,
        const=DEFAULT_IMPORT_PATH,
        default=None,
        metavar="PATH",
        help="Write a local import-drenazh-blog.php compatible JSON payload",
    )
    args = parser.parse_args(argv)
    articles = load_and_validate_articles(args.article_dir, require_complete=args.complete)
    print(render_summary(articles))
    print(f"Validated {len(articles)} production articles.")
    if args.render_import is not None:
        count = write_blog_import_payload(args.render_import, articles)
        print(f"Rendered {count} posts to {args.render_import}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
