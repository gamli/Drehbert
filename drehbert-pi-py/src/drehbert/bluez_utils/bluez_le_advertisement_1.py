from typing import Literal

from dbus_next import PropertyAccess
from dbus_next.service import ServiceInterface, method, dbus_property

from ..dbus_utils.dbus_types import DBUS_STRING, DBUS_STRING_ARRAY, DBUS_UINT16

type BluezAdvertisedType = Literal["peripheral", "broadcast"]


# noinspection PyPep8Naming
class BluezLEAdvertisement1(ServiceInterface):

    def __init__(
            self,
            bluez_advertised_type: BluezAdvertisedType,
            local_name: str,
            service_uuid: str,
            appearance: int
    ) -> None:
        super().__init__("org.bluez.LEAdvertisement1")
        self._bluez_advertised_type = bluez_advertised_type
        self._local_name = local_name
        self._service_uuids = [service_uuid]
        self._appearance = appearance

    @method()
    def Release(self) -> None:
        pass

    @dbus_property(access=PropertyAccess.READ)
    def Type(self) -> DBUS_STRING:
        return self._bluez_advertised_type

    @dbus_property(access=PropertyAccess.READ)
    def LocalName(self) -> DBUS_STRING:
        return self._local_name

    @dbus_property(access=PropertyAccess.READ)
    def ServiceUUIDs(self) -> DBUS_STRING_ARRAY:
        return self._service_uuids

    @dbus_property(access=PropertyAccess.READ)
    def Appearance(self) -> DBUS_UINT16:
        return self._appearance
