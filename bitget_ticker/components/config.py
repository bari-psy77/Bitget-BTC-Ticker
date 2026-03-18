from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class ConfigManager:
    """Load and persist ticker configuration."""

    DEFAULT_CONFIG: dict[str, Any] = {
        "interval_seconds": 300,
        "alarms": [],
        "opacity": 0.85,
        "position": "bottom-right",
        "custom_position": None,
    }
    MIN_INTERVAL_SECONDS = 30
    MAX_INTERVAL_SECONDS = 1800
    POSITION_OPTIONS = {
        "top-left",
        "top-right",
        "bottom-left",
        "bottom-right",
        "center",
        "custom",
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

        interval = data.get("interval_seconds")
        if interval is None:
            legacy_interval = data.get("interval")
            if legacy_interval is not None:
                interval = legacy_interval
                try:
                    interval = int(interval) * 60
                except (TypeError, ValueError):
                    interval = config["interval_seconds"]

        opacity = data.get("opacity", config["opacity"])
        alarms = data.get("alarms", config["alarms"])
        position = data.get("position", config["position"])
        custom_position = data.get("custom_position")

        try:
            interval_value = int(interval)
        except (TypeError, ValueError):
            interval_value = config["interval_seconds"]
        config["interval_seconds"] = min(
            self.MAX_INTERVAL_SECONDS,
            max(self.MIN_INTERVAL_SECONDS, interval_value),
        )

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

        if position in self.POSITION_OPTIONS:
            config["position"] = position

        parsed_custom_position = self._normalize_custom_position(custom_position)
        if config["position"] == "custom" and parsed_custom_position is None:
            config["position"] = self.DEFAULT_CONFIG["position"]
        config["custom_position"] = parsed_custom_position

        return config

    def _normalize_custom_position(
        self,
        custom_position: Any,
    ) -> dict[str, int] | None:
        if not isinstance(custom_position, dict):
            return None

        try:
            x = int(float(custom_position["x"]))
            y = int(float(custom_position["y"]))
        except (KeyError, TypeError, ValueError):
            return None

        return {"x": x, "y": y}
