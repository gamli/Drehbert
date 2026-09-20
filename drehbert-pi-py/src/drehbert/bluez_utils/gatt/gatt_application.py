from dbus_next.service import ServiceInterface

class BluezGattApplication(ServiceInterface):

    def __init__(self, application_name: str) -> None:
        # Exporting an interface at the application path makes dbus-next expose
        # org.freedesktop.DBus.ObjectManager there as required by BlueZ.
        super().__init__(application_name)
