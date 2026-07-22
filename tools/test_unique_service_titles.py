import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_post(import_path: Path, slug: str) -> dict:
    payload = json.loads(import_path.read_text(encoding="utf-8"))
    return next(post for post in payload["posts"] if post["slug"] == slug)


def main() -> None:
    plitka_post = load_post(
        ROOT / "seo-content" / "ukladka-trotuarnoy-plitki" / "import" / "plitka-import.json",
        "otmostka-iz-trotuarnoy-plitki",
    )
    otmostka_post = load_post(
        ROOT / "seo-content" / "otmostka-vokrug-doma" / "import" / "otmostka-import.json",
        "otmostka-iz-plitki",
    )

    assert plitka_post["post_title"] != otmostka_post["post_title"], (
        "Service pages with different search intent must not share a post title: "
        f'{plitka_post["post_title"]!r}'
    )


if __name__ == "__main__":
    main()
