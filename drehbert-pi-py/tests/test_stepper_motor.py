import pytest
from gpiozero.pins.mock import MockFactory

from drehbert.stepper_motor import StepperMotor, EStepperMotorDirection


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
        steps_per_revolution=4,
        steps_per_second=100,
        step_pulse_seconds=0.001,
        sleep_function=sleep_calls.append,
        pin_factory=pin_factory,
    )


def test_rotate_to_degrees_wraps_forward(pin_factory: MockFactory) -> None:
    motor = make_motor(pin_factory)

    motor.rotate_to_degrees(270, EStepperMotorDirection.FORWARD)
    assert motor._current_step == 3

    motor.rotate_to_degrees(360, EStepperMotorDirection.FORWARD)
    assert motor._current_step == 0

    motor.close()


def test_rotate_to_degrees_wraps_reverse(pin_factory: MockFactory) -> None:
    motor = make_motor(pin_factory)

    motor.rotate_to_degrees(270, EStepperMotorDirection.REVERSE)

    assert motor._current_step == 3
    motor.close()


def test_step_uses_short_high_pulse_and_remaining_period(
        pin_factory: MockFactory,
) -> None:
    sleep_calls: list[float] = []
    motor = make_motor(pin_factory, sleep_calls)

    motor.rotate_steps(1, EStepperMotorDirection.REVERSE)

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
        ("steps_per_revolution", 0),
        ("steps_per_second", 0),
    ],
)
def test_step_configuration_must_be_positive(
        pin_factory: MockFactory,
        argument: str,
        value: int | float,
) -> None:
    with pytest.raises(ValueError, match=r"greater than zero|positive integer"):
        StepperMotor(pin_factory=pin_factory, **{argument: value})


@pytest.mark.parametrize("step_count", [True, 1.5])
def test_step_count_must_be_an_integer(
        pin_factory: MockFactory,
        step_count: object,
) -> None:
    motor = make_motor(pin_factory)

    with pytest.raises(TypeError, match="step_count must be an integer"):
        motor.rotate_steps(  # type: ignore[arg-type]
            step_count,
            EStepperMotorDirection.FORWARD,
        )

    motor.close()


def test_invalid_direction_is_rejected(pin_factory: MockFactory) -> None:
    motor = make_motor(pin_factory)

    with pytest.raises(TypeError, match="StepperMotorDirection"):
        motor.rotate_steps(1, "forward")  # type: ignore[arg-type]

    motor.close()
