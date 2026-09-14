import pytest

from drehbert.gpio_context_manager import GPIOContextManager


def test_close_accepts_callable_objects_and_runs_cleanup_in_reverse_order() -> None:
    cleanup_order: list[str] = []

    class Cleanup:
        def __init__(self, name: str):
            self._name = name

        def __call__(self) -> None:
            cleanup_order.append(self._name)

    context_manager = GPIOContextManager(Cleanup("first"), Cleanup("second"))

    context_manager.close()
    context_manager.close()

    assert cleanup_order == ["second", "first"]


def test_close_attempts_remaining_cleanup_after_one_fails() -> None:
    cleanup_order: list[str] = []

    def first() -> None:
        cleanup_order.append("first")

    def failing_second() -> None:
        cleanup_order.append("second")
        raise RuntimeError("cleanup failed")

    context_manager = GPIOContextManager(first, failing_second)

    with pytest.raises(RuntimeError, match="cleanup failed"):
        context_manager.close()

    assert cleanup_order == ["second", "first"]


def test_invalid_resource_is_rejected_at_construction() -> None:
    with pytest.raises(TypeError, match="GPIO resources"):
        GPIOContextManager(object())  # type: ignore[arg-type]
