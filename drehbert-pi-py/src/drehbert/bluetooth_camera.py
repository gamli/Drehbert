from typing import Callable


class BluetoothCamera:
    def capture_photo(self) -> None:
        pass


class BluetoothCameraManager:

    def __init__(self):
        self.when_pairing_mode_exited: Callable[[], None] | None = None

    def connected_camera(self) -> BluetoothCamera | None:
        pass

    def is_camera_connected(self) -> bool:
        pass

    def is_camera_bonded(self) -> bool:
        pass

    def enter_pairing_mode(self) -> None:
        pass
