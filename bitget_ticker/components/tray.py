from __future__ import annotations

import threading
from collections.abc import Callable

try:
    import pystray
    from PIL import Image, ImageDraw, ImageFont
except ImportError:  # pragma: no cover - runtime dependency fallback
    pystray = None  # type: ignore[assignment]
    Image = None  # type: ignore[assignment]
    ImageDraw = None  # type: ignore[assignment]
    ImageFont = None  # type: ignore[assignment]


class TrayIcon:
    """System tray integration for settings and quit actions."""

    SETTINGS_MENU_LABEL = "Settings"
    QUIT_MENU_LABEL = "Quit"

    def __init__(
        self,
        root,
        on_open_settings: Callable[[], None],
        on_quit: Callable[[], None],
    ) -> None:
        self.root = root
        self.on_open_settings = on_open_settings
        self.on_quit = on_quit
        self.icon = None
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if pystray is None or Image is None or ImageDraw is None:
            return

        if self._thread is not None and self._thread.is_alive():
            return

        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        if self.icon is not None:
            try:
                self.icon.stop()
            except Exception:
                pass

    def _run(self) -> None:
        if pystray is None:
            return

        menu = pystray.Menu(
            pystray.MenuItem(
                self.SETTINGS_MENU_LABEL,
                lambda icon, item: self.root.after(0, self.on_open_settings),
            ),
            pystray.MenuItem(
                self.QUIT_MENU_LABEL,
                lambda icon, item: self.root.after(0, self.on_quit),
            ),
        )
        self.icon = pystray.Icon(
            "bitget_btc_ticker",
            self._create_image(),
            "Bitget BTC Ticker",
            menu,
        )
        self.icon.run()

    def _create_image(self):
        if Image is None or ImageDraw is None:
            return None

        image = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        draw.ellipse([2, 2, 62, 62], fill=(247, 147, 26, 255))

        try:
            font = ImageFont.truetype("arial.ttf", 34) if ImageFont else None
        except Exception:
            font = ImageFont.load_default() if ImageFont else None

        draw.text((21, 13), "B", fill=(13, 17, 23, 255), font=font)
        draw.line((28, 12, 28, 52), fill=(13, 17, 23, 255), width=2)
        draw.line((36, 12, 36, 52), fill=(13, 17, 23, 255), width=2)
        return image
