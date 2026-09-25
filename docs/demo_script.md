# 🎬 BlitzDev — 2-Minute Video Demo Script & Presentation Guide
**Team:** Royal Code | **Hackathon:** IBM Bob 2.0 | **Track:** Code Review & Quality

---

## ⏱️ Video Breakdown (Total: 2:00 – 2:30 min)

### [0:00 – 0:25] Act I: The Hidden Danger in Standard PRs
- **Visual:** Open VS Code / IBM Bob IDE with `demo_api/main.py` showing the `/withdraw` and `/transfer` endpoints. Run standard linters (`flake8`, `ruff`, `pylint`).
- **Voiceover:** 
  > *"Every day, standard linters check syntax, types, and style. But in financial systems, the most catastrophic bugs aren't syntax errors—they're business logic flaws. Here is a fast, clean FastAPI banking ledger. Linters give it a 100% clean bill of health. But lurking inside are missing database locks, floating-point rounding errors, and non-atomic transfers that can bankrupt a FinTech startup in milliseconds."*

---

### [0:25 – 0:55] Act II: Autonomous Analysis via IBM Bob 2.0
- **Visual:** Switch to **IBM Bob 2.0 IDE** in **FinTech Validator Custom Mode**. Trigger BlitzDev with:
  ```bash
  python -m blitzdev_agent --repo ./demo_api --pr 1
  ```
- **Voiceover:**
  > *"Enter BlitzDev, a FinTech-Aware PR Guardian built on IBM Bob 2.0. Operating in autonomous Agent Mode with custom FinTech domain skills, BlitzDev inspects the PR diff against the full repository context. It doesn't just read code—it traces financial data flows across database models, routes, and services."*

---

### [0:55 – 1:20] Act III: The Financial Blast Radius & PR Comment
- **Visual:** Open `output/PR_COMMENT.md` in markdown preview. Highlight the **Financial Blast Radius Mermaid Diagram** and the **Critical Financial Risks** section.
- **Voiceover:**
  > *"BlitzDev automatically generates a rich PR comment featuring a visual Financial Blast Radius map. It flags that the `/withdraw` route lacks row-level locking (`with_for_update()`), exposes that float arithmetic is causing IEEE 754 precision loss, and warns of non-atomic transfers that lack database rollback boundaries."*

---

### [1:20 – 1:45] Act IV: Proving the Vulnerability (The Exploit Test)
- **Visual:** Open terminal and run the auto-generated exploit test:
  ```bash
  pytest output/test_fintech_race_condition.py -v
  ```
- **Terminal Output:** Watch `test_race_condition_concurrent_withdrawals` and `test_float_precision_drift` **FAIL** with red assertions.
- **Voiceover:**
  > *"Rather than just claiming there's a bug, BlitzDev generates a targeted pytest-asyncio exploit suite. It fires 5 concurrent requests of $100 against a $100 account. Because row locking was omitted, multiple withdrawals succeed simultaneously, corrupting the balance into negative numbers. The test fails, proving the vulnerability in seconds."*

---

### [1:45 – 2:10] Act V: The Remediation (Fail → Fix → Pass)
- **Visual:** Apply the recommended fix in `demo_api/main.py` (adding row lock & Decimal handling) or run:
  ```bash
  python -m demo_api.apply_remediations
  pytest output/test_fintech_race_condition.py -v
  ```
- **Terminal Output:** Green passing checks `[4 passed in 0.45s]`.
- **Voiceover:**
  > *"Applying BlitzDev's recommended remediation—wrapping balance reads with database row locks and converting floats to exact Decimals—we rerun the test suite. All tests turn green. The exploit is eliminated before the PR ever merges into production."*

---

### [2:10 – 2:30] Act VI: Closing & IBM Bob 2.0 Highlights
- **Visual:** Show `bob_sessions/` audit directory, architecture diagram in `docs/architecture.md`, and lablab.ai submission slide.
- **Voiceover:**
  > *"Powered by IBM Bob 2.0 Custom Modes, autonomous subagents, and persistent task session tracking, BlitzDev turns pull request reviews into an unshakeable financial shield. Built with pride by Team Royal Code."*
