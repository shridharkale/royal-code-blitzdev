from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field

class AccountCreate(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=64)
    initial_balance: Decimal = Field(default=Decimal("0.00"), ge=Decimal("0.00"), decimal_places=2)

class WithdrawRequest(BaseModel):
    # FIN-001 / FIN-007: Quantized Decimal validation enforcing positive withdrawal
    amount: Decimal = Field(..., gt=Decimal("0.00"), decimal_places=2)
    idempotency_key: Optional[str] = Field(None, min_length=1, max_length=128)

class TransferRequest(BaseModel):
    from_account_id: int = Field(..., gt=0)
    to_account_id: int = Field(..., gt=0)
    amount: Decimal = Field(..., gt=Decimal("0.00"), decimal_places=2)
    idempotency_key: Optional[str] = Field(None, min_length=1, max_length=128)

class DepositRequest(BaseModel):
    amount: Decimal = Field(..., gt=Decimal("0.00"), decimal_places=2)
    idempotency_key: Optional[str] = Field(None, min_length=1, max_length=128)
