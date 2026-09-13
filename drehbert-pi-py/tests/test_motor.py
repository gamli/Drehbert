import pytest

from drehbert.stepper_motor import StepperMotor, StepperMotorDirection
from tests.fake_stepper_motor_factory import create_fake_stepper_motor


def test_one_revolution_sends_exactly_3200_rising_edges() -> None:
    motor, step_pin, direction_pin, enable_pin, sleeps = create_fake_stepper_motor()

    with motor:
        motor.rotate_one_revolution(StepperMotorDirection.FORWARD)

        assert sum(step_pin.transitions) == 3200
        assert step_pin.state is False
        assert direction_pin.state is True
        assert enable_pin.state is False
        assert sleeps[0] == StepperMotor.DIRECTION_SETUP_DELAY_SECONDS
        assert sleeps[1:] == [0.5 / StepperMotor.STEPS_PER_SECOND] * 6400


def test_reverse_direction_sets_dir_low() -> None:
    motor, step_pin, direction_pin, enable_pin, sleeps = create_fake_stepper_motor()

    with motor:
        motor.rotate_steps(1, StepperMotorDirection.REVERSE)
        assert direction_pin.state is False
        assert sum(step_pin.transitions) == 1


def test_context_manager_resets_pins_correctly_on_sleep_error() -> None:
    sleep_calls = 0

    def failing_sleep(_: float) -> None:
        nonlocal sleep_calls
        sleep_calls += 1
        if sleep_calls == 2:
            raise RuntimeError("synthetic failure")

    motor, step_pin, direction_pin, enable_pin, sleeps = create_fake_stepper_motor(failing_sleep)

    with motor:
        with pytest.raises(RuntimeError, match="synthetic failure"):
            motor.rotate_steps(1, StepperMotorDirection.FORWARD)

    assert step_pin.state is False
    assert direction_pin.state is True
    assert enable_pin.state is True


def test_context_manager_closes_all_output_pins() -> None:
    motor, step_pin, direction_pin, enable_pin, sleeps = create_fake_stepper_motor()

    with motor:
        pass

    assert step_pin.closed is True
    assert direction_pin.closed is True
    assert enable_pin.closed is True


def test_context_manager_initializes_pins_correctly() -> None:
    motor, step_pin, direction_pin, enable_pin, sleeps = create_fake_stepper_motor()

    with motor:
        assert step_pin.state is False
        assert direction_pin.state is True
        assert enable_pin.state is False


def test_context_manager_resets_pins_correctly() -> None:
    motor, step_pin, direction_pin, enable_pin, sleeps = create_fake_stepper_motor()

    with motor:
        pass

    assert step_pin.state is False
    assert direction_pin.state is True
    assert enable_pin.state is True
