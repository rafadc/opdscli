import httpx
import pytest
import respx

from opdscli.config import AuthConfig, CatalogConfig
from opdscli.http import OPDSClientError, create_client, fetch_url


class TestCreateClient:
    def test_no_auth(self):
        cat = CatalogConfig(url="https://example.com/opds")
        client = create_client(cat)
        assert isinstance(client, httpx.Client)

    def test_basic_auth(self):
        cat = CatalogConfig(
            url="https://example.com/opds",
            auth=AuthConfig(type="basic", username="user", password="pass"),
        )
        client = create_client(cat)
        assert client.auth is not None

    def test_bearer_auth(self):
        cat = CatalogConfig(
            url="https://example.com/opds",
            auth=AuthConfig(type="bearer", token="mytoken"),
        )
        client = create_client(cat)
        assert "Authorization" in client.headers
        assert client.headers["Authorization"] == "Bearer mytoken"


class TestFetchUrl:
    @respx.mock
    def test_successful_fetch(self):
        respx.get("https://example.com/feed").mock(
            return_value=httpx.Response(200, text="<feed/>")
        )
        client = httpx.Client()
        result = fetch_url(client, "https://example.com/feed")
        assert result == "<feed/>"

    @respx.mock
    def test_auth_failure_401(self):
        respx.get("https://example.com/feed").mock(
            return_value=httpx.Response(401)
        )
        client = httpx.Client()
        with pytest.raises(OPDSClientError, match="Authentication failed"):
            fetch_url(client, "https://example.com/feed")

    @respx.mock
    def test_auth_failure_403(self):
        respx.get("https://example.com/feed").mock(
            return_value=httpx.Response(403)
        )
        client = httpx.Client()
        with pytest.raises(OPDSClientError, match="Authentication failed"):
            fetch_url(client, "https://example.com/feed")

    @respx.mock
    def test_http_error(self):
        respx.get("https://example.com/feed").mock(
            return_value=httpx.Response(500)
        )
        client = httpx.Client()
        with pytest.raises(OPDSClientError, match="HTTP error 500"):
            fetch_url(client, "https://example.com/feed")

    @respx.mock
    def test_retry_on_network_error(self):
        route = respx.get("https://example.com/feed")
        route.side_effect = [
            httpx.ConnectError("connection failed"),
            httpx.Response(200, text="<feed/>"),
        ]
        client = httpx.Client()
        result = fetch_url(client, "https://example.com/feed")
        assert result == "<feed/>"
        assert route.call_count == 2

    @respx.mock
    def test_fail_after_retry_exhausted(self):
        respx.get("https://example.com/feed").mock(
            side_effect=httpx.ConnectError("connection failed")
        )
        client = httpx.Client()
        with pytest.raises(OPDSClientError, match="Network error after retry"):
            fetch_url(client, "https://example.com/feed")
