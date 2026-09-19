import asyncio
import errno
import os
from collections.abc import Callable
from contextlib import suppress
from pathlib import Path
from typing import Final, override

from drehbert.drehbert_context_manager import DrehbertAsyncContextManager
from drehbert.optional_value import OptionalValue

type CameraReadyChangedHandler = Callable[[bool], None]


class CameraDisconnectedError(RuntimeError):
    pass


class UsbCamera(DrehbertAsyncContextManager):
    _PRESS_REPORT: Final = b"\x01"
    _RELEASE_REPORT: Final = b"\x00"

    def __init__(
        self,
        *,
        hid_device_path: Path = Path("/dev/hidg0"),
        gadget_udc_path: Path = Path("/sys/kernel/config/usb_gadget/drehbert/UDC"),
        udc_class_path: Path = Path("/sys/class/udc"),
        key_press_seconds: float = 0.05,
        ready_poll_seconds: float = 0.1,
    ) -> None:
        super().__init__()

        if key_press_seconds < 0:
            raise ValueError("key_press_seconds must not be negative")
        if ready_poll_seconds <= 0:
            raise ValueError("ready_poll_seconds must be greater than zero")

        self._hid_device_path = hid_device_path
        self._gadget_udc_path = gadget_udc_path
        self._udc_class_path = udc_class_path
        self._key_press_seconds = key_press_seconds
        self._ready_poll_seconds = ready_poll_seconds

        self.when_ready_changed: CameraReadyChangedHandler | None = None

        self._hid_fd = OptionalValue[int]("_hid_fd")
        self._ready_polling_task = OptionalValue[asyncio.Task[None]]("_ready_polling_task")
        self._is_ready = False

    @property
    def is_ready(self) -> bool:
        self._assert_open()
        return self._is_ready

    @override
    async def _open(self) -> None:
        hid_fd = os.open(
            self._hid_device_path,
            os.O_WRONLY | os.O_NONBLOCK | os.O_CLOEXEC,
        )

        self._hid_fd(hid_fd)
        self._is_ready = self._read_ready()
        if self.when_ready_changed is not None:
            self.when_ready_changed(self._is_ready)

        self._ready_polling_task(
            asyncio.create_task(
                self._poll_ready_state(),
                name="usb-camera-ready-state-polling",
            )
        )

    @override
    async def _close(self) -> None:
        if self._ready_polling_task.is_set():
            polling_task = self._ready_polling_task()
            polling_task.cancel()
            with suppress(asyncio.CancelledError):
                await polling_task
            self._ready_polling_task.reset()

        if self._hid_fd.is_set():
            with suppress(OSError):
                self._write_report(self._RELEASE_REPORT)
            os.close(self._hid_fd())
            self._hid_fd.reset()

        self._is_ready = False

    async def capture_photo(self) -> None:
        self._assert_open()

        pressed = False
        try:
            self._write_report(self._PRESS_REPORT)
            pressed = True
            await asyncio.sleep(self._key_press_seconds)
            self._write_report(self._RELEASE_REPORT)
            pressed = False
        except OSError as error:
            if error.errno != errno.ESHUTDOWN:
                raise

            raise CameraDisconnectedError(
                "USB camera remote disconnected while capturing",
            ) from error
        finally:
            if pressed:
                with suppress(OSError):
                    self._write_report(self._RELEASE_REPORT)

    async def _poll_ready_state(self) -> None:
        while True:
            is_ready = self._read_ready()
            if is_ready != self._is_ready:
                self._is_ready = is_ready
                if self.when_ready_changed is not None:
                    self.when_ready_changed(is_ready)

            await asyncio.sleep(self._ready_poll_seconds)

    def _read_ready(self) -> bool:
        try:
            udc_name = self._gadget_udc_path.read_text(encoding="ascii").strip()
            if not udc_name:
                return False

            state_path = self._udc_class_path / udc_name / "state"
            return state_path.read_text(encoding="ascii").strip() == "configured"
        except OSError:
            return False

    def _write_report(self, report: bytes) -> None:
        written = os.write(self._hid_fd(), report)
        if written != len(report):
            raise OSError(f"Incomplete HID report: wrote {written} of {len(report)} bytes")
