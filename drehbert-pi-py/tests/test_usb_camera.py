import asyncio
import errno
from pathlib import Path
from unittest.mock import patch

import pytest

from drehbert.usb_camera import CameraUnavailableError, UsbCamera


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

        assert ready_changes == [False, True, False]

    asyncio.run(run())


def test_capture_rechecks_state_before_writing(tmp_path: Path) -> None:
    async def run() -> None:
        camera, state_path = create_camera(tmp_path)

        async with camera:
            assert camera.is_ready
            state_path.write_text("not attached", encoding="ascii")

            with pytest.raises(CameraUnavailableError, match="not ready"):
                await camera.capture_photo()

            assert not camera.is_ready

    asyncio.run(run())


def test_disconnect_race_is_reported_as_camera_unavailable(tmp_path: Path) -> None:
    async def run() -> None:
        camera, _ = create_camera(tmp_path)
        ready_changes: list[bool] = []
        camera.when_ready_changed = ready_changes.append

        async with camera:
            with (
                patch(
                    "drehbert.usb_camera.os.write",
                    side_effect=OSError(errno.ESHUTDOWN, "USB disconnected"),
                ),
                pytest.raises(CameraUnavailableError, match="disconnected"),
            ):
                await camera.capture_photo()

            assert not camera.is_ready
            assert ready_changes[-1] is False

    asyncio.run(run())
