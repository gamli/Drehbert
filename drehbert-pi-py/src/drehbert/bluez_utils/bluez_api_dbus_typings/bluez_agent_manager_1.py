from typing import TYPE_CHECKING

from dbus_next.aio import ProxyInterface

if TYPE_CHECKING:

    class BlueZAgentManager1(ProxyInterface):

        async def call_register_agent(self, agent_path: str, capability: str) -> None: ...

        async def call_unregister_agent(self, agent_path: str) -> None: ...

        async def call_request_default_agent(self, agent_path: str) -> None: ...

else:

    BlueZAgentManager1 = ProxyInterface
