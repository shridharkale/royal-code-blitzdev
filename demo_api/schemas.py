from pydantic import BaseModel, Field
from typing import Optional

class AccountCreate(BaseModel):
    user_id: str = Field(..., min_length=1)
    initial_balance: float = Field(0.0, ge=0.0)

class WithdrawRequest(BaseModel):
    amount: float = Field(..., gt=0.0)
    idempotency_key: Optional[str] = None

class TransferRequest(BaseModel):
    from_account_id: int
    to_account_id: int
    amount: float = Field(..., gt=0.0)
    idempotency_key: Optional[str] = None

class DepositRequest(BaseModel):
    amount: float = Field(..., gt=0.0)
    idempotency_key: Optional[str] = None
