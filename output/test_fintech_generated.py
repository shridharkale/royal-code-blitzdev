"""
Auto-generated integration tests by BlitzDev — FinTech Transactional Security.
Deterministic verification for concurrency, atomicity, and idempotency boundaries.
"""
import pytest
import asyncio
import uuid
import httpx
from httpx import ASGITransport

from demo_api.main import app
from demo_api.seed import seed

@pytest.mark.asyncio
async def test_race_condition_concurrent_withdrawals():
    """FIN-002: Verify 5 concurrent withdrawals of $30 on a $100 balance."""
    await seed()
    async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        tasks = [
            client.post(
                "/accounts/1/withdraw",
                json={"amount": 30.0, "idempotency_key": f"tx_{i}_{uuid.uuid4().hex[:6]}"},
            )
            for i in range(5)
        ]
        responses = await asyncio.gather(*tasks)

        successful_withdrawals = [r for r in responses if r.status_code == 200]
        failed_withdrawals = [r for r in responses if r.status_code == 400]

        balance_resp = await client.get("/accounts/1/balance")
        final_balance = balance_resp.json()["balance"]

        print(f"\n[CONCURRENCY RESULT] Success: {len(successful_withdrawals)}, Rejected: {len(failed_withdrawals)}, Final: ${final_balance}")
        assert len(successful_withdrawals) == 3, f"Expected 3 successes, got {len(successful_withdrawals)}"
        assert len(failed_withdrawals) == 2, f"Expected 2 rejections, got {len(failed_withdrawals)}"
        assert final_balance == 10.0, f"Expected $10.0 balance, got ${final_balance}"

@pytest.mark.asyncio
async def test_transfer_non_atomic_failure_rollback():
    """FIN-003: Transfer failure to non-existent recipient must rollback source debit."""
    await seed()
    async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        transfer_resp = await client.post(
            "/accounts/transfer",
            json={"from_account_id": 1, "to_account_id": 99999, "amount": 50.0},
        )
        assert transfer_resp.status_code == 404

        balance_resp = await client.get("/accounts/1/balance")
        assert balance_resp.json()["balance"] == 100.0, "Source account balance corrupted on failed transfer!"

@pytest.mark.asyncio
async def test_idempotency_key_enforcement():
    """FIN-004: Duplicate requests with same idempotency key must not double-process."""
    await seed()
    async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        key = f"key_{uuid.uuid4().hex}"
        payload = {"amount": 25.0, "idempotency_key": key}

        r1 = await client.post("/accounts/1/withdraw", json=payload)
        r2 = await client.post("/accounts/1/withdraw", json=payload)

        assert r1.status_code == 200
        assert r2.status_code == 200
        assert "already processed" in r2.json()["message"]

        balance_resp = await client.get("/accounts/1/balance")
        assert balance_resp.json()["balance"] == 75.0, "Idempotency failed: withdrawal processed twice!"
