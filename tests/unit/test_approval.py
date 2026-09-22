import sys
import os
import asyncio
import tempfile
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "api"))

os.environ["AIOPS_DB_PATH"] = tempfile.mktemp(suffix=".db")
os.environ["APPROVAL_SIGNING_SECRET"] = "test-secret-key"
os.environ["APPROVAL_TTL_SECONDS"] = "300"

from app.db import init_db
from app.services.approval_service import create_approval, validate_approval, mark_token_used, generate_token


async def setup():
    await init_db()


def test_generate_token_format():
    token = generate_token("INC-TEST-001", "fix_gateway_upstream")
    assert token.startswith("APP-")


def test_valid_approval():
    async def run():
        await setup()
        approval = await create_approval("INC-TEST-001", "fix_gateway_upstream", "Test Operator")
        result = await validate_approval("INC-TEST-001", "fix_gateway_upstream", approval["token"])
        assert result["valid"]
    asyncio.run(run())


def test_wrong_incident():
    async def run():
        await setup()
        approval = await create_approval("INC-TEST-002", "fix_gateway_upstream", "Test Operator")
        result = await validate_approval("INC-TEST-999", "fix_gateway_upstream", approval["token"])
        assert not result["valid"]
    asyncio.run(run())


def test_wrong_action():
    async def run():
        await setup()
        approval = await create_approval("INC-TEST-003", "fix_gateway_upstream", "Test Operator")
        result = await validate_approval("INC-TEST-003", "wrong_action", approval["token"])
        assert not result["valid"]
    asyncio.run(run())


def test_fake_token():
    async def run():
        await setup()
        result = await validate_approval("INC-TEST-004", "fix_gateway_upstream", "APP-FAKE-TOKEN")
        assert not result["valid"]
    asyncio.run(run())


def test_token_reuse():
    async def run():
        await setup()
        approval = await create_approval("INC-TEST-005", "fix_gateway_upstream", "Test Operator")
        await mark_token_used("INC-TEST-005", approval["token"])
        result = await validate_approval("INC-TEST-005", "fix_gateway_upstream", approval["token"])
        assert not result["valid"]
        assert result["error"] == "TOKEN_ALREADY_USED"
    asyncio.run(run())


def test_expired_token():
    async def run():
        await setup()
        os.environ["APPROVAL_TTL_SECONDS"] = "0"
        approval = await create_approval("INC-TEST-006", "fix_gateway_upstream", "Test Operator")
        import time
        time.sleep(1)
        result = await validate_approval("INC-TEST-006", "fix_gateway_upstream", approval["token"])
        assert not result["valid"]
        assert result["error"] == "APPROVAL_EXPIRED"
        os.environ["APPROVAL_TTL_SECONDS"] = "300"
    asyncio.run(run())
