from __future__ import annotations

import unittest

from bitget_ticker.components.overlay import OverlayWindow


class OverlayWindowPositionTests(unittest.TestCase):
    def test_resolve_position_defaults_to_bottom_right(self) -> None:
        x, y = OverlayWindow.resolve_position(
            screen_w=1920,
            screen_h=1080,
        )

        self.assertEqual(
            (x, y),
            (
                1920 - OverlayWindow.WIDTH - OverlayWindow.SCREEN_MARGIN,
                1080 - OverlayWindow.HEIGHT - OverlayWindow.SCREEN_MARGIN,
            ),
        )

    def test_resolve_position_uses_custom_coordinates_with_screen_clamp(self) -> None:
        x, y = OverlayWindow.resolve_position(
            screen_w=1280,
            screen_h=720,
            custom_position={"x": 2000, "y": -15},
        )

        self.assertEqual((x, y), (1280 - OverlayWindow.WIDTH, 0))

    def test_context_menu_labels_are_english(self) -> None:
        self.assertEqual(OverlayWindow.SETTINGS_MENU_LABEL, "Settings")
        self.assertEqual(OverlayWindow.SHOW_HIDE_MENU_LABEL, "Show/Hide")
        self.assertEqual(OverlayWindow.QUIT_MENU_LABEL, "Quit")

    def test_format_volume_large(self) -> None:
        self.assertEqual(OverlayWindow._format_volume(12345.0), "Vol 12,345 BTC")

    def test_format_volume_small(self) -> None:
        self.assertEqual(OverlayWindow._format_volume(0.53), "Vol 0.53 BTC")

    def test_resolve_chart_position_prefers_above_overlay(self) -> None:
        x, y = OverlayWindow.resolve_chart_position(
            overlay_x=1200,
            overlay_y=900,
            screen_w=1920,
            screen_h=1080,
        )

        self.assertEqual(x, 1200 + OverlayWindow.WIDTH - OverlayWindow.CHART_WIDTH)
        self.assertEqual(y, 900 - OverlayWindow.CHART_HEIGHT - 12)

    def test_resolve_chart_position_falls_back_below_when_needed(self) -> None:
        x, y = OverlayWindow.resolve_chart_position(
            overlay_x=20,
            overlay_y=10,
            screen_w=1280,
            screen_h=720,
        )

        self.assertEqual(x, 0)
        self.assertEqual(y, 10 + OverlayWindow.HEIGHT + 12)

    def test_build_notification_message_includes_alarm_and_price(self) -> None:
        message = OverlayWindow.build_notification_message(95000.0, 96010.55)

        self.assertEqual(message, "Hit $95,000")

    def test_build_candle_geometry_returns_body_and_wick(self) -> None:
        geometry = OverlayWindow.build_candle_geometry(
            candles=[
                (1710000000000, 90000.0, 90500.0, 89500.0, 90300.0),
                (1710000900000, 90300.0, 91000.0, 90200.0, 90850.0),
            ],
            width=280,
            height=120,
            padding=16,
        )

        self.assertEqual(len(geometry), 2)
        self.assertEqual(geometry[0]["color"], OverlayWindow.UP_COLOR)
        self.assertLess(geometry[0]["wick_top"], geometry[0]["wick_bottom"])
        self.assertLess(geometry[0]["body_top"], geometry[0]["body_bottom"])

    def test_resolve_canvas_dimension_uses_configured_size_when_widget_not_ready(self) -> None:
        self.assertEqual(OverlayWindow.resolve_canvas_dimension(1, 298), 298)
        self.assertEqual(OverlayWindow.resolve_canvas_dimension(0, 120), 120)
        self.assertEqual(OverlayWindow.resolve_canvas_dimension(250, 298), 250)


if __name__ == "__main__":
    unittest.main()
