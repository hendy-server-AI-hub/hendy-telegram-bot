import pytest

from app.services.platform import HendyPlatformClient


class DummySession:
    pass


def test_platform_client_accepts_only_https_and_strong_token():
    client = HendyPlatformClient("https://platform.example.com", "x" * 40, timeout_seconds=5)
    assert client.base_url == "https://platform.example.com"
    assert client.RESOURCES == frozenset({"status", "jobs", "orders", "metrics"})


@pytest.mark.parametrize(
    "url",
    [
        "http://platform.example.com",
        "https://user:pass@platform.example.com",
        "https://platform.example.com?token=bad",
        "https://platform.example.com/#fragment",
        "https:///missing-host",
    ],
)
def test_platform_client_rejects_unsafe_urls(url):
    with pytest.raises(ValueError):
        HendyPlatformClient(url, "x" * 40, timeout_seconds=5)


def test_platform_client_rejects_short_token():
    with pytest.raises(ValueError):
        HendyPlatformClient("https://platform.example.com", "short")
