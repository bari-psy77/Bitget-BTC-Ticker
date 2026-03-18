from __future__ import annotations

import unittest
from unittest.mock import patch

from bitget_ticker.ticker import BitgetBTCTicker


class _OverlayStub:
    def __init__(self) -> None:
        self.notifications: list[tuple[float, float]] = []

    def show_notification(self, alarm_price: float, current_price: float) -> None:
        self.notifications.append((alarm_price, current_price))


class BitgetTickerAlertModeTests(unittest.TestCase):
    def test_on_alarm_uses_overlay_notification_in_notification_mode(self) -> None:
        app = BitgetBTCTicker.__new__(BitgetBTCTicker)
        app.config = {"alert_mode": "notification"}
        app.overlay = _OverlayStub()
        app.root = object()

        with patch("bitget_ticker.ticker.messagebox.showinfo") as showinfo:
            app.on_alarm(95000.0, 96000.0)

        self.assertEqual(app.overlay.notifications, [(95000.0, 96000.0)])
        showinfo.assert_not_called()


if __name__ == "__main__":
    unittest.main()
