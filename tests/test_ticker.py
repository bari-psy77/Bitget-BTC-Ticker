from __future__ import annotations

import unittest
from unittest.mock import patch

from bitget_ticker.ticker import BitgetBTCTicker


class _OverlayStub:
    def __init__(self) -> None:
        self.notifications: list[tuple[float, float]] = []
        self.display_updates: list[tuple[float, float | None]] = []
        self.chart_updates: list[tuple[list[tuple[int, float, float, float, float]], str, str]] = []

    def show_notification(self, alarm_price: float, current_price: float) -> None:
        self.notifications.append((alarm_price, current_price))

    def update_display(self, price: float, previous_price: float | None) -> None:
        self.display_updates.append((price, previous_price))

    def update_chart_data(
        self,
        candles: list[tuple[int, float, float, float, float]],
        timeframe: str,
        market_type: str,
    ) -> None:
        self.chart_updates.append((candles, timeframe, market_type))


class BitgetTickerAlertModeTests(unittest.TestCase):
    def test_on_alarm_uses_overlay_notification_for_notification_alarm(self) -> None:
        app = BitgetBTCTicker.__new__(BitgetBTCTicker)
        app.overlay = _OverlayStub()
        app.root = object()

        with patch("bitget_ticker.ticker.messagebox.showinfo") as showinfo:
            app.on_alarm(95000.0, 96000.0, "notification")

        self.assertEqual(app.overlay.notifications, [(95000.0, 96000.0)])
        showinfo.assert_not_called()

    def test_apply_market_snapshot_updates_price_and_chart_cache(self) -> None:
        app = BitgetBTCTicker.__new__(BitgetBTCTicker)
        app.overlay = _OverlayStub()
        app.previous_price = 90000.0
        app.chart_points = []
        app.config = {
            "market_type": "futures",
            "chart_timeframe": "15m",
        }

        app._apply_market_snapshot(
            91000.0,
            [
                (1710000000000, 90000.0, 90500.0, 89500.0, 90300.0),
                (1710000900000, 90300.0, 91000.0, 90200.0, 90850.0),
            ],
        )

        self.assertEqual(app.overlay.display_updates, [(91000.0, 90000.0)])
        self.assertEqual(
            app.overlay.chart_updates,
            [
                (
                    [
                        (1710000000000, 90000.0, 90500.0, 89500.0, 90300.0),
                        (1710000900000, 90300.0, 91000.0, 90200.0, 90850.0),
                    ],
                    "15m",
                    "futures",
                )
            ],
        )
        self.assertEqual(
            app.chart_points,
            [
                (1710000000000, 90000.0, 90500.0, 89500.0, 90300.0),
                (1710000900000, 90300.0, 91000.0, 90200.0, 90850.0),
            ],
        )
        self.assertEqual(app.previous_price, 91000.0)


if __name__ == "__main__":
    unittest.main()
