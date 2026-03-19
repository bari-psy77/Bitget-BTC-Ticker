from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class ConfigManager:
    """Load and persist ticker configuration."""

    DEFAULT_CONFIG: dict[str, Any] = {
        "interval_seconds": 300,
        "market_type": "futures",
        "chart_timeframe": "15m",
        "alarms": [],
        "opacity": 0.85,
        "custom_position": None,
    }
    MIN_INTERVAL_SECONDS = 30
    MAX_INTERVAL_SECONDS = 1800
    MARKET_TYPE_OPTIONS = {"spot", "futures"}
    CHART_TIMEFRAME_OPTIONS = {"5m", "15m"}
    ALARM_MODE_OPTIONS = {"popup", "notification"}

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
        market_type = data.get("market_type", config["market_type"])
        chart_timeframe = data.get("chart_timeframe", config["chart_timeframe"])
        alarms = data.get("alarms", config["alarms"])
        legacy_alert_mode = data.get("alert_mode", "popup")
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

        if market_type in self.MARKET_TYPE_OPTIONS:
            config["market_type"] = market_type
        if chart_timeframe in self.CHART_TIMEFRAME_OPTIONS:
            config["chart_timeframe"] = chart_timeframe

        parsed_alarms: list[dict[str, Any]] = []
        if isinstance(alarms, list):
            for alarm in alarms:
                parsed_alarm = self._normalize_alarm_entry(alarm, legacy_alert_mode)
                if parsed_alarm is not None:
                    parsed_alarms.append(parsed_alarm)
        config["alarms"] = parsed_alarms

        config["custom_position"] = self._normalize_custom_position(custom_position)

        return config

    def _normalize_alarm_entry(
        self,
        alarm: Any,
        default_mode: Any = "popup",
    ) -> dict[str, Any] | None:
        raw_price = alarm
        enabled = True
        mode = default_mode if default_mode in self.ALARM_MODE_OPTIONS else "popup"

        if isinstance(alarm, dict):
            raw_price = alarm.get("price")
            enabled = bool(alarm.get("enabled", True))
            raw_mode = alarm.get("mode", mode)
            if raw_mode in self.ALARM_MODE_OPTIONS:
                mode = raw_mode

        try:
            price = float(raw_price)
        except (TypeError, ValueError):
            return None

        return {
            "price": price,
            "enabled": enabled,
            "mode": mode,
        }

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
