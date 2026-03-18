from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class ConfigManager:
    """Load and persist ticker configuration."""

    DEFAULT_CONFIG: dict[str, Any] = {
        "interval": 5,
        "alarms": [],
        "opacity": 0.85,
    }

    def __init__(self, config_path: Path | None = None) -> None:
        self.config_path = config_path or (Path.home() / ".bitget_ticker_config.json")

    def load(self) -> dict[str, Any]:
        if not self.config_path.exists():
            return self.DEFAULT_CONFIG.copy()

        try:
            raw = json.loads(self.config_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return self.DEFAULT_CONFIG.copy()

        return self._normalize(raw)

    def save(self, config: dict[str, Any]) -> dict[str, Any]:
        normalized = self._normalize(config)
        payload = {
            key: value
            for key, value in normalized.items()
            if key != "alarm_states"
        }
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.config_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return payload

    def _normalize(self, data: dict[str, Any] | None) -> dict[str, Any]:
        config = self.DEFAULT_CONFIG.copy()
        if not isinstance(data, dict):
            return config

        interval = data.get("interval", config["interval"])
        opacity = data.get("opacity", config["opacity"])
        alarms = data.get("alarms", config["alarms"])

        try:
            interval_value = int(interval)
        except (TypeError, ValueError):
            interval_value = config["interval"]
        config["interval"] = interval_value if interval_value > 0 else config["interval"]

        try:
            opacity_value = float(opacity)
        except (TypeError, ValueError):
            opacity_value = config["opacity"]
        config["opacity"] = min(1.0, max(0.2, opacity_value))

        parsed_alarms: list[float] = []
        if isinstance(alarms, list):
            for alarm in alarms:
                try:
                    parsed_alarms.append(float(alarm))
                except (TypeError, ValueError):
                    continue
        config["alarms"] = sorted(parsed_alarms)

        return config
