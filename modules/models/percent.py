from typing import Callable

type PercentChangeHandler = Callable[[float], None]


class Percent:
    def __init__(self, steps: int = 100, on_change: PercentChangeHandler | None = None):
        self._f_value = 0.0  # Floating point representation of the percent
        self._steps = steps  # Total number of steps to reach 100%
        self._increment = 100 / steps  # Increment per step
        self._on_change = on_change  # Optional callback function
        # Call the change handler with the initial value
        if on_change:
            on_change(self._f_value)

    def increment(self):
        """Increment the value by the calculated step increment, ensuring it does not exceed 100%."""
        self._f_value = min(100.0, self._f_value + self._increment)
        if self._on_change:
            self._on_change(
                self._f_value
            )  # Trigger change handler with the updated float value

    def set_steps(self, remaining_steps: int):
        """Set new steps and recalculate the increment based on the current value."""
        if remaining_steps > 0:
            self._steps = remaining_steps
            remaining_percentage = 100.0 - self._f_value
            self._increment = remaining_percentage / remaining_steps
        else:
            raise ValueError("Remaining steps must be greater than zero.")

    def reset(self, value: float = 0.0, steps: int = 100):
        """Reset the percentage and steps to a given value, recalculate increment."""
        self._f_value = value
        self.set_steps(steps)
        if self._on_change:
            self._on_change(self._f_value)  # Trigger change handler with the new value

    @property
    def value(self) -> float:
        return self._f_value

    @value.setter
    def value(self, value: float):
        """Set the percentage value, ensuring it's within the valid range."""
        if 0.0 <= value <= 100.0:
            self._f_value = value
            if self._on_change:
                self._on_change(
                    self._f_value
                )  # Trigger change handler with the new float value
            remaining_steps = self._steps
            self.set_steps(
                remaining_steps
            )  # Recalculate increment when value is manually set
        else:
            raise ValueError("Value must be between 0 and 100 for a percentage.")
