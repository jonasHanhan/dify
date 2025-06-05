from pydantic import BaseModel

from configs import dify_config
from core.plugin.impl.base import BasePluginClient
from core.plugin.impl.nacos_client import NacosPluginClient

BaseClient = NacosPluginClient if dify_config.PLUGIN_REGISTRY_MODE == "nacos" else BasePluginClient


class PluginDebuggingClient(BaseClient):
    def get_debugging_key(self, tenant_id: str) -> str:
        """
        Get the debugging key for the given tenant.
        """

        class Response(BaseModel):
            key: str

        response = self._request_with_plugin_daemon_response("POST", f"plugin/{tenant_id}/debugging/key", Response)

        return response.key
