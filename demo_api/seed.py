import asyncio
from demo_api.database import async_session, init_db, engine
from demo_api.models import Account, Base

async def seed():
    # 1. Clean DDL reset outside of active session context
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    # 2. Ensure PRAGMA configuration (WAL, busy_timeout, foreign_keys)
    await init_db()

    # 3. Deterministic balance seeding
    async with async_session() as session:
        acc1 = Account(id=1, user_id="viraj_primary", balance=100.0)
        acc2 = Account(id=2, user_id="shridhar_receiver", balance=50.0)
        session.add_all([acc1, acc2])
        await session.commit()
        print("✅ Database cleanly initialized and seeded:")
        print("   - Account 1: $100.00 (viraj_primary)")
        print("   - Account 2: $50.00 (shridhar_receiver)")

    # 4. Clear in-memory mutex registry for 100% test isolation
    try:
        from demo_api.main import _account_locks
        _account_locks.clear()
    except Exception:
        pass

if __name__ == "__main__":
    asyncio.run(seed())
