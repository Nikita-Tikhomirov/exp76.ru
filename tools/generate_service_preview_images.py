from __future__ import annotations

import json
import re
import textwrap
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "generated-assets" / "service-previews"
THEME_IMPORT_DIR = ROOT / "ftp_dump_minimal" / "wp-content" / "themes" / "land76wp" / "import"
SEO_IMPORT_DIR = ROOT / "seo-content" / "service-previews" / "import"
CACHE_DIR = OUT_DIR / "_source"
WIDTH = 1200
HEIGHT = 675


SERVICE_IMPORTS = [
    ("drenazh", ROOT / "seo-content" / "drenazh-uchastka" / "import" / "drenazh-import.json"),
    ("otmostka", ROOT / "seo-content" / "otmostka-vokrug-doma" / "import" / "otmostka-import.json"),
    ("plitka", ROOT / "seo-content" / "ukladka-trotuarnoy-plitki" / "import" / "plitka-import.json"),
    ("osushenie", ROOT / "seo-content" / "osushenie-uchastka" / "import" / "osushenie-import.json"),
    ("livnevka", ROOT / "seo-content" / "livnevaya-kanalizatsiya" / "import" / "livnevka-import.json"),
    ("autopoliv", ROOT / "seo-content" / "avtopoliv-na-uchastke" / "import" / "autopoliv-import.json"),
]


CATEGORY_META = {
    "drenazh": {
        "label": "Дренаж участка",
        "accent": (10, 146, 21),
        "image": "https://exp76.ru/wp-content/uploads/2020/10/IMG_20190828_145808_HDR-1024x768.webp",
        "alt_suffix": "дренаж участка под ключ",
    },
    "otmostka": {
        "label": "Отмостка вокруг дома",
        "accent": (10, 146, 21),
        "image": "https://exp76.ru/wp-content/uploads/2018/02/IMG_1173-848x480.webp",
        "alt_suffix": "отмостка вокруг дома под ключ",
    },
    "plitka": {
        "label": "Укладка тротуарной плитки",
        "accent": (10, 146, 21),
        "image": "https://exp76.ru/wp-content/uploads/2018/02/DbDKG2WLtEk-848x430.webp",
        "alt_suffix": "укладка тротуарной плитки",
    },
    "osushenie": {
        "label": "Осушение участка",
        "accent": (10, 146, 21),
        "image": "https://exp76.ru/wp-content/uploads/2018/02/IMG_1814-1024x768.webp",
        "alt_suffix": "осушение участка и отвод воды",
    },
    "livnevka": {
        "label": "Ливневая канализация",
        "accent": (10, 146, 21),
        "image": "https://exp76.ru/wp-content/uploads/2018/02/IMG_1173-848x480.webp",
        "alt_suffix": "ливневая канализация на участке",
    },
    "autopoliv": {
        "label": "Автополив на участке",
        "accent": (10, 146, 21),
        "image": "https://exp76.ru/wp-content/uploads/2019/02/IMG_20180626_124212_HDR-1024x768.webp",
        "alt_suffix": "автополив на участке",
    },
}


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def slugify(value: str) -> str:
    value = value.lower()
    value = re.sub(r"[^a-z0-9а-яё-]+", "-", value, flags=re.IGNORECASE)
    value = value.strip("-")
    return value or "service-preview"


def download_source(category: str, url: str) -> Path:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    suffix = Path(urllib.request.urlparse(url).path).suffix or ".jpg"
    dest = CACHE_DIR / f"{category}{suffix}"
    if dest.exists() and dest.stat().st_size > 0:
        return dest

    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=30) as response:
        dest.write_bytes(response.read())
    return dest


def cover_image(source: Image.Image) -> Image.Image:
    source = source.convert("RGB")
    src_ratio = source.width / source.height
    dst_ratio = WIDTH / HEIGHT
    if src_ratio > dst_ratio:
        new_h = HEIGHT
        new_w = int(new_h * src_ratio)
    else:
        new_w = WIDTH
        new_h = int(new_w / src_ratio)

    resized = source.resize((new_w, new_h), Image.Resampling.LANCZOS)
    left = (new_w - WIDTH) // 2
    top = (new_h - HEIGHT) // 2
    return resized.crop((left, top, left + WIDTH, top + HEIGHT))


def font(path: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(path, size=size)


FONT_REG = r"C:\Windows\Fonts\segoeui.ttf"
FONT_BOLD = r"C:\Windows\Fonts\segoeuib.ttf"


def wrap_by_pixels(draw: ImageDraw.ImageDraw, text: str, font_obj: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        bbox = draw.textbbox((0, 0), candidate, font=font_obj)
        if bbox[2] <= max_width:
            current = candidate
            continue
        if current:
            lines.append(current)
        current = word
    if current:
        lines.append(current)
    return lines


def draw_text_block(draw: ImageDraw.ImageDraw, xy: tuple[int, int], lines: list[str], font_obj, fill, line_gap: int) -> int:
    x, y = xy
    for line in lines:
        draw.text((x, y), line, font=font_obj, fill=fill)
        bbox = draw.textbbox((x, y), line, font=font_obj)
        y = bbox[3] + line_gap
    return y


def make_preview(category: str, title: str, slug: str) -> Path:
    meta = CATEGORY_META[category]
    source_path = download_source(category, meta["image"])
    base = cover_image(Image.open(source_path))
    base = base.filter(ImageFilter.GaussianBlur(radius=1.1))

    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    overlay_draw.rectangle((0, 0, WIDTH, HEIGHT), fill=(0, 0, 0, 82))
    overlay_draw.rectangle((0, 0, 520, HEIGHT), fill=(0, 0, 0, 92))
    base = Image.alpha_composite(base.convert("RGBA"), overlay)

    draw = ImageDraw.Draw(base)
    accent = meta["accent"]
    draw.rounded_rectangle((78, 92, 158, 172), radius=40, outline=accent + (255,), width=5)
    draw.line((118, 112, 118, 152), fill=accent + (255,), width=5)
    draw.line((98, 132, 138, 132), fill=accent + (255,), width=5)

    draw.text((185, 98), "ЭКСПЕРТЫ", font=font(FONT_BOLD, 34), fill=(255, 255, 255, 255))
    draw.text((187, 137), "ландшафтная компания", font=font(FONT_REG, 20), fill=(232, 232, 232, 255))

    draw.rounded_rectangle((80, 240, 1120, 560), radius=10, fill=(255, 255, 255, 228))
    draw.rectangle((80, 240, 92, 560), fill=accent + (255,))

    draw.text((125, 278), meta["label"].upper(), font=font(FONT_BOLD, 25), fill=accent + (255,))
    title_font = font(FONT_BOLD, 56)
    title_lines = wrap_by_pixels(draw, title, title_font, 900)
    if len(title_lines) > 3:
        title_font = font(FONT_BOLD, 48)
        title_lines = wrap_by_pixels(draw, title, title_font, 900)[:4]
    y = draw_text_block(draw, (125, 330), title_lines, title_font, (35, 35, 35, 255), 8)

    subtitle = "Проектирование, материалы и монтаж под ключ"
    draw.text((125, min(y + 14, 512)), subtitle, font=font(FONT_REG, 27), fill=(85, 85, 85, 255))

    draw.rounded_rectangle((930, 595, 1120, 632), radius=18, fill=accent + (245,))
    draw.text((958, 601), "exp76.ru", font=font(FONT_BOLD, 23), fill=(255, 255, 255, 255))

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / f"{slug}.webp"
    base.convert("RGB").save(out_path, "WEBP", quality=86, method=6)
    return out_path


def main() -> None:
    previews = []
    for category, import_path in SERVICE_IMPORTS:
        payload = read_json(import_path)
        meta = CATEGORY_META[category]
        for post in payload.get("posts", []):
            slug = post["slug"]
            title = post["post_title"]
            image_path = make_preview(category, title, slug)
            alt = f"{title} — {meta['alt_suffix']} в Ярославской области"
            previews.append(
                {
                    "slug": slug,
                    "post_title": title,
                    "category": category,
                    "local_file": str(image_path.relative_to(ROOT)).replace("\\", "/"),
                    "upload_subdir": "seo-service-previews",
                    "filename": image_path.name,
                    "url": f"https://exp76.ru/wp-content/uploads/seo-service-previews/{image_path.name}",
                    "alt": alt,
                    "title": title,
                    "caption": "",
                    "description": alt,
                }
            )

    result = {
        "image_size": {"width": WIDTH, "height": HEIGHT},
        "items": previews,
    }

    SEO_IMPORT_DIR.mkdir(parents=True, exist_ok=True)
    THEME_IMPORT_DIR.mkdir(parents=True, exist_ok=True)
    for path in (SEO_IMPORT_DIR / "service-previews-import.json", THEME_IMPORT_DIR / "service-previews-import.json"):
        path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"Generated {len(previews)} previews in {OUT_DIR}")


if __name__ == "__main__":
    main()
