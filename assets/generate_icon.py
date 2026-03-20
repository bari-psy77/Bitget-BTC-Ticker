"""Generate app icon (ICO) matching the tray icon design."""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def create_icon(size: int = 256) -> Image.Image:
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    font_size = int(size * 0.85)
    font = None
    for face in (
        "DejaVuSans-Bold.ttf",
        "LiberationSans-Bold.ttf",
        "DejaVuSans.ttf",
        "arial.ttf",
    ):
        try:
            candidate = ImageFont.truetype(face, font_size)
            bbox = draw.textbbox((0, 0), "B", font=candidate)
            if bbox[2] - bbox[0] > size * 0.1:
                font = candidate
                break
        except Exception:
            continue

    if font is None:
        font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), "B", font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    x = (size - text_w) // 2 - bbox[0]
    y = (size - text_h) // 2 - bbox[1]
    draw.text((x, y), "B", fill=(247, 147, 26, 255), font=font)

    return image


def main() -> None:
    output_path = Path(__file__).parent / "icon.ico"
    sizes = [16, 24, 32, 48, 64, 128, 256]
    images = [create_icon(s) for s in sizes]
    images[-1].save(
        str(output_path),
        format="ICO",
        sizes=[(s, s) for s in sizes],
        append_images=images[:-1],
    )
    print(f"Icon saved to {output_path}")


if __name__ == "__main__":
    main()
