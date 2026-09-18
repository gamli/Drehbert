import asyncio
from typing import Self, TYPE_CHECKING

from bless import (
    BlessGATTCharacteristic,
    BlessServer,
    GATTAttributePermissions,
    GATTCharacteristicProperties,
    GATTDescriptorProperties,
)
from dbus_next import Variant
from dbus_next.aio import MessageBus, ProxyInterface
from dbus_next.constants import BusType
from dbus_next.service import ServiceInterface, method

from drehbert.drehbert_context_manager import DrehbertContextManager, DrehbertAsyncContextManager

type _DBUS_OBJECT_PATH = str
type _DBUS_UINT32 = int

if TYPE_CHECKING:

    class _BluezAgentManager1(ProxyInterface):

        async def call_register_agent(self, agent_path: _DBUS_OBJECT_PATH, capability: str) -> None: ...

        async def call_unregister_agent(self, agent_path: _DBUS_OBJECT_PATH) -> None: ...

        async def call_request_default_agent(self, agent_path: _DBUS_OBJECT_PATH) -> None: ...


    class _BluezAdapter1(ProxyInterface):

        async def call_set(self, adapter_path: _DBUS_OBJECT_PATH, name: str, value: Variant) -> None: ...

else:

    _BluezAgentManager1 = ProxyInterface
    _BluezAdapter1 = ProxyInterface


class BluetoothCamera(DrehbertAsyncContextManager):

    def __init__(self, key_press_seconds: float = 0.05):
        super().__init__()
        self._key_press_seconds = key_press_seconds
        self._server: BlessServer | None = None
        self._dbus: MessageBus | None = None
        self._bluez_pairing_agent: _BlueZAutoAcceptPairingAgent | None = None
        self._agent_manager: _BluezAgentManager1 | None = None
        self._adapter: _BluezAdapter1 | None = None

    async def _open(self) -> None:

        self._dbus = await MessageBus(bus_type=BusType.SYSTEM).connect()
        assert self._dbus is not None

        self._bluez_pairing_agent = _BlueZAutoAcceptPairingAgent()
        assert self._bluez_pairing_agent is not None
        self._dbus.export(self._BLUEZ_PAIRING_AGENT_DBUS_OBJECTPATH, self._bluez_pairing_agent)

        self._agent_manager = await self._dbus_interface(self._dbus, "/org/bluez", "org.bluez.AgentManager1")
        assert self._agent_manager is not None
        await self._agent_manager.call_register_agent(self._BLUEZ_PAIRING_AGENT_DBUS_OBJECTPATH, "NoInputNoOutput")
        await self._agent_manager.call_request_default_agent(self._BLUEZ_PAIRING_AGENT_DBUS_OBJECTPATH)

        self._adapter = await self._dbus_interface(self._dbus, "/org/bluez/hci0", "org.freedesktop.DBus.Properties")
        await self._set_adapter_prop("Powered", True)
        await self._set_adapter_prop("Pairable", False)
        await self._set_adapter_prop("Discoverable", False)

        self._server = BlessServer(name="Drehbert", adapter="hci0")
        assert self._server is not None
        self._server.read_request_func = self._read_value
        self._server.write_request_func = self._write_value
        await self._server.add_gatt(self._GATT)
        await self._server.start()

    @staticmethod
    async def _dbus_interface[TProxy](dbus: MessageBus, path: str, name: str) -> TProxy:
        introspection = await dbus.introspect("org.bluez", path)
        proxy_object = dbus.get_proxy_object("org.bluez", path, introspection)
        proxy_interface = proxy_object.get_interface(name)
        return proxy_interface

    @staticmethod
    def _read_value(characteristic: BlessGATTCharacteristic) -> bytearray:
        return characteristic.value

    @staticmethod
    def _write_value(characteristic: BlessGATTCharacteristic, value: bytearray) -> None:
        characteristic.value = value

    async def _close(self) -> None:

        if self._server is not None:
            await self._server.stop()

        if self._adapter is not None:
            await self._set_adapter_prop("Discoverable", False)
            await self._set_adapter_prop("Pairable", False)

        if self._agent_manager is not None:
            await self._agent_manager.call_unregister_agent(self._BLUEZ_PAIRING_AGENT_DBUS_OBJECTPATH)

        if self._dbus is not None:
            self._dbus.unexport(self._BLUEZ_PAIRING_AGENT_DBUS_OBJECTPATH, self._bluez_pairing_agent)
            self._dbus.disconnect()

    async def enter_pairing_mode(self) -> None:
        await self._set_adapter_prop("Pairable", True)
        await self._set_adapter_prop("Discoverable", True)

    async def is_connected(self) -> bool:
        assert self._server is not None
        return await self._server.is_connected()

    async def capture_photo(self) -> None:

        assert self._server is not None

        report = self._server.get_characteristic(self.HID_SVC_REPORT_GUID)
        assert report is not None

        report.value = bytearray((1,))
        self._server.update_value(self.HID_SVC_GUID, self.HID_SVC_REPORT_GUID)

        await asyncio.sleep(self._key_press_seconds)

        report.value = bytearray((0,))
        self._server.update_value(self.HID_SVC_GUID, self.HID_SVC_REPORT_GUID)

    async def _set_adapter_prop(self, name: str, value: bool) -> None:
        assert self._adapter is not None
        await self._adapter.call_set("org.bluez.Adapter1", name, Variant("b", value))

    HID_SVC_GUID = "00001812-0000-1000-8000-00805f9b34fb"
    HID_SVC_INFORMATION_GUID = "00002a4a-0000-1000-8000-00805f9b34fb"
    HID_SVC_REPORT_MAP_GUID = "00002a4b-0000-1000-8000-00805f9b34fb"
    HID_SVC_CONTROL_POINT_GUID = "00002a4c-0000-1000-8000-00805f9b34fb"
    HID_SVC_REPORT_GUID = "00002a4d-0000-1000-8000-00805f9b34fb"
    HID_SVC_REPORT_REFERENCE_GUID = "00002908-0000-1000-8000-00805f9b34fb"

    _BLUEZ_PAIRING_AGENT_DBUS_OBJECTPATH = "/org/drehbert/pairing_agent"

    _GATT_CHAR_PROP_READ = GATTCharacteristicProperties.read
    # noinspection unsupported-operator
    _GATT_CHAR_PROP_READ_NOTIFY = GATTCharacteristicProperties.read | GATTCharacteristicProperties.notify
    _GATT_CHAR_PROP_WRITE_NO_RESPONSE = GATTCharacteristicProperties.write_without_response
    # noinspection unsupported-operator
    _GATT_ATT_PERM_READ_ENCRYPT = GATTAttributePermissions.readable | GATTAttributePermissions.read_encryption_required
    _GATT_ATT_PERM_WRITE = GATTAttributePermissions.writeable
    _GAT_DESC_PROP_READ = GATTDescriptorProperties.read

    _GATT_REPORT_MAP_VALUE = bytearray((
        # @formatter:off
        0x05, 0x0C,  # Usage Page (Consumer)
        0x09, 0x01,  # Usage (Consumer Control)
        0xA1, 0x01,  # Collection (Application)
        0x85, 0x01,  #     Report ID (1)
        0x15, 0x00,  #     Logical Minimum (0)
        0x25, 0x01,  #     Logical Maximum (1)
        0x75, 0x01,  #     Report Size (1)
        0x95, 0x01,  #     Report Count (1)
        0x09, 0xEA,  #     Usage (Volume Decrement / Shutter)
        0x81, 0x02,  #     Input (Data, Variable, Absolute)
        0x75, 0x07,  #     Report Size (padding of 7 bits)
        0x95, 0x01,  #     Report Count (1)
        0x81, 0x03,  #     Input (Constant, Variable, Absolute)
        0xC0,        # End Collection
        # @formatter:on
    ))

    _GATT = {
        HID_SVC_GUID: {
            HID_SVC_INFORMATION_GUID: {
                "Properties": _GATT_CHAR_PROP_READ,
                "Permissions": _GATT_ATT_PERM_READ_ENCRYPT,
                "Value": bytearray((0x11, 0x01, 0x00, 0x02)),
            },
            HID_SVC_REPORT_MAP_GUID: {
                "Properties": _GATT_CHAR_PROP_READ,
                "Permissions": _GATT_ATT_PERM_READ_ENCRYPT,
                "Value": _GATT_REPORT_MAP_VALUE.copy(),
            },
            HID_SVC_CONTROL_POINT_GUID: {
                "Properties": _GATT_CHAR_PROP_WRITE_NO_RESPONSE,
                "Permissions": _GATT_ATT_PERM_WRITE,
                "Value": bytearray((0,)),
            },
            HID_SVC_REPORT_GUID: {
                "Properties": _GATT_CHAR_PROP_READ_NOTIFY,
                "Permissions": _GATT_ATT_PERM_READ_ENCRYPT,
                "Value": bytearray((0,)),
                "Descriptors": {
                    HID_SVC_REPORT_REFERENCE_GUID: {
                        "Properties": _GAT_DESC_PROP_READ,
                        "Permissions": _GATT_ATT_PERM_READ_ENCRYPT,
                        "Value": bytearray((1, 1)),
                    }
                },
            },
        }
    }


# noinspection pep8-naming
class _BlueZAutoAcceptPairingAgent(ServiceInterface):
    def __init__(self) -> None:
        super().__init__("org.bluez.Agent1")

    @method()
    def Release(self):
        pass

    @method()
    def RequestConfirmation(self, device: _DBUS_OBJECT_PATH, passkey: _DBUS_UINT32):
        pass

    @method()
    def RequestAuthorization(self, device: _DBUS_OBJECT_PATH):
        pass

    @method()
    def AuthorizeService(self, device: _DBUS_OBJECT_PATH, uuid: str):
        pass

    @method()
    def Cancel(self):
        pass
