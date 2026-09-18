from typing import TYPE_CHECKING

from dbus_next import Variant
from dbus_next.aio import ProxyInterface

if TYPE_CHECKING:

    class BlueZGattManager1(ProxyInterface):

        async def call_register_application(self, application: str, options: dict[str, Variant]) -> None: ...

        async def call_unregister_application(self, application: str) -> None: ...

else:

    BlueZGattManager1 = ProxyInterface
