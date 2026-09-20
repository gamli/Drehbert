from dbus_next import PropertyAccess, DBusError
from dbus_next.service import ServiceInterface, dbus_property, method

from drehbert.dbus_utils import DBUS_STRING, DBUS_OBJECT_PATH, DBUS_BYTE_ARRAY, DBUS_BOOLEAN, \
    DBUS_STRING_ARRAY, DBUS_OPTIONS
from ..binary_utils import read_at_offset


# noinspection PyPep8Naming
class BluezGattCharacteristic1(ServiceInterface):

    def __init__(self, uuid: str, service_path: str, flags: list[str], value: DBUS_BYTE_ARRAY) -> None:
        super().__init__("org.bluez.GattCharacteristic1")
        self._uuid = uuid
        self._service_path = service_path
        self._flags = flags
        self._value = value
        self._notifying = False

    @property
    def is_notifying(self) -> bool:
        return self._notifying

    def set_value(self, value: DBUS_BYTE_ARRAY) -> None:
        self._value = value
        self.emit_properties_changed({"Value": value})

    @dbus_property(access=PropertyAccess.READ)
    def UUID(self) -> DBUS_STRING:
        return self._uuid

    @dbus_property(access=PropertyAccess.READ)
    def Service(self) -> DBUS_OBJECT_PATH:
        return self._service_path

    @dbus_property(access=PropertyAccess.READ)
    def Value(self) -> DBUS_BYTE_ARRAY:
        return self._value

    @dbus_property(access=PropertyAccess.READ)
    def Notifying(self) -> DBUS_BOOLEAN:
        return self._notifying

    @dbus_property(access=PropertyAccess.READ)
    def Flags(self) -> DBUS_STRING_ARRAY:
        return self._flags

    @method()
    def ReadValue(self, options: DBUS_OPTIONS) -> DBUS_BYTE_ARRAY:
        return read_at_offset(self._value, options)

    @method()
    def WriteValue(self, value: DBUS_BYTE_ARRAY, options: DBUS_OPTIONS) -> None:
        if "offset" in options and options["offset"].value != 0:
            raise DBusError("org.bluez.Error.InvalidOffset", "Invalid write offset")

        # TODO should not be necessary, but mypy complains?!?
        # noinspection bad-argument-type
        self.set_value(value)

    @method()
    def StartNotify(self) -> None:
        if not self._notifying:
            self._notifying = True
            self.emit_properties_changed({"Notifying": True})

    @method()
    def StopNotify(self) -> None:
        if self._notifying:
            self._notifying = False
            self.emit_properties_changed({"Notifying": False})
