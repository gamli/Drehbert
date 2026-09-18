import pytest
from drehbert.drehbert_context_manager import DrehbertContextManager


class MockDrehbertContextManager(DrehbertContextManager):
    def __init__(self):
        super().__init__()
        self._close_count = 0

    def _close(self) -> None:
        self._close_count += 1


def test_context_manager_enters_and_exits() -> None:
    manager = MockDrehbertContextManager()
    with manager as m:
        assert isinstance(m, MockDrehbertContextManager)
        assert not m._state
    assert manager._close_count == 1
    assert manager._state


def test_context_manager_close_called_twice() -> None:
    manager = MockDrehbertContextManager()
    manager.close()
    assert manager._close_count == 1
    assert manager._state
    manager.close()  # Call close again; it should not raise an error or double-close
    assert manager._close_count == 1
    assert manager._state


def test_context_manager_close_called_in_with() -> None:
    manager = MockDrehbertContextManager()
    with manager as m:
        m.close()
        assert m._close_count == 1
        assert m._state
    assert manager._close_count == 1
    assert manager._state
    manager.close()
    assert manager._close_count == 1
    assert manager._state


def test_context_manager_raises_when_already_closed() -> None:
    manager = MockDrehbertContextManager()
    manager.close()
    with pytest.raises(RuntimeError, match="Context manager is already closed"):
        with manager:
            pass
