import json
import logging
import time
from typing import Optional

import requests
from yarl import URL

from configs import dify_config
from configs.remote_settings_sources.nacos.http_request import NacosHttpClient
from core.plugin.impl.base import BasePluginClient
from core.plugin.entities.plugin_daemon import PluginDaemonInnerError

logger = logging.getLogger(__name__)


class NacosDiscovery:
    def __init__(self) -> None:
        self.client = NacosHttpClient()
        self.namespace = dify_config.NACOS_PLUGIN_NAMESPACE or ""
        self.group = dify_config.NACOS_PLUGIN_GROUP or "DEFAULT_GROUP"
        self.service_name = dify_config.NACOS_PLUGIN_SERVICE_NAME
        self._cache_url: Optional[str] = None
        self._cache_time = 0.0
        self._cache_ttl = 30

    def get_service_url(self) -> str:
        now = time.time()
        if self._cache_url and now - self._cache_time < self._cache_ttl:
            return self._cache_url

        params = {
            "serviceName": self.service_name,
            "groupName": self.group,
            "namespaceId": self.namespace,
        }
        try:
            resp = self.client.http_request(
                "/nacos/v1/ns/instance/list", method="GET", headers={}, params=params
            )
            data = json.loads(resp)
            hosts = data.get("hosts", [])
            if not hosts:
                raise ValueError("no available service instance")
            host = hosts[0]
            url = f"http://{host['ip']}:{host['port']}"
        except Exception as e:  # pragma: no cover - network issues
            logger.exception("Failed to discover plugin daemon from nacos")
            raise RuntimeError("nacos discovery failed") from e

        self._cache_url = url
        self._cache_time = now
        return url


class NacosPluginClient(BasePluginClient):
    def __init__(self) -> None:
        super().__init__()
        self.discovery = NacosDiscovery()

    def _request(
        self,
        method: str,
        path: str,
        headers: dict | None = None,
        data: bytes | dict | str | None = None,
        params: dict | None = None,
        files: dict | None = None,
        stream: bool = False,
    ) -> requests.Response:
        url = URL(self.discovery.get_service_url()) / path
        headers = headers or {}
        headers["X-Api-Key"] = dify_config.PLUGIN_DAEMON_KEY
        headers["Accept-Encoding"] = "gzip, deflate, br"

        if headers.get("Content-Type") == "application/json" and isinstance(data, dict):
            data = json.dumps(data)

        try:
            response = requests.request(
                method=method,
                url=str(url),
                headers=headers,
                data=data,
                params=params,
                stream=stream,
                files=files,
            )
        except requests.exceptions.ConnectionError:
            logger.exception("Request to Plugin Daemon Service failed")
            raise PluginDaemonInnerError(code=-500, message="Request to Plugin Daemon Service failed")

        return response
