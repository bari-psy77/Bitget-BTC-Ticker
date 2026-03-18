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
            self.assertEqual(config["opacity"], 0.85)
            self.assertEqual(config["position"], "bottom-right")
            self.assertIsNone(config["custom_position"])

    def test_save_excludes_runtime_alarm_states(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.json"
            manager = ConfigManager(config_path=config_path)

            payload = {
                "interval_seconds": 600,
                "alarms": [95000.0, 100000.0],
                "opacity": 0.65,
                "position": "top-left",
                "custom_position": {"x": 120, "y": 80},
                "alarm_states": {"95000.0": "above"},
            }

            manager.save(payload)

            saved = json.loads(config_path.read_text(encoding="utf-8"))
            self.assertNotIn("alarm_states", saved)
            self.assertEqual(saved["interval_seconds"], 600)
            self.assertEqual(saved["alarms"], [95000.0, 100000.0])
            self.assertEqual(saved["opacity"], 0.65)
            self.assertEqual(saved["position"], "top-left")
            self.assertEqual(saved["custom_position"], {"x": 120, "y": 80})

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
            self.assertEqual(config["position"], "bottom-right")

    def test_load_clamps_interval_seconds_and_custom_position(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.json"
            config_path.write_text(
                json.dumps(
                    {
                        "interval_seconds": 5,
                        "position": "custom",
                        "custom_position": {"x": "40", "y": 75.8},
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            manager = ConfigManager(config_path=config_path)
            config = manager.load()

            self.assertEqual(config["interval_seconds"], 30)
            self.assertEqual(config["position"], "custom")
            self.assertEqual(config["custom_position"], {"x": 40, "y": 75})


if __name__ == "__main__":
    unittest.main()
