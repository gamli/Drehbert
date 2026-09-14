import pytest
from gpiozero.pins.mock import MockFactory

from drehbert.stepper_motor import StepperMotor, StepperMotorDirection


@pytest.fixture
def pin_factory() -> MockFactory:
    return MockFactory()


def make_motor(
        pin_factory: MockFactory,
        sleep_calls: list[float] | None = None,
) -> StepperMotor:
    if sleep_calls is None:
        sleep_calls = []

    return StepperMotor(
        full_steps_per_revolution=4,
        configured_microsteps_per_full_step=1,
        microsteps_per_second=100,
        step_pulse_seconds=0.001,
        sleep_function=sleep_calls.append,
        pin_factory=pin_factory,
    )


def test_rotate_to_degrees_wraps_forward(pin_factory: MockFactory) -> None:
    motor = make_motor(pin_factory)

    motor.rotate_to_degrees(270, StepperMotorDirection.FORWARD)
    assert motor._current_step == 3

    motor.rotate_to_degrees(360, StepperMotorDirection.FORWARD)
    assert motor._current_step == 0

    motor.close()


def test_rotate_to_degrees_wraps_reverse(pin_factory: MockFactory) -> None:
    motor = make_motor(pin_factory)

    motor.rotate_to_degrees(270, StepperMotorDirection.REVERSE)

    assert motor._current_step == 3
    motor.close()


def test_step_uses_short_high_pulse_and_remaining_period(
        pin_factory: MockFactory,
) -> None:
    sleep_calls: list[float] = []
    motor = make_motor(pin_factory, sleep_calls)

    motor.rotate_steps(1, StepperMotorDirection.REVERSE)

    assert sleep_calls == pytest.approx([0.001, 0.009])
    motor.close()


def test_close_disables_driver_and_releases_all_gpio_devices(
        pin_factory: MockFactory,
) -> None:
    motor = make_motor(pin_factory)

    motor.close()

    assert motor._motor_step.closed
    assert motor._motor_dir.closed
    assert motor._motor_enable.closed


@pytest.mark.parametrize(
    ("argument", "value"),
    [
        ("full_steps_per_revolution", 0),
        ("configured_microsteps_per_full_step", 0),
        ("microsteps_per_second", 0),
    ],
)
def test_integer_configuration_must_be_positive(
        pin_factory: MockFactory,
        argument: str,
        value: int,
) -> None:
    with pytest.raises(ValueError, match="positive integer"):
        StepperMotor(pin_factory=pin_factory, **{argument: value})


def test_invalid_direction_is_rejected(pin_factory: MockFactory) -> None:
    motor = make_motor(pin_factory)

    with pytest.raises(TypeError, match="StepperMotorDirection"):
        motor.rotate_steps(1, "forward")  # type: ignore[arg-type]

    motor.close()
