from __future__ import annotations

import unittest
from unittest.mock import patch

from bitget_ticker.ticker import BitgetBTCTicker


class _OverlayStub:
    def __init__(self, chart_visible: bool = False) -> None:
        self.notifications: list[tuple[float, float]] = []
        self.display_updates: list[tuple[float, float | None]] = []
        self.chart_updates: list[tuple[list[tuple[int, float, float, float, float, float]], str, str]] = []
        self.chart_visible = chart_visible

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

    def is_chart_visible(self) -> bool:
        return self.chart_visible


class _RootStub:
    def __init__(self) -> None:
        self.after_calls: list[tuple[int, object]] = []

    def after(self, delay: int, callback) -> None:
        self.after_calls.append((delay, callback))


class _SettingsDialogStub:
    def __init__(self) -> None:
        self.destroy_called = False

    def destroy(self) -> None:
        self.destroy_called = True


class _TrayIconStub:
    def __init__(self) -> None:
        self.stop_called = False

    def stop(self) -> None:
        self.stop_called = True


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

        with patch("bitget_ticker.ticker.time.time", return_value=1710001200.0):
            app._apply_market_snapshot(
                91000.0,
                [
                    (1710000000000, 90000.0, 90500.0, 89500.0, 90300.0, 1234.5),
                    (1710000900000, 90300.0, 91000.0, 90200.0, 90850.0, 5678.9),
                ],
                "15m",
                "futures",
            )

        self.assertEqual(app.overlay.display_updates, [(91000.0, 90000.0)])
        self.assertEqual(
            app.overlay.chart_updates,
            [
                (
                    [
                        (1710000000000, 90000.0, 90500.0, 89500.0, 90300.0, 1234.5),
                        (1710000900000, 90300.0, 91000.0, 90200.0, 91000.0, 5678.9),
                    ],
                    "15m",
                    "futures",
                )
            ],
        )
        self.assertEqual(
            app.chart_points,
            [
                (1710000000000, 90000.0, 90500.0, 89500.0, 90300.0, 1234.5),
                (1710000900000, 90300.0, 91000.0, 90200.0, 91000.0, 5678.9),
            ],
        )
        self.assertEqual(app.previous_price, 91000.0)

    def test_apply_market_snapshot_appends_live_candle_when_api_candles_are_stale(self) -> None:
        app = BitgetBTCTicker.__new__(BitgetBTCTicker)
        app.overlay = _OverlayStub()
        app.previous_price = 90000.0
        app.chart_points = []
        app.config = {
            "market_type": "futures",
            "chart_timeframe": "15m",
        }

        with patch("bitget_ticker.ticker.time.time", return_value=1710001800.0):
            app._apply_market_snapshot(
                91500.0,
                [
                    (1710000000000, 90000.0, 90500.0, 89500.0, 90300.0, 1234.5),
                    (1710000900000, 90300.0, 91000.0, 90200.0, 90850.0, 5678.9),
                ],
                "15m",
                "futures",
            )

        self.assertEqual(
            app.chart_points,
            [
                (1710000000000, 90000.0, 90500.0, 89500.0, 90300.0, 1234.5),
                (1710000900000, 90300.0, 91000.0, 90200.0, 90850.0, 5678.9),
                (1710001800000, 90850.0, 91500.0, 90850.0, 91500.0, 0.0),
            ],
        )

    def test_apply_market_snapshot_uses_cached_chart_points_when_candle_fetch_returns_empty(self) -> None:
        app = BitgetBTCTicker.__new__(BitgetBTCTicker)
        app.overlay = _OverlayStub()
        app.previous_price = 90000.0
        app.chart_points = [
            (1710000000000, 90000.0, 90500.0, 89500.0, 90300.0, 1234.5),
            (1710000900000, 90300.0, 91000.0, 90200.0, 90850.0, 5678.9),
        ]
        app.config = {
            "market_type": "futures",
            "chart_timeframe": "15m",
        }

        with patch("bitget_ticker.ticker.time.time", return_value=1710001200.0):
            app._apply_market_snapshot(
                91234.0,
                [],
                "15m",
                "futures",
            )

        self.assertEqual(
            app.chart_points,
            [
                (1710000000000, 90000.0, 90500.0, 89500.0, 90300.0, 1234.5),
                (1710000900000, 90300.0, 91234.0, 90200.0, 91234.0, 5678.9),
            ],
        )

    def test_should_refresh_chart_respects_force_and_visibility(self) -> None:
        app = BitgetBTCTicker.__new__(BitgetBTCTicker)
        app.overlay = _OverlayStub(chart_visible=False)

        self.assertFalse(app._should_refresh_chart(force_chart_refresh=False))
        self.assertTrue(app._should_refresh_chart(force_chart_refresh=True))

        app.overlay.chart_visible = True
        self.assertTrue(app._should_refresh_chart(force_chart_refresh=False))

    def test_quit_app_destroys_settings_dialog_before_shutdown(self) -> None:
        app = BitgetBTCTicker.__new__(BitgetBTCTicker)
        app.running = True
        app.settings_dialog = _SettingsDialogStub()
        app.tray_icon = _TrayIconStub()
        app.root = _RootStub()

        app.quit_app()

        self.assertFalse(app.running)
        self.assertTrue(app.settings_dialog.destroy_called)
        self.assertTrue(app.tray_icon.stop_called)
        self.assertEqual(len(app.root.after_calls), 1)
        self.assertEqual(app.root.after_calls[0][0], 0)
        self.assertEqual(app.root.after_calls[0][1], app._shutdown_ui)


if __name__ == "__main__":
    unittest.main()
