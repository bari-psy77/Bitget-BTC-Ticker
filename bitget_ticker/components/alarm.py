from __future__ import annotations

import threading
from collections.abc import Callable, Iterable

try:
    import winsound
except ImportError:  # pragma: no cover - Linux/macOS fallback
    winsound = None  # type: ignore[assignment]


class AlarmEngine:
    """Detect cross events for configured price alarms."""

    def __init__(
        self,
        on_alarm: Callable[[float, float], None],
        beep_func: Callable[[], None] | None = None,
        beep_enabled_provider: Callable[[], bool] | None = None,
    ) -> None:
        self.on_alarm = on_alarm
        self.beep_func = beep_func or self._play_beep
        self.beep_enabled_provider = beep_enabled_provider or (lambda: True)
        self.alarm_states: dict[str, str] = {}

    def check(self, price: float, alarms: Iterable[float | dict[str, object]]) -> None:
        alarm_list = self._normalize_alarms(alarms)
        active_keys = {key for key, _alarm_price in alarm_list}
        stale_keys = set(self.alarm_states) - active_keys
        for key in stale_keys:
            self.alarm_states.pop(key, None)

        for key, alarm_price in alarm_list:
            current_side = "above" if price >= alarm_price else "below"
            previous_side = self.alarm_states.get(key)

            if previous_side is None:
                self.alarm_states[key] = current_side
                continue

            if previous_side == current_side:
                continue

            self.alarm_states[key] = current_side
            self.on_alarm(alarm_price, price)
            if self.beep_enabled_provider():
                threading.Thread(target=self.beep_func, daemon=True).start()

    def reset(self) -> None:
        self.alarm_states = {}

    def _normalize_alarms(
        self,
        alarms: Iterable[float | dict[str, object]],
    ) -> list[tuple[str, float]]:
        normalized: list[tuple[str, float]] = []

        for index, alarm in enumerate(alarms):
            enabled = True
            raw_price: object = alarm

            if isinstance(alarm, dict):
                raw_price = alarm.get("price")
                enabled = bool(alarm.get("enabled", True))

            if not enabled:
                continue

            try:
                alarm_price = float(raw_price)
            except (TypeError, ValueError):
                continue

            normalized.append((f"{index}:{alarm_price}", alarm_price))

        return normalized

    def _play_beep(self) -> None:
        if winsound is None:
            return

        for _ in range(3):
            winsound.Beep(1200, 400)
