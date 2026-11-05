import asyncio

import pytest
from pydantic import SecretStr

from app.services.github import GitHubService, validate_repo_slug


def test_valid_repo_slug():
    assert validate_repo_slug("hendy-video-studio") == "hendy-video-studio"


@pytest.mark.parametrize("bad", ["", "../secrets", "..", "bad/name", "has spaces"])
def test_invalid_repo_slug(bad):
    with pytest.raises(ValueError):
        validate_repo_slug(bad)


def test_github_service_rejects_path_traversal_before_api_call():
    class DummySettings:
        github_org = "hendy-server-AI-hub"
        github_token = SecretStr("test-token")

    service = GitHubService(client=None, settings=DummySettings())
    with pytest.raises(ValueError):
        asyncio.run(service.read_file("hendy-video-studio", "../.env"))
