from configs import dify_config
from core.plugin.impl.base import BasePluginClient
from core.plugin.impl.nacos_client import NacosPluginClient

BaseClient = NacosPluginClient if dify_config.PLUGIN_REGISTRY_MODE == "nacos" else BasePluginClient

class PluginAssetManager(BaseClient):
    def fetch_asset(self, tenant_id: str, id: str) -> bytes:
        """
        Fetch an asset by id.
        """
        response = self._request(method="GET", path=f"plugin/{tenant_id}/asset/{id}")
        if response.status_code != 200:
            raise ValueError(f"can not found asset {id}")
        return response.content
