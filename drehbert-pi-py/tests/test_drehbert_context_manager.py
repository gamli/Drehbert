import pytest
from drehbert.drehbert_context_manager import DrehbertContextManager


class MockDrehbertContextManager(DrehbertContextManager):
    def __init__(self):
        super().__init__()
        self._was_closed = False

    def _close(self) -> None:
        self._was_closed = True


def test_context_manager_enters_and_exits() -> None:
    manager = MockDrehbertContextManager()
    with manager as m:
        assert isinstance(m, MockDrehbertContextManager)
        assert not m._closed
    assert manager._was_closed
    assert manager._closed


def test_context_manager_close_called_twice() -> None:
    manager = MockDrehbertContextManager()
    manager.close()
    assert manager._was_closed
    assert manager._closed
    manager.close()  # Call close again; it should not raise an error or double-close
    assert manager._was_closed
    assert manager._closed


def test_context_manager_close_called_in_with() -> None:
    manager = MockDrehbertContextManager()
    with manager as m:
        m.close()
        assert m._was_closed
        assert m._closed
    assert manager._was_closed
    assert manager._closed
    manager.close()
    assert manager._was_closed
    assert manager._closed


def test_context_manager_raises_when_already_closed() -> None:
    manager = MockDrehbertContextManager()
    manager.close()
    with pytest.raises(RuntimeError, match="Context manager is already closed"):
        with manager:
            pass
