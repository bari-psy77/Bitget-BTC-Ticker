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
            self.assertEqual(config["market_type"], "futures")
            self.assertEqual(config["chart_timeframe"], "15m")
            self.assertFalse(config["chart_always_visible"])
            self.assertTrue(config["chart_hover_enabled"])
            self.assertEqual(config["alarms"], [])
            self.assertEqual(config["price_lines"], [])
            self.assertEqual(config["opacity"], 0.85)
            self.assertIsNone(config["custom_position"])
            self.assertNotIn("position", config)
            self.assertNotIn("alert_mode", config)

    def test_save_excludes_runtime_alarm_states(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.json"
            manager = ConfigManager(config_path=config_path)

            payload = {
                "interval_seconds": 600,
                "alarms": [
                    {"price": 95000.0, "enabled": True, "mode": "popup"},
                    {"price": 100000.0, "enabled": False, "mode": "notification"},
                ],
                "market_type": "spot",
                "chart_timeframe": "5m",
                "chart_always_visible": True,
                "chart_hover_enabled": False,
                "opacity": 0.65,
                "custom_position": {"x": 120, "y": 80},
                "price_lines": [
                    {"price": 95000.0, "color": "red"},
                    {"price": 100000.0, "color": "blue"},
                ],
                "alarm_states": {"95000.0": "above"},
            }

            manager.save(payload)

            saved = json.loads(config_path.read_text(encoding="utf-8"))
            self.assertNotIn("alarm_states", saved)
            self.assertEqual(saved["interval_seconds"], 600)
            self.assertEqual(
                saved["alarms"],
                [
                    {"price": 95000.0, "enabled": True, "mode": "popup"},
                    {"price": 100000.0, "enabled": False, "mode": "notification"},
                ],
            )
            self.assertEqual(saved["market_type"], "spot")
            self.assertEqual(saved["chart_timeframe"], "5m")
            self.assertTrue(saved["chart_always_visible"])
            self.assertFalse(saved["chart_hover_enabled"])
            self.assertEqual(saved["opacity"], 0.65)
            self.assertEqual(saved["custom_position"], {"x": 120, "y": 80})
            self.assertEqual(
                saved["price_lines"],
                [
                    {"price": 95000.0, "color": "red"},
                    {"price": 100000.0, "color": "blue"},
                ],
            )
            self.assertNotIn("position", saved)
            self.assertNotIn("alert_mode", saved)

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
            self.assertEqual(config["market_type"], "futures")
            self.assertEqual(config["chart_timeframe"], "15m")
            self.assertFalse(config["chart_always_visible"])
            self.assertTrue(config["chart_hover_enabled"])
            self.assertEqual(config["price_lines"], [])
            self.assertIsNone(config["custom_position"])
            self.assertNotIn("position", config)
            self.assertNotIn("alert_mode", config)

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

            self.assertEqual(config["interval_seconds"], 10)
            self.assertEqual(
                config["alarms"],
                [],
            )
            self.assertEqual(config["price_lines"], [])
            self.assertEqual(config["chart_timeframe"], "15m")
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
            self.assertEqual(config["chart_timeframe"], "15m")
            self.assertFalse(config["chart_always_visible"])
            self.assertTrue(config["chart_hover_enabled"])
            self.assertEqual(config["price_lines"], [])
            self.assertIsNone(config["custom_position"])
            self.assertNotIn("position", config)

    def test_load_converts_legacy_alarm_numbers_to_enabled_alarm_entries(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.json"
            config_path.write_text(
                json.dumps(
                    {
                        "alarms": [95000, "100000.5"],
                        "alert_mode": "notification",
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
                    {"price": 95000.0, "enabled": True, "mode": "notification"},
                    {"price": 100000.5, "enabled": True, "mode": "notification"},
                ],
            )
            self.assertEqual(config["market_type"], "futures")
            self.assertEqual(config["chart_timeframe"], "15m")
            self.assertNotIn("alert_mode", config)

    def test_load_normalizes_price_lines_and_ignores_invalid_entries(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.json"
            config_path.write_text(
                json.dumps(
                    {
                        "price_lines": [
                            {"price": "95000", "color": "red"},
                            {"price": 100500.25, "color": "blue"},
                            {"price": "bad", "color": "yellow"},
                            {"price": 92000, "color": "invalid"},
                        ],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            manager = ConfigManager(config_path=config_path)
            config = manager.load()

            self.assertEqual(
                config["price_lines"],
                [
                    {"price": 95000.0, "color": "red"},
                    {"price": 100500.25, "color": "blue"},
                ],
            )

    def test_load_accepts_extended_chart_timeframes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.json"
            config_path.write_text(
                json.dumps(
                    {
                        "chart_timeframe": "4h",
                        "chart_always_visible": 1,
                        "chart_hover_enabled": 0,
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            manager = ConfigManager(config_path=config_path)
            config = manager.load()

            self.assertEqual(config["chart_timeframe"], "4h")
            self.assertTrue(config["chart_always_visible"])
            self.assertFalse(config["chart_hover_enabled"])

    def test_load_normalizes_chart_timeframe(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.json"
            config_path.write_text(
                json.dumps(
                    {
                        "chart_timeframe": "bad-value",
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            manager = ConfigManager(config_path=config_path)
            config = manager.load()

            self.assertEqual(config["chart_timeframe"], "15m")


if __name__ == "__main__":
    unittest.main()
