from __future__ import annotations

import unittest

from bitget_ticker.components.alarm import AlarmEngine


class AlarmEngineTests(unittest.TestCase):
    def test_first_check_only_initializes_states(self) -> None:
        triggered: list[tuple[float, float]] = []
        engine = AlarmEngine(on_alarm=lambda alarm, price: triggered.append((alarm, price)))

        engine.check(90000.0, [95000.0])

        self.assertEqual(triggered, [])
        self.assertEqual(engine.alarm_states["0:95000.0"], "below")

    def test_crossing_threshold_triggers_in_both_directions(self) -> None:
        triggered: list[tuple[float, float]] = []
        engine = AlarmEngine(on_alarm=lambda alarm, price: triggered.append((alarm, price)))

        engine.check(90000.0, [95000.0])
        engine.check(96000.0, [95000.0])
        engine.check(94000.0, [95000.0])

        self.assertEqual(triggered, [(95000.0, 96000.0), (95000.0, 94000.0)])

    def test_reset_clears_runtime_states(self) -> None:
        engine = AlarmEngine(on_alarm=lambda *_args: None)

        engine.check(90000.0, [95000.0])
        engine.reset()

        self.assertEqual(engine.alarm_states, {})

    def test_disabled_alarm_entries_do_not_trigger(self) -> None:
        triggered: list[tuple[float, float]] = []
        engine = AlarmEngine(on_alarm=lambda alarm, price: triggered.append((alarm, price)))

        engine.check(90000.0, [{"price": 95000.0, "enabled": False}])
        engine.check(96000.0, [{"price": 95000.0, "enabled": False}])

        self.assertEqual(triggered, [])
        self.assertEqual(engine.alarm_states, {})

    def test_sound_provider_can_disable_beep_for_notification_mode(self) -> None:
        triggered: list[tuple[float, float]] = []
        beep_calls: list[str] = []
        engine = AlarmEngine(
            on_alarm=lambda alarm, price: triggered.append((alarm, price)),
            beep_func=lambda: beep_calls.append("beep"),
            beep_enabled_provider=lambda: False,
        )

        engine.check(90000.0, [{"price": 95000.0, "enabled": True}])
        engine.check(96000.0, [{"price": 95000.0, "enabled": True}])

        self.assertEqual(triggered, [(95000.0, 96000.0)])
        self.assertEqual(beep_calls, [])


if __name__ == "__main__":
    unittest.main()
