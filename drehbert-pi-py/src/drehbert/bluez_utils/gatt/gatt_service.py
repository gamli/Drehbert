from dbus_next import PropertyAccess
from dbus_next.service import ServiceInterface, dbus_property

from drehbert.dbus_utils import DBUS_STRING, DBUS_BOOLEAN


# noinspection PyPep8Naming
class BluezGattService(ServiceInterface):

    def __init__(self, uuid: str) -> None:
        super().__init__("org.bluez.GattService1")
        self._uuid = uuid

    @dbus_property(access=PropertyAccess.READ)
    def UUID(self) -> DBUS_STRING:
        return self._uuid

    @dbus_property(access=PropertyAccess.READ)
    def Primary(self) -> DBUS_BOOLEAN:
        return True
