from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.orm import declarative_base
import datetime

Base = declarative_base()

class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(64), nullable=False, index=True)
    balance = Column(Float, default=0.0, nullable=False)

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    account_id = Column(Integer, nullable=False, index=True)
    amount = Column(Float, nullable=False)
    type = Column(String(32), nullable=False)
    idempotency_key = Column(String(128), nullable=True, index=True)
    status = Column(String(32), default="completed", nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
