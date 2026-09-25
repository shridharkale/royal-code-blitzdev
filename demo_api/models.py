from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.orm import declarative_base
from datetime import datetime, timezone

Base = declarative_base()

class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(64), nullable=False, index=True)
    # INJECTED FLAW FIN-001: Float used for currency balance instead of Decimal or integer cents
    balance = Column(Float, default=0.0, nullable=False)

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    account_id = Column(Integer, nullable=False, index=True)
    amount = Column(Float, nullable=False)
    type = Column(String(32), nullable=False)
    idempotency_key = Column(String(128), nullable=True, index=True)
    status = Column(String(32), default="completed", nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
