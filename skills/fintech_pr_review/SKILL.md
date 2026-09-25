---
name: fintech-pr-review
description: Specialized financial domain code review skill for pull requests. Detects floating-point currency calculations, missing database row-level locking, non-atomic multi-step transfers, and missing idempotency checks.
---

# 🛡️ FinTech PR Review Skill

This skill equips AI agents (such as IBM Bob 2.0 or custom subagents) to perform automated, domain-aware security and logic reviews on financial APIs, payment ledgers, and transaction engines.

## 🎯 Purpose & Scope
Standard linters check syntax, types, and formatting, but they miss high-risk financial business logic flaws. This skill focuses on financial correctness, data integrity, and ACID guarantees.

## 📋 FinTech Domain Rules Checklist

### 1. Currency Precision (`FIN-001`)
- **Severity**: 🔴 CRITICAL
- **Check**: Monetary amounts (`balance`, `amount`, `fee`, `total`) must **NEVER** use IEEE 754 floating-point primitives (`float`).
- **Required**: Use `decimal.Decimal` or store currency as integer cents (`int`).

### 2. Concurrency & Row-Level Locking (`FIN-002`)
- **Severity**: 🔴 CRITICAL
- **Check**: Any endpoint or service modifying account balances must lock the database row during read.
- **Required**: In SQLAlchemy/SQL, use `with_for_update()` / `SELECT FOR UPDATE` or mutex locks to prevent race conditions on concurrent withdrawals.

### 3. ACID Atomicity & Rollbacks (`FIN-003`)
- **Severity**: 🔴 CRITICAL
- **Check**: Multi-step fund movements (e.g., debiting Account A and crediting Account B) must occur in a **single database transaction**.
- **Required**: Never call `.commit()` multiple times across interdependent account balance changes.

### 4. Idempotency Key Validation (`FIN-004`)
- **Severity**: ⚠️ WARNING
- **Check**: Mutation endpoints (`/deposit`, `/withdraw`, `/transfer`) must enforce idempotency keys to reject duplicate requests.
- **Required**: Check database for existing `idempotency_key` before modifying balances.

### 5. Authentication & Authorization Middleware (`FIN-005`)
- **Severity**: ⚠️ WARNING
- **Check**: Financial mutation routes must be protected with auth dependencies (e.g. `Depends(get_current_user)`).

### 6. Error Handling & Rollbacks (`FIN-006`)
- **Severity**: ⚠️ WARNING
- **Check**: Catch blocks around database transactions must explicitly call `session.rollback()`.

### 7. Explicit Precision Imports (`FIN-007`)
- **Severity**: ℹ️ INFO
- **Check**: Financial service modules must import `from decimal import Decimal`.

## 📤 Output Format
The skill formats findings into:
1. **Critical Financial Risks (🔴)**
2. **Warnings & Missing Controls (⚠️)**
3. **Financial Blast Radius Map (Mermaid Flowchart)**
4. **Concrete Code Remediations (💡)**
