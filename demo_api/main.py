import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from demo_api.database import get_db, init_db
from demo_api.models import Account, Transaction
from demo_api.schemas import WithdrawRequest, TransferRequest, DepositRequest

# Mutex registry providing deterministic row-level serialization for ledger mutations
_account_locks = {}

def get_account_lock(account_id: int) -> asyncio.Lock:
    if account_id not in _account_locks:
        _account_locks[account_id] = asyncio.Lock()
    return _account_locks[account_id]

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

app = FastAPI(
    title="Royal Bank Ledger API (Remediated)",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "Royal Bank Ledger API (Remediated)"}

@app.get("/accounts/{account_id}/balance")
async def get_balance(account_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Account).where(Account.id == account_id))
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return {"account_id": account.id, "balance": account.balance}

@app.post("/accounts/{account_id}/deposit")
async def deposit(account_id: int, req: DepositRequest, db: AsyncSession = Depends(get_db)):
    lock = get_account_lock(account_id)
    async with lock:
        result = await db.execute(select(Account).where(Account.id == account_id))
        account = result.scalar_one_or_none()
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")
            
        account.balance = round(account.balance + req.amount, 2)
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
    # REMEDIATED (FIN-002): Serialized mutex lock enforces atomic balance validation & debit
    lock = get_account_lock(account_id)
    async with lock:
        result = await db.execute(select(Account).where(Account.id == account_id))
        account = result.scalar_one_or_none()
        
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")
            
        if account.balance < req.amount:
            raise HTTPException(status_code=400, detail="Insufficient funds")
        
        # REMEDIATED (FIN-001): Quantized precision balance calculation
        account.balance = round(account.balance - req.amount, 2)
        
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
    # REMEDIATED (FIN-003): Single atomic transaction block with deadlock-free sorted locks
    lock1 = get_account_lock(min(req.from_account_id, req.to_account_id))
    lock2 = get_account_lock(max(req.from_account_id, req.to_account_id))
    
    async with lock1:
        async with lock2:
            result_from = await db.execute(select(Account).where(Account.id == req.from_account_id))
            source_acc = result_from.scalar_one_or_none()
            
            result_to = await db.execute(select(Account).where(Account.id == req.to_account_id))
            dest_acc = result_to.scalar_one_or_none()
            
            if not source_acc or not dest_acc:
                raise HTTPException(status_code=404, detail="One or both accounts not found")
                
            if source_acc.balance < req.amount:
                raise HTTPException(status_code=400, detail="Insufficient funds in source account")
                
            source_acc.balance = round(source_acc.balance - req.amount, 2)
            dest_acc.balance = round(dest_acc.balance + req.amount, 2)
            
            db.add(Transaction(account_id=source_acc.id, amount=-req.amount, type="transfer_out", idempotency_key=req.idempotency_key))
            db.add(Transaction(account_id=dest_acc.id, amount=req.amount, type="transfer_in", idempotency_key=req.idempotency_key))
            
            # Atomic single commit
            await db.commit()
            return {"message": "Transfer completed successfully", "source_balance": source_acc.balance}
