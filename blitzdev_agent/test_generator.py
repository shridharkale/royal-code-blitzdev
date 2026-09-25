"""
BlitzDev Test Generator — Automated Exploit Test Creation
==========================================================
Generates pytest-asyncio integration tests that expose race conditions
and financial logic bugs found during analysis.
"""
import textwrap
from pathlib import Path
from .analyzer import AnalysisResult, Finding
from .rules import Category


class TestGenerator:
    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)

    def generate(self, result: AnalysisResult) -> str:
        """Generate test file content based on analysis findings."""
        header = textwrap.dedent('''\
            """
            Auto-generated exploit tests by BlitzDev — FinTech PR Guardian.
            Exposes race conditions, floating-point loss, non-atomic transfers, and idempotency bugs.
            Run with: pytest output/test_fintech_race_condition.py -v
            """
            import pytest
            import asyncio
            import httpx
            from httpx import ASGITransport
            from decimal import Decimal

            from demo_api.main import app
            from demo_api.database import init_db


            @pytest.fixture(autouse=True)
            async def setup_database():
                """Ensure tables exist before tests run."""
                await init_db()


            @pytest.fixture()
            async def client():
                """Provide an async HTTP client wired directly to the FastAPI app ASGI transport."""
                transport = ASGITransport(app=app)
                async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
                    yield c


            @pytest.fixture()
            async def seeded_account(client: httpx.AsyncClient):
                """Create a test account with exactly $100.0 balance for concurrency testing."""
                # Unique user ID per test run to prevent collision
                user_id = f"race_test_user_{asyncio.get_event_loop().time()}"
                resp = await client.post("/accounts/", json={"user_id": user_id})
                assert resp.status_code == 200, f"Account creation failed: {resp.text}"
                account_id = resp.json()["id"]
                
                # Deposit exactly $100.0
                dep_resp = await client.post(
                    f"/accounts/{account_id}/deposit",
                    json={"amount": 100.0},
                )
                assert dep_resp.status_code == 200
                return account_id
        ''')

        sections: list[str] = [header]

        has_concurrency = any(
            f.rule.category == Category.CONCURRENCY for f in result.findings
        )
        has_precision = any(
            f.rule.category == Category.CURRENCY_PRECISION for f in result.findings
        )
        has_acid = any(
            f.rule.category == Category.ACID_ROLLBACK for f in result.findings
        )
        has_idempotency = any(
            f.rule.category == Category.IDEMPOTENCY for f in result.findings
        )

        # ---- Race-condition exploit (FIN-002) --------------------------------
        if has_concurrency:
            sections.append(textwrap.dedent('''\

                # ==============================================================================
                # 🔴 RACE CONDITION TEST (FIN-002): Missing Row Locking on Withdrawals
                # ==============================================================================
                # This test exposes the vulnerability where /accounts/{id}/withdraw reads
                # the balance without `with_for_update()` / row locks.
                # When 5 concurrent requests try to withdraw $100 from a $100 balance,
                # multiple requests read the $100 balance simultaneously before any write commits,
                # resulting in duplicate withdrawals and balance corruption / overdraft.
                # ==============================================================================

                @pytest.mark.asyncio
                async def test_race_condition_concurrent_withdrawals(client, seeded_account):
                    """
                    1. Account starts with $100 balance.
                    2. Fire 5 concurrent withdrawal requests of $100 each.
                    3. Under correct row-locking (SELECT FOR UPDATE), exactly ONE request must succeed (HTTP 200)
                       and the other 4 must fail with HTTP 400 (Insufficient funds).
                    4. Final balance must be $0, not negative.
                    """
                    account_id = seeded_account

                    async def perform_withdrawal():
                        return await client.post(
                            f"/accounts/{account_id}/withdraw",
                            json={"amount": 100.0},
                        )

                    # Fire 5 concurrent withdrawal requests simultaneously
                    responses = await asyncio.gather(*[perform_withdrawal() for _ in range(5)])

                    status_codes = [r.status_code for r in responses]
                    successful_withdrawals = [r for r in responses if r.status_code == 200]
                    failed_withdrawals = [r for r in responses if r.status_code == 400]

                    balance_resp = await client.get(f"/accounts/{account_id}/balance")
                    final_balance = balance_resp.json()["balance"]

                    print(f"\\n[RACE CONDITION TEST RESULT]")
                    print(f"Status codes: {status_codes}")
                    print(f"Successful withdrawals: {len(successful_withdrawals)}/5")
                    print(f"Final account balance: ${final_balance}")

                    # ASSERTION 1: Exactly one request should succeed
                    assert len(successful_withdrawals) == 1, (
                        f"CRITICAL VULNERABILITY: {len(successful_withdrawals)} concurrent withdrawals succeeded! "
                        f"Expected exactly 1. Race condition allowed multiple withdrawals of the same funds."
                    )

                    # ASSERTION 2: Final balance must be 0.0, never negative
                    assert final_balance == 0.0, (
                        f"CRITICAL VULNERABILITY: Balance corrupted to ${final_balance}. Expected $0.0."
                    )
            '''))

        # ---- Float precision exploit (FIN-001) --------------------------------
        if has_precision:
            sections.append(textwrap.dedent('''\

                # ==============================================================================
                # 🔴 CURRENCY PRECISION TEST (FIN-001): IEEE 754 Floating-Point Drift
                # ==============================================================================

                @pytest.mark.asyncio
                async def test_float_precision_drift(client):
                    """
                    Demonstrates floating-point inaccuracy: depositing 0.1 + 0.2 gives 0.30000000000000004
                    instead of exact Decimal 0.3.
                    """
                    user_id = f"precision_user_{asyncio.get_event_loop().time()}"
                    resp = await client.post("/accounts/", json={"user_id": user_id})
                    account_id = resp.json()["id"]

                    await client.post(f"/accounts/{account_id}/deposit", json={"amount": 0.1})
                    await client.post(f"/accounts/{account_id}/deposit", json={"amount": 0.2})

                    balance_resp = await client.get(f"/accounts/{account_id}/balance")
                    balance = balance_resp.json()["balance"]

                    # In float math, 0.1 + 0.2 == 0.30000000000000004
                    print(f"\\n[PRECISION TEST] Balance after 0.1 + 0.2: {balance!r}")
                    assert balance == 0.3, f"Precision loss detected: {balance!r} != 0.3"
            '''))

        # ---- Non-atomic transfer exploit (FIN-003) ----------------------------
        if has_acid:
            sections.append(textwrap.dedent('''\

                # ==============================================================================
                # 🔴 ACID ATOMICITY TEST (FIN-003): Missing Rollback on Transfer Failure
                # ==============================================================================

                @pytest.mark.asyncio
                async def test_transfer_non_atomic_failure_rollback(client):
                    """
                    Transfer to a non-existent recipient (id: 99999).
                    The debit must NOT persist if the credit fails.
                    """
                    user_id = f"sender_{asyncio.get_event_loop().time()}"
                    resp = await client.post("/accounts/", json={"user_id": user_id})
                    source_id = resp.json()["id"]
                    await client.post(f"/accounts/{source_id}/deposit", json={"amount": 500.0})

                    # Attempt transfer to invalid destination
                    transfer_resp = await client.post(
                        "/accounts/transfer",
                        json={"from_account_id": source_id, "to_account_id": 99999, "amount": 200.0},
                    )
                    assert transfer_resp.status_code == 404

                    # Verify source account balance did not deduct funds
                    balance_resp = await client.get(f"/accounts/{source_id}/balance")
                    balance = balance_resp.json()["balance"]

                    assert balance == 500.0, (
                        f"ACID VIOLATION: Source account debited to ${balance} even though transfer failed!"
                    )
            '''))

        # ---- Idempotency exploit (FIN-004) ------------------------------------
        if has_idempotency:
            sections.append(textwrap.dedent('''\

                # ==============================================================================
                # ⚠️ IDEMPOTENCY TEST (FIN-004): Duplicate Request Replay
                # ==============================================================================

                @pytest.mark.asyncio
                async def test_idempotency_key_enforcement(client):
                    """
                    Sending identical request with same idempotency key twice must only process once.
                    """
                    user_id = f"idemp_user_{asyncio.get_event_loop().time()}"
                    resp = await client.post("/accounts/", json={"user_id": user_id})
                    account_id = resp.json()["id"]

                    payload = {"amount": 50.0, "idempotency_key": "unique-uuid-key-001"}

                    r1 = await client.post(f"/accounts/{account_id}/deposit", json=payload)
                    r2 = await client.post(f"/accounts/{account_id}/deposit", json=payload)

                    balance_resp = await client.get(f"/accounts/{account_id}/balance")
                    balance = balance_resp.json()["balance"]

                    assert balance == 50.0, (
                        f"IDEMPOTENCY FAILURE: Replayed deposit was processed twice. Balance is ${balance}, expected $50.0"
                    )
            '''))

        return "\n".join(sections)

    def save(
        self, test_content: str, filename: str = "test_fintech_race_condition.py"
    ) -> Path:
        """Save generated tests to output directory."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        filepath = self.output_dir / filename
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(test_content)

        # Also write to generated_tests subdirectory for organized discovery
        gen_dir = self.output_dir / "generated_tests"
        gen_dir.mkdir(parents=True, exist_ok=True)
        with open(gen_dir / "test_financial_exploits.py", "w", encoding="utf-8") as f:
            f.write(test_content)

        return filepath
