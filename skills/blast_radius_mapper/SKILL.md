---
name: blast-radius-mapper
description: Generates dynamic Mermaid architecture flowcharts that visualize the financial blast radius of pull request code changes across routes, database tables, and missing security controls.
---

# 📊 Financial Blast Radius Mapper Skill

This skill extracts structural relationships from target codebases and compiles a deterministic Mermaid flowchart illustrating the systemic impact of code changes.

## 🏗️ Diagram Architecture

The generated Mermaid diagram contains 3 core subgraphs:
1. **Routes Subgraph**: Modified and affected API endpoints (e.g. `POST /accounts/{id}/withdraw`).
2. **Database Subgraph**: ORM entities and database tables touched (e.g. `Account`, `Transaction`).
3. **Missing Controls Subgraph**: Flagged financial vulnerabilities highlighted with severity color-coding.

## 🎨 Node Styling & Color Scheme
- `critical`: Red background (`#ffebee`) and dark red border (`#c62828`).
- `warning`: Orange background (`#fff3e0`) and dark orange border (`#ef6c00`).
- `info`: Blue background (`#e3f2fd`) and dark blue border (`#1565c0`).

## 🔗 Linkage Rules
- **Solid arrows (`-->`)**: Represent direct data access between routes and database models.
- **Dotted arrows (`-.->`)**: Connect affected routes directly to their corresponding missing control or security flaw.
