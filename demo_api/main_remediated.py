import asyncio
from contextlib import asynccontextmanager
from decimal import Decimal, ROUND_HALF_UP
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from demo_api.database import get_db, init_db
from demo_api.models import Account, Transaction
from demo_api.schemas import WithdrawRequest, TransferRequest, DepositRequest

# In-memory mutex registry ensuring deterministic row-level serialization
_account_locks = {}

def get_account_lock(account_id: int) -> asyncio.Lock:
    if account_id not in _account_locks:
        _account_locks[account_id] = asyncio.Lock()
    return _account_locks[account_id]

def to_decimal(val) -> Decimal:
    """Convert any numeric value to a strict 2-decimal quantized Decimal (FIN-001)."""
    return Decimal(str(val)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

app = FastAPI(
    title="Royal Bank Ledger API (Production Hardened)",
    version="1.2.0",
    lifespan=lifespan
)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "Royal Bank Ledger API (Production Hardened)"}

@app.get("/accounts/{account_id}/balance")
async def get_balance(account_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Account).where(Account.id == account_id))
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return {"account_id": account.id, "balance": float(to_decimal(account.balance))}

@app.post("/accounts/{account_id}/deposit")
async def deposit(account_id: int, req: DepositRequest, db: AsyncSession = Depends(get_db)):
    lock = get_account_lock(account_id)
    async with lock:
        try:
            # FIN-004: Validate idempotency key prior to state mutation
            if req.idempotency_key:
                existing_txn = await db.execute(
                    select(Transaction).where(Transaction.idempotency_key == req.idempotency_key)
                )
                if existing_txn.scalar_one_or_none():
                    acc_res = await db.execute(select(Account).where(Account.id == account_id))
                    acc = acc_res.scalar_one()
                    return {"message": "Deposit already processed (idempotent replay)", "balance": float(to_decimal(acc.balance))}

            result = await db.execute(select(Account).where(Account.id == account_id))
            account = result.scalar_one_or_none()
            if not account:
                raise HTTPException(status_code=404, detail="Account not found")
                
            current_balance = to_decimal(account.balance)
            new_balance = current_balance + req.amount
            account.balance = float(new_balance)

            txn = Transaction(
                account_id=account.id,
                amount=float(req.amount),
                type="deposit",
                idempotency_key=req.idempotency_key
            )
            db.add(txn)
            await db.commit()
            await db.refresh(account)
            return {"message": "Deposit successful", "balance": float(to_decimal(account.balance))}
        except Exception:
            await db.rollback()
            raise

@app.post("/accounts/{account_id}/withdraw")
async def withdraw(account_id: int, req: WithdrawRequest, db: AsyncSession = Depends(get_db)):
    # FIN-002: Serialized row-level mutex prevents concurrent balance race conditions
    lock = get_account_lock(account_id)
    async with lock:
        try:
            # FIN-004: Enforce idempotency key replay defense
            if req.idempotency_key:
                existing_txn = await db.execute(
                    select(Transaction).where(Transaction.idempotency_key == req.idempotency_key)
                )
                if existing_txn.scalar_one_or_none():
                    acc_res = await db.execute(select(Account).where(Account.id == account_id))
                    acc = acc_res.scalar_one()
                    return {"message": "Withdrawal already processed (idempotent replay)", "new_balance": float(to_decimal(acc.balance))}

            result = await db.execute(select(Account).where(Account.id == account_id))
            account = result.scalar_one_or_none()
            
            if not account:
                raise HTTPException(status_code=404, detail="Account not found")
                
            current_balance = to_decimal(account.balance)
            if current_balance < req.amount:
                raise HTTPException(status_code=400, detail="Insufficient funds")
            
            # FIN-001: Strict Decimal balance calculation
            new_balance = current_balance - req.amount
            account.balance = float(new_balance)
            
            txn = Transaction(
                account_id=account.id,
                amount=float(req.amount),
                type="withdraw",
                idempotency_key=req.idempotency_key
            )
            db.add(txn)
            await db.commit()
            await db.refresh(account)
            return {"message": "Withdrawal successful", "new_balance": float(to_decimal(account.balance))}
        except Exception:
            await db.rollback()
            raise

@app.post("/accounts/transfer")
async def transfer(req: TransferRequest, db: AsyncSession = Depends(get_db)):
    # Guard against self-transfer deadlock
    if req.from_account_id == req.to_account_id:
        raise HTTPException(status_code=400, detail="Cannot transfer funds to the same account")

    # FIN-003: Deterministic deadlock-free sorted lock acquisition
    first_id = min(req.from_account_id, req.to_account_id)
    second_id = max(req.from_account_id, req.to_account_id)
    
    lock1 = get_account_lock(first_id)
    lock2 = get_account_lock(second_id)
    
    async with lock1:
        async with lock2:
            try:
                # FIN-004: Validate idempotency key for transfers
                if req.idempotency_key:
                    existing_txn = await db.execute(
                        select(Transaction).where(Transaction.idempotency_key == req.idempotency_key)
                    )
                    if existing_txn.scalar_one_or_none():
                        acc_res = await db.execute(select(Account).where(Account.id == req.from_account_id))
                        acc = acc_res.scalar_one()
                        return {"message": "Transfer already processed (idempotent replay)", "source_balance": float(to_decimal(acc.balance))}

                result_from = await db.execute(select(Account).where(Account.id == req.from_account_id))
                source_acc = result_from.scalar_one_or_none()
                
                result_to = await db.execute(select(Account).where(Account.id == req.to_account_id))
                dest_acc = result_to.scalar_one_or_none()
                
                if not source_acc or not dest_acc:
                    raise HTTPException(status_code=404, detail="One or both accounts not found")
                    
                source_balance = to_decimal(source_acc.balance)
                if source_balance < req.amount:
                    raise HTTPException(status_code=400, detail="Insufficient funds in source account")
                    
                source_acc.balance = float(source_balance - req.amount)
                dest_acc.balance = float(to_decimal(dest_acc.balance) + req.amount)
                
                db.add(Transaction(account_id=source_acc.id, amount=float(-req.amount), type="transfer_out", idempotency_key=req.idempotency_key))
                db.add(Transaction(account_id=dest_acc.id, amount=float(req.amount), type="transfer_in", idempotency_key=req.idempotency_key))
                
                # FIN-003: Single atomic commit ensuring both legs settle together
                await db.commit()
                return {"message": "Transfer completed successfully", "source_balance": float(to_decimal(source_acc.balance))}
            except Exception:
                await db.rollback()
                raise
