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

            self.assertEqual(config["interval"], 5)
            self.assertEqual(config["alarms"], [])
            self.assertEqual(config["opacity"], 0.85)

    def test_save_excludes_runtime_alarm_states(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.json"
            manager = ConfigManager(config_path=config_path)

            payload = {
                "interval": 10,
                "alarms": [95000.0, 100000.0],
                "opacity": 0.65,
                "alarm_states": {"95000.0": "above"},
            }

            manager.save(payload)

            saved = json.loads(config_path.read_text(encoding="utf-8"))
            self.assertNotIn("alarm_states", saved)
            self.assertEqual(saved["interval"], 10)
            self.assertEqual(saved["alarms"], [95000.0, 100000.0])
            self.assertEqual(saved["opacity"], 0.65)


if __name__ == "__main__":
    unittest.main()
