import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from demo_api.database import get_db, init_db
from demo_api.models import Account, Transaction
from demo_api.schemas import WithdrawRequest, TransferRequest, DepositRequest

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

app = FastAPI(
    title="Royal Bank Ledger API (Vulnerable Baseline)",
    version="0.1.0",
    lifespan=lifespan
)

@app.get("/accounts/{account_id}/balance")
async def get_balance(account_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Account).where(Account.id == account_id))
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return {"account_id": account.id, "balance": account.balance}

@app.post("/accounts/{account_id}/withdraw")
async def withdraw(account_id: int, req: WithdrawRequest, db: AsyncSession = Depends(get_db)):
    # VULNERABLE (FIN-002): Balance read without row locks
    result = await db.execute(select(Account).where(Account.id == account_id))
    account = result.scalar_one_or_none()
    
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
        
    # Simulate database latency to guarantee concurrent race condition triggers
    await asyncio.sleep(0.05)
    
    if account.balance < float(req.amount):
        raise HTTPException(status_code=400, detail="Insufficient funds")
    
    # VULNERABLE (FIN-001): Direct float mutation without quantization
    account.balance = account.balance - float(req.amount)
    
    # VULNERABLE (FIN-004): Idempotency key stored but never validated
    txn = Transaction(
        account_id=account.id,
        amount=float(req.amount),
        type="withdraw",
        idempotency_key=req.idempotency_key
    )
    db.add(txn)
    await db.commit()
    await db.refresh(account)
    return {"message": "Withdrawal successful", "new_balance": account.balance}
