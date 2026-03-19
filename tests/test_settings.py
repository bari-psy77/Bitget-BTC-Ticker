from __future__ import annotations

import unittest

from bitget_ticker.components.settings import SettingsDialog


class SettingsDialogLayoutTests(unittest.TestCase):
    def test_resolve_scroll_canvas_width_uses_fallback_when_widget_not_ready(self) -> None:
        self.assertEqual(
            SettingsDialog.resolve_scroll_canvas_width(measured_width=1, fallback_width=560),
            560,
        )
        self.assertEqual(
            SettingsDialog.resolve_scroll_canvas_width(measured_width=0, fallback_width=560),
            560,
        )
        self.assertEqual(
            SettingsDialog.resolve_scroll_canvas_width(measured_width=720, fallback_width=560),
            720,
        )


if __name__ == "__main__":
    unittest.main()
