import pytest


@pytest.mark.integration
def test_fix_without_token_denied():
    pass


@pytest.mark.integration
def test_fake_token_denied():
    pass


@pytest.mark.integration
def test_expired_token_denied():
    pass


@pytest.mark.integration
def test_valid_token_allowed():
    pass
