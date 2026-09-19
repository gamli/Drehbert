import asyncio
import errno
from pathlib import Path
from unittest.mock import patch

import pytest

from drehbert.usb_camera import CameraDisconnectedError, UsbCamera


def create_camera_files(tmp_path: Path, state: str) -> tuple[Path, Path, Path]:
    hid_device_path = tmp_path / "hidg0"
    hid_device_path.touch()

    gadget_udc_path = tmp_path / "configfs" / "drehbert" / "UDC"
    gadget_udc_path.parent.mkdir(parents=True)
    gadget_udc_path.write_text("dummy_udc", encoding="ascii")

    udc_class_path = tmp_path / "udc"
    state_path = udc_class_path / "dummy_udc" / "state"
    state_path.parent.mkdir(parents=True)
    state_path.write_text(state, encoding="ascii")

    return hid_device_path, gadget_udc_path, udc_class_path


def create_camera(tmp_path: Path, state: str = "configured") -> tuple[UsbCamera, Path]:
    hid_device_path, gadget_udc_path, udc_class_path = create_camera_files(tmp_path, state)
    return UsbCamera(
        hid_device_path=hid_device_path,
        gadget_udc_path=gadget_udc_path,
        udc_class_path=udc_class_path,
        key_press_seconds=0,
        ready_poll_seconds=0.01,
    ), udc_class_path / "dummy_udc" / "state"


def test_capture_sends_volume_down_press_and_release(tmp_path: Path) -> None:
    async def run() -> None:
        camera, _ = create_camera(tmp_path)

        async with camera:
            assert camera.is_ready
            await camera.capture_photo()

        assert (tmp_path / "hidg0").read_bytes() == b"\x01\x00\x00"

    asyncio.run(run())


def test_ready_callback_tracks_udc_configuration(tmp_path: Path) -> None:
    async def run() -> None:
        camera, state_path = create_camera(tmp_path, "not attached")
        ready_changes: list[bool] = []
        became_ready = asyncio.Event()

        def ready_changed(ready: bool) -> None:
            ready_changes.append(ready)
            if ready:
                became_ready.set()

        camera.when_ready_changed = ready_changed

        async with camera:
            assert not camera.is_ready
            state_path.write_text("configured", encoding="ascii")
            await asyncio.wait_for(became_ready.wait(), timeout=1)
            assert camera.is_ready

        assert ready_changes == [False, True]

    asyncio.run(run())


def test_capture_does_not_depend_on_cached_ready_state(tmp_path: Path) -> None:
    async def run() -> None:
        camera, _ = create_camera(tmp_path, "not attached")

        async with camera:
            assert not camera.is_ready
            await camera.capture_photo()

        assert (tmp_path / "hidg0").read_bytes() == b"\x01\x00\x00"

    asyncio.run(run())


def test_open_error_is_not_translated(tmp_path: Path) -> None:
    async def run() -> None:
        camera, _ = create_camera(tmp_path)

        with (
            patch(
                "drehbert.usb_camera.os.open",
                side_effect=PermissionError(errno.EACCES, "Permission denied"),
            ),
            pytest.raises(PermissionError),
        ):
            async with camera:
                pass

    asyncio.run(run())


def test_ready_state_read_error_is_not_translated(tmp_path: Path) -> None:
    camera, state_path = create_camera(tmp_path)
    state_path.unlink()

    with pytest.raises(FileNotFoundError):
        camera._read_ready()


def test_disconnect_race_is_reported_as_camera_disconnected(tmp_path: Path) -> None:
    async def run() -> None:
        camera, _ = create_camera(tmp_path)

        async with camera:
            with (
                patch(
                    "drehbert.usb_camera.os.write",
                    side_effect=OSError(errno.ESHUTDOWN, "USB disconnected"),
                ),
                pytest.raises(CameraDisconnectedError, match="disconnected"),
            ):
                await camera.capture_photo()

    asyncio.run(run())


def test_disconnect_during_close_is_ignored(tmp_path: Path) -> None:
    async def run() -> None:
        camera, _ = create_camera(tmp_path)

        with patch(
                "drehbert.usb_camera.os.write",
                side_effect=OSError(errno.ESHUTDOWN, "USB disconnected"),
        ):
            async with camera:
                pass

    asyncio.run(run())


def test_unexpected_close_error_is_not_ignored(tmp_path: Path) -> None:
    async def run() -> None:
        camera, _ = create_camera(tmp_path)

        with (
            patch(
                "drehbert.usb_camera.os.write",
                side_effect=OSError(errno.EIO, "I/O error"),
            ),
            pytest.raises(OSError) as error,
        ):
            async with camera:
                pass

        assert error.value.errno == errno.EIO

    asyncio.run(run())


def test_unexpected_write_error_is_not_translated(tmp_path: Path) -> None:
    async def run() -> None:
        camera, _ = create_camera(tmp_path)

        async with camera:
            with (
                patch(
                    "drehbert.usb_camera.os.write",
                    side_effect=OSError(errno.EIO, "I/O error"),
                ),
                pytest.raises(OSError) as error,
            ):
                await camera.capture_photo()

            assert error.value.errno == errno.EIO

    asyncio.run(run())
