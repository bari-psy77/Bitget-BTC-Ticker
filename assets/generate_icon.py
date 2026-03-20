"""Generate app icon (ICO) matching the tray icon design."""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def create_icon(size: int = 256) -> Image.Image:
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    # Orange circle background
    margin = size // 32
    draw.ellipse(
        [margin, margin, size - margin, size - margin],
        fill=(247, 147, 26, 255),
    )

    # "B" letter
    font_size = int(size * 0.53)
    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except Exception:
        font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), "B", font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    x = (size - text_w) // 2
    y = (size - text_h) // 2 - bbox[1]
    draw.text((x, y), "B", fill=(13, 17, 23, 255), font=font)

    # Vertical lines through B (Bitcoin style)
    line_width = max(2, size // 32)
    left_line_x = size // 2 - size // 16
    right_line_x = size // 2 + size // 16
    top_y = int(size * 0.18)
    bottom_y = int(size * 0.82)
    draw.line((left_line_x, top_y, left_line_x, bottom_y), fill=(13, 17, 23, 255), width=line_width)
    draw.line((right_line_x, top_y, right_line_x, bottom_y), fill=(13, 17, 23, 255), width=line_width)

    return image


def main() -> None:
    output_path = Path(__file__).parent / "icon.ico"
    sizes = [16, 32, 48, 64, 128, 256]
    images = [create_icon(s) for s in sizes]
    images[-1].save(str(output_path), format="ICO", sizes=[(s, s) for s in sizes], append_images=images[:-1])
    print(f"Icon saved to {output_path}")


if __name__ == "__main__":
    main()
