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
    ) -> None:
        self.on_alarm = on_alarm
        self.beep_func = beep_func or self._play_beep
        self.alarm_states: dict[str, str] = {}

    def check(self, price: float, alarms: Iterable[float]) -> None:
        alarm_list = [float(alarm) for alarm in alarms]
        active_keys = {str(alarm) for alarm in alarm_list}
        stale_keys = set(self.alarm_states) - active_keys
        for key in stale_keys:
            self.alarm_states.pop(key, None)

        for alarm_price in alarm_list:
            key = str(alarm_price)
            current_side = "above" if price >= alarm_price else "below"
            previous_side = self.alarm_states.get(key)

            if previous_side is None:
                self.alarm_states[key] = current_side
                continue

            if previous_side == current_side:
                continue

            self.alarm_states[key] = current_side
            self.on_alarm(alarm_price, price)
            threading.Thread(target=self.beep_func, daemon=True).start()

    def reset(self) -> None:
        self.alarm_states = {}

    def _play_beep(self) -> None:
        if winsound is None:
            return

        for _ in range(3):
            winsound.Beep(1200, 400)
