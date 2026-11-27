import pytest

from services.open_router.tests.mock import MockOpenRouter


@pytest.fixture(autouse=True)
def _static_root(settings, tmp_path):
    """Keep test runs away from the collected static files."""
    settings.STATIC_ROOT = tmp_path


@pytest.fixture
def upstream(monkeypatch: pytest.MonkeyPatch) -> MockOpenRouter:
    """Swap OpenRouter for a mock."""
    return MockOpenRouter(monkeypatch=monkeypatch)
