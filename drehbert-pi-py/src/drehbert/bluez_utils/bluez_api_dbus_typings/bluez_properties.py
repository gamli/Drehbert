from typing import TYPE_CHECKING

from dbus_next import Variant
from dbus_next.aio import ProxyInterface

if TYPE_CHECKING:

    class BlueZProperties(ProxyInterface):

        async def call_set(self, interface: str, name: str, value: Variant) -> None: ...

else:

    BlueZProperties = ProxyInterface
