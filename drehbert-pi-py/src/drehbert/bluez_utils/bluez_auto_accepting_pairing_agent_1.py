from dbus_next.service import ServiceInterface, method

from ..dbus_utils import DBUS_OBJECT_PATH, DBUS_UINT32, DBUS_STRING


# noinspection PyPep8Naming
class BlueZAutoAcceptingPairingAgent1(ServiceInterface):

    def __init__(self) -> None:
        super().__init__("org.bluez.Agent1")

    @method()
    def Release(self) -> None:
        pass

    @method()
    def RequestConfirmation(self, device: DBUS_OBJECT_PATH, passkey: DBUS_UINT32) -> None:
        pass

    @method()
    def RequestAuthorization(self, device: DBUS_OBJECT_PATH) -> None:
        pass

    @method()
    def AuthorizeService(self, device: DBUS_OBJECT_PATH, uuid: DBUS_STRING) -> None:
        pass

    @method()
    def Cancel(self) -> None:
        pass
