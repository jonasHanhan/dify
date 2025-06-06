import json
import importlib
from types import SimpleNamespace

import requests
from core.plugin.impl import nacos_client
from configs import dify_config


def test_nacos_service_discovery_and_request(monkeypatch):
    dify_config.PLUGIN_REGISTRY_MODE = "nacos"
    monkeypatch.setattr(dify_config, "NACOS_PLUGIN_SERVER_ADDR", "nacos:8848", raising=False)
    monkeypatch.setattr(dify_config, "NACOS_PLUGIN_SERVICE_NAME", "plugin-daemon", raising=False)

    def mock_http_request(self, url, method="GET", headers=None, params=None):
        assert params["serviceName"] == "plugin-daemon"
        return json.dumps({"hosts": [{"ip": "127.0.0.1", "port": 5002}]})

    monkeypatch.setattr(nacos_client.NacosHttpClient, "http_request", mock_http_request)

    called = {}
    def mock_request(method, url, **kwargs):
        called["url"] = url
        response = requests.Response()
        response.status_code = 200
        response._content = b"{}"
        return response

    monkeypatch.setattr(requests, "request", mock_request)

    importlib.reload(nacos_client)
    client = nacos_client.NacosPluginClient()
    client._request("GET", "ping")
    assert called["url"].startswith("http://127.0.0.1:5002/ping")
