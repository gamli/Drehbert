import pytest
from gpiozero.pins.mock import MockFactory

from drehbert.drehbert_buttons import DrehbertButtons, EButtonGesture


@pytest.fixture
def pin_factory() -> MockFactory:
    return MockFactory()


def test_release_before_hold_emits_short_press(pin_factory: MockFactory) -> None:
    gestures: list[EButtonGesture] = []

    with DrehbertButtons(long_press_threshold=10, pin_factory=pin_factory) as buttons:
        buttons.when_scan_button_gesture = gestures.append

        buttons._scan_button.when_pressed()
        buttons._scan_button.when_released()

    assert gestures == [EButtonGesture.SHORT_PRESS]


def test_hold_emits_long_press_once_and_release_does_not_emit_short_press(
        pin_factory: MockFactory,
) -> None:
    gestures: list[EButtonGesture] = []

    with DrehbertButtons(long_press_threshold=10, pin_factory=pin_factory) as buttons:
        buttons.when_bluetooth_button_gesture = gestures.append

        buttons._bluetooth_button.when_pressed()
        buttons._bluetooth_button.when_held()
        buttons._bluetooth_button.when_released()

    assert gestures == [EButtonGesture.LONG_PRESS]


def test_long_press_threshold_must_be_positive(pin_factory: MockFactory) -> None:
    with pytest.raises(ValueError, match="greater than zero"):
        DrehbertButtons(long_press_threshold=0, pin_factory=pin_factory)
