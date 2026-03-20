"""Generate app icon (ICO) matching the tray icon design."""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def create_icon(size: int = 256) -> Image.Image:
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    # Orange circle — with margin so it doesn't bleed to edges
    margin = int(size * 0.06)
    draw.ellipse(
        [margin, margin, size - margin, size - margin],
        fill=(247, 147, 26, 255),
    )

    # Use a bold font for clean "B" rendering; prefer Bold variants
    font_size = int(size * 0.48)
    font = None
    for face in (
        "DejaVuSans-Bold.ttf",
        "DejaVuSans.ttf",
        "LiberationSans-Bold.ttf",
        "arial.ttf",
        "segoeui.ttf",
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

    symbol = "B"

    # Center the symbol
    bbox = draw.textbbox((0, 0), symbol, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    x = (size - text_w) // 2 - bbox[0]
    y = (size - text_h) // 2 - bbox[1]
    draw.text((x, y), symbol, fill=(13, 17, 23, 255), font=font)

    # Classic Bitcoin vertical serifs (two short horizontal bars top & bottom)
    lw = max(2, size // 32)
    cx = size // 2
    serif_half = int(size * 0.12)
    top_y = int(size * 0.20)
    bot_y = int(size * 0.80)
    draw.line((cx - serif_half, top_y, cx + serif_half, top_y), fill=(13, 17, 23, 255), width=lw)
    draw.line((cx - serif_half, bot_y, cx + serif_half, bot_y), fill=(13, 17, 23, 255), width=lw)

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
