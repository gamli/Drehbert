import asyncio
from typing import cast

from dbus_next import Variant
from dbus_next.aio import MessageBus, ProxyInterface
from dbus_next.constants import BusType
from dbus_next.service import ServiceInterface

from drehbert.bluez_utils.bluez_api_dbus_typings.bluez_agent_manager_1 import BlueZAgentManager1
from drehbert.bluez_utils.bluez_api_dbus_typings.bluez_le_advertising_manager_1 import BlueZLEAdvertisingManager1
from drehbert.bluez_utils.bluez_api_dbus_typings.bluez_properties import BlueZProperties
from drehbert.bluez_utils.bluez_auto_accepting_pairing_agent_1 import BlueZAutoAcceptingPairingAgent1
from drehbert.bluez_utils.bluez_le_advertisement_1 import BluezLEAdvertisement1
from drehbert.bluez_utils.gatt.gatt_application import BluezGattApplication
from drehbert.bluez_utils.gatt.gatt_characteristic_1 import BluezGattCharacteristic1
from drehbert.bluez_utils.gatt.gatt_descriptor_1 import BluezGattDescriptor1
from drehbert.bluez_utils.gatt.gatt_manager_1 import BlueZGattManager1
from drehbert.bluez_utils.gatt.gatt_service_1 import BluezGattService1
from drehbert.drehbert_context_manager import DrehbertAsyncContextManager
from drehbert.optional_value import OptionalValue


class BluetoothCamera(DrehbertAsyncContextManager):

    _BLUEZ_SERVICE = "org.bluez"
    _BLUEZ_ADAPTER_PATH = "/org/bluez/hci0"
    _PAIRING_AGENT_PATH = "/org/drehbert/pairing_agent"
    _ADVERTISEMENT_PATH = "/org/drehbert/bluetooth_camera_advertisement"

    _HID_GENERIC_APPEARANCE = 0x03C0

    _HID_SVC_GUID = "00001812-0000-1000-8000-00805f9b34fb"
    _HID_SVC_INFORMATION_GUID = "00002a4a-0000-1000-8000-00805f9b34fb"
    _HID_SVC_REPORT_MAP_GUID = "00002a4b-0000-1000-8000-00805f9b34fb"
    _HID_SVC_CONTROL_POINT_GUID = "00002a4c-0000-1000-8000-00805f9b34fb"
    _HID_SVC_REPORT_GUID = "00002a4d-0000-1000-8000-00805f9b34fb"
    _HID_SVC_REPORT_REFERENCE_GUID = "00002908-0000-1000-8000-00805f9b34fb"
    _BATTERY_SVC_GUID = "0000180f-0000-1000-8000-00805f9b34fb"
    _BATTERY_LEVEL_GUID = "00002a19-0000-1000-8000-00805f9b34fb"
    _DEVICE_INFORMATION_SVC_GUID = "0000180a-0000-1000-8000-00805f9b34fb"
    _PNP_ID_GUID = "00002a50-0000-1000-8000-00805f9b34fb"

    _GATT_APPLICATION_PATH = "/org/drehbert/bluetooth_camera"
    _GATT_APPLICATION_NAME = "org.drehbert.GattApplication1"
    _GATT_SERVICE_PATH = f"{_GATT_APPLICATION_PATH}/service0"
    _GATT_INFORMATION_PATH = f"{_GATT_SERVICE_PATH}/char0"
    _GATT_REPORT_MAP_PATH = f"{_GATT_SERVICE_PATH}/char1"
    _GATT_CONTROL_POINT_PATH = f"{_GATT_SERVICE_PATH}/char2"
    _GATT_REPORT_PATH = f"{_GATT_SERVICE_PATH}/char3"
    _GATT_REPORT_REFERENCE_PATH = f"{_GATT_REPORT_PATH}/desc0"
    _BATTERY_SERVICE_PATH = f"{_GATT_APPLICATION_PATH}/service1"
    _BATTERY_LEVEL_PATH = f"{_BATTERY_SERVICE_PATH}/char0"
    _DEVICE_INFORMATION_SERVICE_PATH = f"{_GATT_APPLICATION_PATH}/service2"
    _PNP_ID_PATH = f"{_DEVICE_INFORMATION_SERVICE_PATH}/char0"
    # USB-IF source, unassigned vendor ID, product 1, version 1.
    _PNP_ID = bytes((0x02, 0x00, 0x00, 0x01, 0x00, 0x01, 0x00))

    _REPORT_MAP = bytes((
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

    def __init__(self, key_press_seconds: float = 0.05):
        super().__init__()
        self._key_press_seconds = key_press_seconds
        self._dbus = OptionalValue[MessageBus]()
        self._agent_manager = OptionalValue[BlueZAgentManager1]()
        self._adapter = OptionalValue[BlueZProperties]()
        self._gatt_manager = OptionalValue[BlueZGattManager1]()
        self._advertising_manager = OptionalValue[BlueZLEAdvertisingManager1]()
        self._report = OptionalValue[BluezGattCharacteristic1]()
        self._exported_interfaces: list[tuple[str, ServiceInterface]] = []
        self._agent_registered = False
        self._gatt_registered = False
        self._advertisement_registered = False

    async def _open(self) -> None:

        self._dbus(await MessageBus(bus_type=BusType.SYSTEM).connect())

        self._export_interface(self._PAIRING_AGENT_PATH, BlueZAutoAcceptingPairingAgent1())

        self._agent_manager(cast(
            BlueZAgentManager1,
            await self._dbus_interface("/org/bluez", "org.bluez.AgentManager1"),
        ))
        await self._agent_manager().call_register_agent(self._PAIRING_AGENT_PATH, "NoInputNoOutput")
        self._agent_registered = True
        await self._agent_manager().call_request_default_agent(self._PAIRING_AGENT_PATH)

        introspection = await self._dbus().introspect(self._BLUEZ_SERVICE, self._BLUEZ_ADAPTER_PATH)
        adapter = self._dbus().get_proxy_object(self._BLUEZ_SERVICE, self._BLUEZ_ADAPTER_PATH, introspection)
        self._adapter(cast(
            BlueZProperties,
            adapter.get_interface("org.freedesktop.DBus.Properties"),
        ))
        self._gatt_manager(cast(BlueZGattManager1, adapter.get_interface("org.bluez.GattManager1")))
        self._advertising_manager(
            cast(BlueZLEAdvertisingManager1, adapter.get_interface("org.bluez.LEAdvertisingManager1")))

        await self._set_adapter_property("Powered", Variant("b", True))
        await self._set_adapter_property("Pairable", Variant("b", False))
        await self._set_adapter_property("Discoverable", Variant("b", False))
        await self._set_adapter_property("Alias", Variant("s", "Drehbert"))

        self._export_gatt_application()
        await self._gatt_manager().call_register_application(self._GATT_APPLICATION_PATH, {})
        self._gatt_registered = True

        advertisement = BluezLEAdvertisement1(
            "peripheral",
            "Drehbert",
            self._HID_SVC_GUID,
            self._HID_GENERIC_APPEARANCE,
        )
        self._export_interface(self._ADVERTISEMENT_PATH, advertisement)
        await self._advertising_manager().call_register_advertisement(self._ADVERTISEMENT_PATH, {})
        self._advertisement_registered = True

    async def _close(self) -> None:
        if self._advertisement_registered:
            assert self._advertising_manager is not None
            await self._advertising_manager().call_unregister_advertisement(self._ADVERTISEMENT_PATH)
            self._advertisement_registered = False

        if self._gatt_registered:
            assert self._gatt_manager is not None
            await self._gatt_manager().call_unregister_application(self._GATT_APPLICATION_PATH)
            self._gatt_registered = False

        if self._adapter is not None:
            await self._set_adapter_property("Discoverable", Variant("b", False))
            await self._set_adapter_property("Pairable", Variant("b", False))

        if self._agent_registered:
            assert self._agent_manager is not None
            await self._agent_manager().call_unregister_agent(self._PAIRING_AGENT_PATH)
            self._agent_registered = False

        if self._dbus is not None:
            for path, interface in reversed(self._exported_interfaces):
                self._dbus().unexport(path, interface)

            self._dbus().disconnect()

        self._exported_interfaces.clear()
        self._report = None
        self._advertising_manager = None
        self._gatt_manager = None
        self._adapter = None
        self._agent_manager = None
        self._dbus = None

    async def enter_pairing_mode(self) -> None:
        await self._set_adapter_property("Pairable", Variant("b", True))
        await self._set_adapter_property("Discoverable", Variant("b", True))

    async def is_connected(self) -> bool:
        assert self._report is not None
        return self._report().is_notifying

    async def capture_photo(self) -> None:
        assert self._report is not None

        self._report().set_value(b"\x01")
        try:
            await asyncio.sleep(self._key_press_seconds)
        finally:
            self._report().set_value(b"\x00")

    async def _set_adapter_property(self, name: str, value: Variant) -> None:
        assert self._adapter is not None
        await self._adapter().call_set("org.bluez.Adapter1", name, value)

    async def _dbus_interface(self, path: str, name: str) -> ProxyInterface:
        assert self._dbus is not None
        introspection = await self._dbus().introspect(self._BLUEZ_SERVICE, path)
        proxy_object = self._dbus().get_proxy_object(self._BLUEZ_SERVICE, path, introspection)
        return proxy_object.get_interface(name)

    def _export_interface(self, path: str, interface: ServiceInterface) -> None:
        assert self._dbus is not None
        self._dbus().export(path, interface)
        self._exported_interfaces.append((path, interface))

    def _export_gatt_application(self) -> None:
        self._export_interface(self._GATT_APPLICATION_PATH, BluezGattApplication(self._GATT_APPLICATION_NAME))
        self._export_interface(self._GATT_SERVICE_PATH, BluezGattService1(self._HID_SVC_GUID))

        self._export_interface(self._GATT_INFORMATION_PATH, BluezGattCharacteristic1(
            self._HID_SVC_INFORMATION_GUID,
            self._GATT_SERVICE_PATH,
            ["read", "encrypt-read"],
            bytes((0x11, 0x01, 0x00, 0x02)),
        ))
        self._export_interface(self._GATT_REPORT_MAP_PATH, BluezGattCharacteristic1(
            self._HID_SVC_REPORT_MAP_GUID,
            self._GATT_SERVICE_PATH,
            ["read", "encrypt-read"],
            self._REPORT_MAP,
        ))
        self._export_interface(self._GATT_CONTROL_POINT_PATH, BluezGattCharacteristic1(
            self._HID_SVC_CONTROL_POINT_GUID,
            self._GATT_SERVICE_PATH,
            ["write-without-response", "encrypt-write"],
            b"\x00",
        ))

        self._report(BluezGattCharacteristic1(
            self._HID_SVC_REPORT_GUID,
            self._GATT_SERVICE_PATH,
            ["read", "notify", "encrypt-read"],
            b"\x00",
        ))
        self._export_interface(self._GATT_REPORT_PATH, self._report())
        self._export_interface(self._GATT_REPORT_REFERENCE_PATH, BluezGattDescriptor1(
            self._HID_SVC_REPORT_REFERENCE_GUID,
            self._GATT_REPORT_PATH,
            ["read", "encrypt-read"],
            bytes((1, 1)),
        ))

        self._export_interface(self._BATTERY_SERVICE_PATH, BluezGattService1(self._BATTERY_SVC_GUID))
        self._export_interface(self._BATTERY_LEVEL_PATH, BluezGattCharacteristic1(
            self._BATTERY_LEVEL_GUID,
            self._BATTERY_SERVICE_PATH,
            ["read"],
            bytes((100,)),
        ))

        self._export_interface(
            self._DEVICE_INFORMATION_SERVICE_PATH,
            BluezGattService1(self._DEVICE_INFORMATION_SVC_GUID),
        )
        self._export_interface(self._PNP_ID_PATH, BluezGattCharacteristic1(
            self._PNP_ID_GUID,
            self._DEVICE_INFORMATION_SERVICE_PATH,
            ["read"],
            self._PNP_ID,
        ))

# from typing import cast
#
# from dbus_next import Variant
# from dbus_next.aio import MessageBus, ProxyInterface
# from dbus_next.service import ServiceInterface
#
# from bluez_auto_accepting_pairing_agent import BlueZAutoAcceptingPairingAgent
# from bluez_le_advertisement_1 import BluezLEAdvertisement1
# from drehbert.bluez_utils.bluez_api_dbus_typings.bluez_agent_manager_1 import BlueZAgentManager1
# from drehbert.bluez_utils.bluez_api_dbus_typings.bluez_le_advertising_manager_1 import BlueZLEAdvertisingManager1
# from drehbert.bluez_utils.bluez_api_dbus_typings.bluez_properties import BlueZProperties
# from drehbert.bluez_utils.drehbert_hogp_manager import BlueZHOGPManager
# from drehbert.drehbert_context_manager import DrehbertAsyncContextManager
# from drehbert.optional_value import OptionalValue
#
#
# class DrehbertCameraTriggerManager(DrehbertAsyncContextManager):
#
#     _BLUEZ_SERVICE = "org.bluez"
#     _BLUEZ_ADAPTER_PATH = "/org/bluez/hci0"
#     _PAIRING_AGENT_PATH = "/org/drehbert/pairing_agent"
#     _ADVERTISEMENT_PATH = "/org/drehbert/bluetooth_camera_advertisement"
#
#     _HID_GENERIC_APPEARANCE = 0x03C0
#
#     _HID_SVC_GUID = "00001812-0000-1000-8000-00805f9b34fb"
#     _HID_SVC_INFORMATION_GUID = "00002a4a-0000-1000-8000-00805f9b34fb"
#     _HID_SVC_REPORT_MAP_GUID = "00002a4b-0000-1000-8000-00805f9b34fb"
#     _HID_SVC_CONTROL_POINT_GUID = "00002a4c-0000-1000-8000-00805f9b34fb"
#     _HID_SVC_REPORT_GUID = "00002a4d-0000-1000-8000-00805f9b34fb"
#     _HID_SVC_REPORT_REFERENCE_GUID = "00002908-0000-1000-8000-00805f9b34fb"
#     _BATTERY_SVC_GUID = "0000180f-0000-1000-8000-00805f9b34fb"
#     _BATTERY_LEVEL_GUID = "00002a19-0000-1000-8000-00805f9b34fb"
#     _DEVICE_INFORMATION_SVC_GUID = "0000180a-0000-1000-8000-00805f9b34fb"
#     _PNP_ID_GUID = "00002a50-0000-1000-8000-00805f9b34fb"
#
#     _GATT_APPLICATION_PATH = "/org/drehbert/bluetooth_camera"
#     _GATT_APPLICATION_NAME = "org.drehbert.GattApplication1"
#     _GATT_SERVICE_PATH = f"{_GATT_APPLICATION_PATH}/service0"
#     _GATT_INFORMATION_PATH = f"{_GATT_SERVICE_PATH}/char0"
#     _GATT_REPORT_MAP_PATH = f"{_GATT_SERVICE_PATH}/char1"
#     _GATT_CONTROL_POINT_PATH = f"{_GATT_SERVICE_PATH}/char2"
#     _GATT_REPORT_PATH = f"{_GATT_SERVICE_PATH}/char3"
#     _GATT_REPORT_REFERENCE_PATH = f"{_GATT_REPORT_PATH}/desc0"
#     _BATTERY_SERVICE_PATH = f"{_GATT_APPLICATION_PATH}/service1"
#     _BATTERY_LEVEL_PATH = f"{_BATTERY_SERVICE_PATH}/char0"
#     _DEVICE_INFORMATION_SERVICE_PATH = f"{_GATT_APPLICATION_PATH}/service2"
#     _PNP_ID_PATH = f"{_DEVICE_INFORMATION_SERVICE_PATH}/char0"
#     # USB-IF source, unassigned vendor ID, product 1, version 1.
#     _PNP_ID = bytes((0x02, 0x00, 0x00, 0x01, 0x00, 0x01, 0x00))
#
#     _REPORT_MAP = bytes((
#         # @formatter:off
#         0x05, 0x0C,  # Usage Page (Consumer)
#         0x09, 0x01,  # Usage (Consumer Control)
#         0xA1, 0x01,  # Collection (Application)
#         0x85, 0x01,  #     Report ID (1)
#         0x15, 0x00,  #     Logical Minimum (0)
#         0x25, 0x01,  #     Logical Maximum (1)
#         0x75, 0x01,  #     Report Size (1)
#         0x95, 0x01,  #     Report Count (1)
#         0x09, 0xEA,  #     Usage (Volume Decrement / Shutter)
#         0x81, 0x02,  #     Input (Data, Variable, Absolute)
#         0x75, 0x07,  #     Report Size (padding of 7 bits)
#         0x95, 0x01,  #     Report Count (1)
#         0x81, 0x03,  #     Input (Constant, Variable, Absolute)
#         0xC0,        # End Collection
#         # @formatter:on
#     ))
#
#     def __init__(self, dbus: MessageBus):
#         super().__init__()
#
#         self._dbus = dbus
#
#         self._agent_manager = OptionalValue[BlueZAgentManager1]()
#         self._adapter = OptionalValue[BlueZProperties]()
#         self._advertising_manager = OptionalValue[BlueZLEAdvertisingManager1]()
#
#         self._bluez_hogp_manager = BlueZHOGPManager(self._GATT_APPLICATION_PATH, self._adapter, dbus)
#
#         self._exported_interfaces: list[tuple[str, ServiceInterface]] = []
#
#     async def _open(self) -> None:
#
#         self._export_interface(self._PAIRING_AGENT_PATH, BlueZAutoAcceptingPairingAgent())
#
#         self._agent_manager(cast(
#             BlueZAgentManager1,
#             await self._dbus_interface("/org/bluez", "org.bluez.AgentManager1"),
#         ))
#         await self._agent_manager().call_register_agent(self._PAIRING_AGENT_PATH, "NoInputNoOutput")
#         self._agent_registered = True
#         await self._agent_manager().call_request_default_agent(self._PAIRING_AGENT_PATH)
#
#         introspection = await self._dbus.introspect(self._BLUEZ_SERVICE, self._BLUEZ_ADAPTER_PATH)
#         adapter = self._dbus.get_proxy_object(self._BLUEZ_SERVICE, self._BLUEZ_ADAPTER_PATH, introspection)
#         self._adapter(cast(
#             BlueZProperties,
#             adapter.get_interface("org.freedesktop.DBus.Properties"),
#         ))
#
#
#         self._gatt_manager(Gat)
#
#         self._advertising_manager(
#             cast(BlueZLEAdvertisingManager1, adapter.get_interface("org.bluez.LEAdvertisingManager1")))
#
#         await self._set_adapter_property("Powered", Variant("b", True))
#         await self._set_adapter_property("Pairable", Variant("b", False))
#         await self._set_adapter_property("Discoverable", Variant("b", False))
#         await self._set_adapter_property("Alias", Variant("s", "Drehbert"))
#
#         self._export_gatt_application()
#         await self._gatt_manager().call_register_application(self._GATT_APPLICATION_PATH, {})
#         self._gatt_registered = True
#
#         advertisement = BluezLEAdvertisement1(
#             "peripheral",
#             "Drehbert",
#             self._HID_SVC_GUID,
#             self._HID_GENERIC_APPEARANCE,
#         )
#         self._export_interface(self._ADVERTISEMENT_PATH, advertisement)
#         await self._advertising_manager().call_register_advertisement(self._ADVERTISEMENT_PATH, {})
#         self._advertisement_registered = True
#
#     async def _close(self) -> None:
#         if self._advertisement_registered:
#             assert self._advertising_manager is not None
#             await self._advertising_manager().call_unregister_advertisement(self._ADVERTISEMENT_PATH)
#             self._advertisement_registered = False
#
#         if self._gatt_registered:
#             assert self._gatt_manager is not None
#             await self._gatt_manager().call_unregister_application(self._GATT_APPLICATION_PATH)
#             self._gatt_registered = False
#
#         if self._adapter is not None:
#             await self._set_adapter_property("Discoverable", Variant("b", False))
#             await self._set_adapter_property("Pairable", Variant("b", False))
#
#         if self._agent_registered:
#             assert self._agent_manager is not None
#             await self._agent_manager().call_unregister_agent(self._PAIRING_AGENT_PATH)
#             self._agent_registered = False
#
#         if self._dbus is not None:
#             for path, interface in reversed(self._exported_interfaces):
#                 self._dbus.unexport(path, interface)
#
#             self._dbus.disconnect()
#
#         self._exported_interfaces.clear()
#         self._report = None
#         self._advertising_manager = None
#         self._gatt_manager = None
#         self._adapter = None
#         self._agent_manager = None
#         self._dbus = None
#
#     async def enter_pairing_mode(self) -> None:
#         await self._set_adapter_property("Pairable", Variant("b", True))
#         await self._set_adapter_property("Discoverable", Variant("b", True))
#
#     async def is_connected(self) -> bool:
#         assert self._report is not None
#         return self._report().is_notifying
#
#     async def _set_adapter_property(self, name: str, value: Variant) -> None:
#         assert self._adapter is not None
#         await self._adapter().call_set("org.bluez.Adapter1", name, value)
#
#     async def _dbus_interface(self, path: str, name: str) -> ProxyInterface:
#         assert self._dbus is not None
#         introspection = await self._dbus.introspect(self._BLUEZ_SERVICE, path)
#         proxy_object = self._dbus.get_proxy_object(self._BLUEZ_SERVICE, path, introspection)
#         return proxy_object.get_interface(name)
#
#     def _export_interface(self, path: str, interface: ServiceInterface) -> None:
#         assert self._dbus is not None
#         self._dbus.export(path, interface)
#         self._exported_interfaces.append((path, interface))
#
#
