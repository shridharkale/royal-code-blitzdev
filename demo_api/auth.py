"""
FinTech Authentication Dependency (FIN-005 Remediation)
======================================================
Provides JWT Bearer token authentication for financial ledger
mutation endpoints (/deposit, /withdraw, /transfer) using python-jose.
"""
import os
from fastapi import Header, HTTPException, status
from jose import JWTError, jwt
from typing import Optional

# In production, load via secrets manager / env variable.
# Ensure JWT_SECRET is set in the runtime environment.
JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-in-production")
JWT_ALGORITHM = "HS256"


async def verify_token(
    authorization: Optional[str] = Header(default=None),
) -> dict:
    """
    FIN-005 Guard: Validates the JWT Bearer token on every money-movement
    route (/withdraw, /deposit, /transfer) using python-jose.

    Raises HTTP 401 if the token is absent, malformed, or has an invalid
    signature/claims.  Returns the decoded claims dict on success.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication scheme — Bearer token required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = authorization.split(" ", 1)[1].strip()
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Empty Bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        subject: Optional[str] = payload.get("sub")
        if subject is None:
            raise credentials_exception
        return payload
    except JWTError:
        raise credentials_exception
