# ⚡ BlitzDev — 48H Battle Plan & KT Document
**Team:** Royal Code | **Hackathon:** IBM Bob 2.0 | **Track:** Code Review & Quality

---

## 🎯 Core Principles
- **Rule #1**: No Bobcoin gets spent without checking this doc first.
- **Rule #2**: Viraj screenshots every Bob task. No exceptions.
- **Rule #3**: We stop building at Hour 40. Last 8 hours = polish + submit only.

---

## 🔴 PRE-BUILD CHECKLIST (Before writing a single line of code)

### Shridhar ✅
- [x] Confirm Bob login email received — check spam, search "IBM Bob"
- [x] Sign into Bob IDE using hackathon email
- [x] Switch Bob account to `ibm-coding-challenge-uat` (region: us-east) in Settings > General
- [x] Verify Bobcoin balance shows 40 coins
- [x] Create GitHub repo: `royal-code/blitzdev`
- [x] Push repository folder structure:
  ```text
  /blitzdev
    /bob_sessions         ← ALL Bob task screenshots go here (MANDATORY)
    /demo-api             ← Viraj's payment API (injected bugs)
    /blitzdev_agent       ← Our Bob-powered scanner
    /output               ← Generated reports, test files, SARIF
    README.md
    .bobignore
  ```

### Viraj ✅
- [x] Confirm Bob login email received — check spam, search "IBM Bob"
- [x] Sign into Bob IDE using hackathon email
- [x] Switch Bob account to `ibm-coding-challenge-uat` (region: us-east)
- [x] Verify Bobcoin balance shows 40 coins
- [x] Clone repo Shridhar created
- [x] Set up clean Python/FastAPI payment API in `demo_api/` (5 routes: balance check, deposit, withdraw, transfer, transaction history)
- [x] Inject Bug 1: Floating-point division on currency calculation (e.g., balance / 3 * 3 instead of Decimal)
- [x] Inject Bug 2: Race condition on withdrawal — no SELECT FOR UPDATE or row lock on balance read
- [x] Confirm the API runs locally: `uvicorn main:app --reload`
- [x] Open a local branch or PR on the demo repo for BlitzDev to scan

---

## 🟡 BOBCOIN BUDGET — 80 COINS TOTAL (40 each)

| # | Task | Owner | Coins | Bob Feature |
|---|------|-------|-------|-------------|
| 1 | Scaffold `blitzdev_agent` repo structure | Shridhar | 5 | Agent Mode |
| 2 | Create FinTech Validator Custom Mode + rules | Shridhar | 8 | Custom Mode |
| 3 | Build GitHub PR diff fetcher + repo context loader | Shridhar | 5 | Agent Mode |
| 4 | Build Financial Blast Radius analyzer → Mermaid output | Shridhar | 7 | Architecture Diagrams |
| 5 | Build output formatter → PR comment markdown | Viraj | 5 | Skills |
| 6 | Build pytest-asyncio race condition test generator | Viraj | 6 | Agent Mode |
| 7 | Integration wiring + bug fixes | Both | 8 | Agent Mode |
| 8 | Architecture diagram of BlitzDev itself | Shridhar | 3 | Architecture Diagrams |
| 9 | README generation | Viraj | 3 | Document Understanding |
| **TOTAL PLANNED** | | | **50** | |
| **RESERVE — DO NOT TOUCH** | | | **30** | Emergency / buffer only |

---

## 🟢 HOUR-BY-HOUR EXECUTION PLAN

### HOUR 0–4 | Foundation (Zero Bobcoins)
- GitHub repo created with full folder structure.
- FinTech Validator Mode rules created.
- `.bobignore` created.
- Demo payment API running locally with injected flaws.

### HOUR 4–10 | Core Build Part 1 (Shridhar)
- Task 1 (5 coins): Scaffold agent structure in `/blitzdev_agent`.
- Task 2 (8 coins): FinTech Validator Custom Mode in Bob IDE.
- Task 3 (5 coins): Blast Radius analyzer with Mermaid diagrams.

### HOUR 10–18 | Core Build Part 2 (Viraj)
- Task 4 (5 coins): PR comment markdown formatter (`formatter.py`).
- Task 5 (6 coins): Race condition test generator (`test_generator.py`).

### HOUR 18–28 | Integration (Both)
- Task 6 (8 coins): End-to-end orchestration CLI (`main.py`).
- Generate `PR_COMMENT.md`, `blitzdev_report.sarif`, and `test_fintech_race_condition.py`.

### HOUR 28–32 | Documentation & Diagrams
- Task 7 (3 coins): Mermaid architecture diagram (`docs/architecture.md`).
- Task 8 (3 coins): Comprehensive `README.md`.

### HOUR 32–40 | Final Polish & Video
- Record 2-minute demo video.
- Test cycle: Fail on broken demo API → Fix → Pass.

### HOUR 40–48 | Buffer & Verification
- Code freeze & submission verification on lablab.ai.
