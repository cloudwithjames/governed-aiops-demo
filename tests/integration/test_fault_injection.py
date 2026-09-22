import pytest
import httpx


@pytest.mark.integration
def test_portal_healthy_before_inject():
    pass


@pytest.mark.integration
def test_portal_502_after_inject():
    pass


@pytest.mark.integration
def test_backend_stays_healthy():
    pass
