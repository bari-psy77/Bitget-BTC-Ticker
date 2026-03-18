from __future__ import annotations

import unittest

from bitget_ticker.components.overlay import OverlayWindow


class OverlayWindowPositionTests(unittest.TestCase):
    def test_resolve_position_defaults_to_bottom_right(self) -> None:
        x, y = OverlayWindow.resolve_position(
            position="bottom-right",
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
            position="custom",
            screen_w=1280,
            screen_h=720,
            custom_position={"x": 2000, "y": -15},
        )

        self.assertEqual((x, y), (1280 - OverlayWindow.WIDTH, 0))


if __name__ == "__main__":
    unittest.main()
