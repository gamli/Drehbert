import asyncio
import logging
import os
from collections.abc import Callable
from contextlib import suppress
from pathlib import Path
from typing import Final, override

from drehbert.drehbert_context_manager import DrehbertAsyncContextManager
from drehbert.optional_value import OptionalValue

LOGGER = logging.getLogger(__name__)

type CameraReadyChangedHandler = Callable[[bool], None]


class CameraUnavailableError(RuntimeError):
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
        self._ready_event = OptionalValue[asyncio.Event]("_ready_event")
        self._capture_lock = OptionalValue[asyncio.Lock]("_capture_lock")
        self._ready_monitor = OptionalValue[asyncio.Task[None]]("_ready_monitor")
        self._ready = False

    @property
    def is_ready(self) -> bool:
        self._assert_open()
        return self._ready

    @override
    async def _open(self) -> None:
        try:
            hid_fd = os.open(
                self._hid_device_path,
                os.O_WRONLY | os.O_NONBLOCK | os.O_CLOEXEC,
            )
        except OSError as error:
            raise CameraUnavailableError(
                f"Cannot open USB HID device {self._hid_device_path}",
            ) from error

        self._hid_fd(hid_fd)
        self._ready_event(asyncio.Event())
        self._capture_lock(asyncio.Lock())
        self._set_ready(self._read_ready(), force_notification=True)
        self._ready_monitor(
            asyncio.create_task(
                self._monitor_ready(),
                name="usb-camera-ready-monitor",
            )
        )

    @override
    async def _close(self) -> None:
        if self._ready_monitor.is_set():
            monitor = self._ready_monitor()
            monitor.cancel()
            with suppress(asyncio.CancelledError):
                await monitor
            self._ready_monitor.reset()

        if self._hid_fd.is_set():
            with suppress(OSError):
                self._write_report(self._RELEASE_REPORT)
            os.close(self._hid_fd())
            self._hid_fd.reset()

        self._set_ready(False)
        self._ready_event.reset()
        self._capture_lock.reset()

    async def wait_until_ready(self) -> None:
        self._assert_open()
        await self._ready_event().wait()

    async def capture_photo(self) -> None:
        self._assert_open()

        async with self._capture_lock():
            self._set_ready(self._read_ready())
            if not self._ready:
                raise CameraUnavailableError("USB camera remote is not ready")

            pressed = False
            try:
                self._write_report(self._PRESS_REPORT)
                pressed = True
                await asyncio.sleep(self._key_press_seconds)
                self._write_report(self._RELEASE_REPORT)
                pressed = False
            except OSError as error:
                self._set_ready(False)
                raise CameraUnavailableError(
                    "USB camera remote disconnected while capturing",
                ) from error
            finally:
                if pressed:
                    with suppress(OSError):
                        self._write_report(self._RELEASE_REPORT)

    async def _monitor_ready(self) -> None:
        while True:
            self._set_ready(self._read_ready())
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

    def _set_ready(self, ready: bool, *, force_notification: bool = False) -> None:
        if ready == self._ready and not force_notification:
            return

        self._ready = ready
        if self._ready_event.is_set():
            if ready:
                self._ready_event().set()
            else:
                self._ready_event().clear()

        if self.when_ready_changed is not None:
            try:
                self.when_ready_changed(ready)
            except Exception:
                LOGGER.exception("USB camera ready-state handler failed")

    def _write_report(self, report: bytes) -> None:
        written = os.write(self._hid_fd(), report)
        if written != len(report):
            raise OSError(f"Incomplete HID report: wrote {written} of {len(report)} bytes")
