from __future__ import annotations

import unittest

from bitget_ticker.components.settings import SettingsDialog
from bitget_ticker.components.tray import TrayIcon


class UiStringTests(unittest.TestCase):
    def test_settings_dialog_uses_english_drag_guide(self) -> None:
        self.assertEqual(
            SettingsDialog.DRAG_GUIDE_TEXT,
            "Drag the overlay with the mouse to save its position.",
        )

    def test_settings_dialog_exposes_alert_mode_labels(self) -> None:
        self.assertEqual(SettingsDialog.POPUP_MODE_LABEL, "Popup")
        self.assertEqual(SettingsDialog.NOTIFICATION_MODE_LABEL, "Notification")

    def test_tray_menu_labels_are_english(self) -> None:
        self.assertEqual(TrayIcon.SETTINGS_MENU_LABEL, "Settings")
        self.assertEqual(TrayIcon.QUIT_MENU_LABEL, "Quit")


if __name__ == "__main__":
    unittest.main()
