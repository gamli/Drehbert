from dbus_next import Variant, DBusError


def read_at_offset(value: bytes, options: dict[str, Variant]) -> bytes:
    offset_option = options.get("offset")
    offset = 0 if offset_option is None else offset_option.value

    if offset > len(value):
        raise DBusError("org.bluez.Error.InvalidOffset", "Invalid read offset")

    return value[offset:]
