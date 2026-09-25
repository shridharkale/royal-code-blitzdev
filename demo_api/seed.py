import asyncio
from demo_api.database import async_session, init_db, engine
from demo_api.models import Account, Base

async def seed():
    await init_db()
    async with async_session() as session:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
            
        acc1 = Account(id=1, user_id="viraj_primary", balance=100.0)
        acc2 = Account(id=2, user_id="shridhar_receiver", balance=50.0)
        
        session.add_all([acc1, acc2])
        await session.commit()
        print("✅ Database cleanly initialized and seeded:")
        print("   - Account 1: $100.00 (viraj_primary)")
        print("   - Account 2: $50.00 (shridhar_receiver)")

if __name__ == "__main__":
    asyncio.run(seed())
