from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from bitget_ticker.components.config import ConfigManager


class ConfigManagerTests(unittest.TestCase):
    def test_load_returns_defaults_when_file_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "missing.json"

            manager = ConfigManager(config_path=config_path)
            config = manager.load()

            self.assertEqual(config["interval_seconds"], 300)
            self.assertEqual(config["alarms"], [])
            self.assertEqual(config["alert_mode"], "popup")
            self.assertEqual(config["opacity"], 0.85)
            self.assertIsNone(config["custom_position"])
            self.assertNotIn("position", config)

    def test_save_excludes_runtime_alarm_states(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.json"
            manager = ConfigManager(config_path=config_path)

            payload = {
                "interval_seconds": 600,
                "alarms": [
                    {"price": 95000.0, "enabled": True},
                    {"price": 100000.0, "enabled": False},
                ],
                "alert_mode": "notification",
                "opacity": 0.65,
                "custom_position": {"x": 120, "y": 80},
                "alarm_states": {"95000.0": "above"},
            }

            manager.save(payload)

            saved = json.loads(config_path.read_text(encoding="utf-8"))
            self.assertNotIn("alarm_states", saved)
            self.assertEqual(saved["interval_seconds"], 600)
            self.assertEqual(
                saved["alarms"],
                [
                    {"price": 95000.0, "enabled": True},
                    {"price": 100000.0, "enabled": False},
                ],
            )
            self.assertEqual(saved["alert_mode"], "notification")
            self.assertEqual(saved["opacity"], 0.65)
            self.assertEqual(saved["custom_position"], {"x": 120, "y": 80})
            self.assertNotIn("position", saved)

    def test_load_converts_legacy_interval_minutes_to_seconds(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.json"
            config_path.write_text(
                json.dumps({"interval": 15, "opacity": 0.9}, ensure_ascii=False),
                encoding="utf-8",
            )

            manager = ConfigManager(config_path=config_path)
            config = manager.load()

            self.assertEqual(config["interval_seconds"], 900)
            self.assertEqual(config["alert_mode"], "popup")
            self.assertIsNone(config["custom_position"])
            self.assertNotIn("position", config)

    def test_load_clamps_interval_seconds_and_custom_position(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.json"
            config_path.write_text(
                json.dumps(
                    {
                        "interval_seconds": 5,
                        "custom_position": {"x": "40", "y": 75.8},
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            manager = ConfigManager(config_path=config_path)
            config = manager.load()

            self.assertEqual(config["interval_seconds"], 30)
            self.assertEqual(
                config["alarms"],
                [],
            )
            self.assertEqual(config["custom_position"], {"x": 40, "y": 75})
            self.assertNotIn("position", config)

    def test_load_ignores_legacy_position_preset_without_custom_coordinates(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.json"
            config_path.write_text(
                json.dumps(
                    {
                        "position": "top-left",
                        "opacity": 0.7,
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            manager = ConfigManager(config_path=config_path)
            config = manager.load()

            self.assertEqual(config["opacity"], 0.7)
            self.assertIsNone(config["custom_position"])
            self.assertNotIn("position", config)

    def test_load_converts_legacy_alarm_numbers_to_enabled_alarm_entries(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.json"
            config_path.write_text(
                json.dumps(
                    {
                        "alarms": [95000, "100000.5"],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            manager = ConfigManager(config_path=config_path)
            config = manager.load()

            self.assertEqual(
                config["alarms"],
                [
                    {"price": 95000.0, "enabled": True},
                    {"price": 100000.5, "enabled": True},
                ],
            )
            self.assertEqual(config["alert_mode"], "popup")


if __name__ == "__main__":
    unittest.main()
