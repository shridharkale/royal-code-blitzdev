import pytest
import asyncio
import httpx
from demo_api.main import app
from demo_api.seed import seed
from demo_api.database import async_session
from demo_api.models import Account
from sqlalchemy import select

@pytest.mark.asyncio
async def test_remediated_concurrent_withdrawals():
    # 1. Deterministic database seed (Account 1 starts with $100.00)
    await seed()

    # 2. Fire 5 distinct concurrent withdrawal requests ($30.00 each = $150 total demand on $100 balance)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        tasks = [
            client.post("/accounts/1/withdraw", json={"amount": 30.0, "idempotency_key": f"distinct_tx_{i}"})
            for i in range(5)
        ]
        responses = await asyncio.gather(*tasks)

    # 3. Aggregate response status codes
    status_codes = [r.status_code for r in responses]
    successful_withdrawals = status_codes.count(200)
    failed_withdrawals = status_codes.count(400)

    # 4. Check final ledger balance directly from database
    async with async_session() as session:
        result = await session.execute(select(Account).where(Account.id == 1))
        account = result.scalar_one()
        final_balance = float(account.balance)

    print("\n" + "=" * 60)
    print("REMEDIATED CONCURRENCY TEST EXECUTION RESULTS:")
    print("=" * 60)
    print(f"Total Requests Dispatched: 5 (Each requesting $30.00)")
    print(f"Initial Starting Balance:  $100.00")
    print(f"Successful Requests (200): {successful_withdrawals}")
    print(f"Rejected Requests   (400): {failed_withdrawals}")
    print(f"Final Balance in Database: ${final_balance:.2f}")
    print("=" * 60)
    print("✅ LEDGER INTEGRITY VERIFIED (FIN-002 REMEDIATED):")
    print("   Race condition eliminated: Exactly 3 withdrawals succeeded, 2 rejected.")
    print("   Overdraft prevented: Final balance never dipped below zero.")
    print("=" * 60)

    # Strict financial integrity assertions
    assert successful_withdrawals == 3, f"Expected exactly 3 successes, got {successful_withdrawals}"
    assert failed_withdrawals == 2, f"Expected exactly 2 rejections (HTTP 400), got {failed_withdrawals}"
    assert final_balance == 10.0, f"Expected final balance to be $10.00, got ${final_balance}"

@pytest.mark.asyncio
async def test_idempotency_replay_protection():
    """Verify FIN-004: Network replay with identical key must never double debit."""
    await seed()
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        # Initial request
        res1 = await client.post("/accounts/1/withdraw", json={"amount": 25.0, "idempotency_key": "unique_idem_key_101"})
        assert res1.status_code == 200

        # Duplicate replay
        res2 = await client.post("/accounts/1/withdraw", json={"amount": 25.0, "idempotency_key": "unique_idem_key_101"})
        assert res2.status_code == 200
        assert "already processed" in res2.json()["message"]

    async with async_session() as session:
        result = await session.execute(select(Account).where(Account.id == 1))
        account = result.scalar_one()
        # Initial was 100.00, should only be debited ONCE to 75.00
        assert float(account.balance) == 75.0, f"Expected $75.00, got ${account.balance}"
        print("\n✅ IDEMPOTENCY REPLAY PROTECTION VERIFIED (FIN-004 REMEDIATED): Replay safely ignored.")
