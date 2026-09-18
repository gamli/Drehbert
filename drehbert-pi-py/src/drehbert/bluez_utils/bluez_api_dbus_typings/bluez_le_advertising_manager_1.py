from typing import TYPE_CHECKING

from dbus_next import Variant
from dbus_next.aio import ProxyInterface

if TYPE_CHECKING:

    class BlueZLEAdvertisingManager1(ProxyInterface):

        async def call_register_advertisement(self, advertisement: str, options: dict[str, Variant]) -> None: ...

        async def call_unregister_advertisement(self, advertisement: str) -> None: ...

else:

    BlueZLEAdvertisingManager1 = ProxyInterface
