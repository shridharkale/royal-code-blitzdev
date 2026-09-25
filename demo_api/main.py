from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from demo_api.database import get_db, init_db
from demo_api.models import Account, Transaction
from demo_api.schemas import WithdrawRequest, TransferRequest, DepositRequest
import asyncio

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

app = FastAPI(
    title="Royal Bank Ledger API",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "Royal Bank Ledger API"}

@app.get("/accounts/{account_id}/balance")
async def get_balance(account_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Account).where(Account.id == account_id))
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return {"account_id": account.id, "balance": account.balance}

@app.post("/accounts/{account_id}/deposit")
async def deposit(account_id: int, req: DepositRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Account).where(Account.id == account_id))
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
        
    account.balance = account.balance + req.amount
    txn = Transaction(
        account_id=account.id,
        amount=req.amount,
        type="deposit",
        idempotency_key=req.idempotency_key
    )
    db.add(txn)
    await db.commit()
    await db.refresh(account)
    return {"message": "Deposit successful", "balance": account.balance}

@app.post("/accounts/{account_id}/withdraw")
async def withdraw(account_id: int, req: WithdrawRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Account).where(Account.id == account_id))
    account = result.scalar_one_or_none()
    
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
        
    await asyncio.sleep(0.05)
    
    if account.balance < req.amount:
        raise HTTPException(status_code=400, detail="Insufficient funds")
    
    account.balance = account.balance - req.amount
    
    txn = Transaction(
        account_id=account.id,
        amount=req.amount,
        type="withdraw",
        idempotency_key=req.idempotency_key
    )
    db.add(txn)
    await db.commit()
    await db.refresh(account)
    return {"message": "Withdrawal successful", "new_balance": account.balance}

@app.post("/accounts/transfer")
async def transfer(req: TransferRequest, db: AsyncSession = Depends(get_db)):
    result_from = await db.execute(select(Account).where(Account.id == req.from_account_id))
    source_acc = result_from.scalar_one_or_none()
    
    result_to = await db.execute(select(Account).where(Account.id == req.to_account_id))
    dest_acc = result_to.scalar_one_or_none()
    
    if not source_acc or not dest_acc:
        raise HTTPException(status_code=404, detail="One or both accounts not found")
        
    if source_acc.balance < req.amount:
        raise HTTPException(status_code=400, detail="Insufficient funds in source account")
        
    source_acc.balance = source_acc.balance - req.amount
    db.add(Transaction(account_id=source_acc.id, amount=-req.amount, type="transfer_out", idempotency_key=req.idempotency_key))
    await db.commit()
    
    dest_acc.balance = dest_acc.balance + req.amount
    db.add(Transaction(account_id=dest_acc.id, amount=req.amount, type="transfer_in", idempotency_key=req.idempotency_key))
    await db.commit()
    
    return {"message": "Transfer completed successfully", "source_balance": source_acc.balance}
