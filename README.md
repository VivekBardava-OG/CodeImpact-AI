# CodeImpact AI ⚡

> **AI-Powered Codebase Impact Analysis Agent Using FalkorDB**  
> *Track 1: Agents That Act on Connected Data*

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)](https://fastapi.tiangolo.com/)
[![FalkorDB](https://img.shields.io/badge/FalkorDB-Graph_Database-orange.svg)](https://www.falkordb.com/)
[![React](https://img.shields.io/badge/React-18-61dafb.svg)](https://react.dev/)
[![React Flow](https://img.shields.io/badge/React_Flow-11-ff0072.svg)](https://reactflow.dev/)
[![Tests](https://img.shields.io/badge/tests-14%20passed-brightgreen.svg)]()

---

## 🚀 Overview

**CodeImpact AI** is an intelligent developer tool that answers the critical question every engineer faces before merging a pull request:

> **"If I modify this function or file, what could break, which tests should I run, and why?"**

Unlike naive vector search or LLM guessing, CodeImpact AI relies on **real graph relationships and Cypher queries executed in FalkorDB**. Dependency analysis is deterministic, mathematically bounded, and explainable through explicit graph traversal paths.

### Key Capabilities
- **FalkorDB as Primary Graph Database:** Models repositories as property graphs with `:Repository`, `:File`, `:Symbol`, and `:Test` nodes connected by `[:CALLS]`, `[:IMPORTS]`, `[:TESTS]`, and `[:DEPENDS_ON]` edges.
- **Bounded Multi-Hop Traversal:** Identifies direct (1 hop) and transitive (2+ hops) dependents, gracefully handling circular calls and deep recursion.
- **Affected Test Discovery:** Finds all automated tests that directly or indirectly exercise changed components, complete with confidence scores and graph reachability paths.
- **Interactive React Flow Visualization:** Explores the blast radius with custom node styling, animated directional call edges, and clickable inspection drawers.
- **Git Diff Blast Radius Analyzer:** Maps modified lines from unified Git diffs directly to graph symbols and computes cumulative blast radiuses.
- **Dual-Mode Explanation:**
  - *Deterministic Engine:* Generates structured, zero-hallucination markdown summaries from Cypher query results without requiring any API key.
  - *LLM Grounded (Optional):* Translates graph facts into conversational answers when an API key is provided.
- **Live Cypher Query Telemetry:** Live inspector displaying the exact OpenCypher queries executed against FalkorDB with parameter bindings and latency.

---

## 🛠️ Technology Stack

| Layer | Technologies |
|---|---|
| **Graph Database** | **FalkorDB** (Docker container `falkordb/falkordb:latest`), official `falkordb` Python client |
| **Backend** | Python 3.11+, FastAPI, Uvicorn, Python AST (`ast` module), Pydantic v2 |
| **Frontend** | React 18, Vite, TypeScript, Tailwind CSS, React Flow |
| **Testing** | Pytest, FastAPI TestClient, synthetic repeatable test fixtures |

---

## 📂 Project Structure

```
CodeImpact-AI/
├── docker-compose.yml          # FalkorDB Docker container configuration
├── .env.example                # Environment variables template
├── requirements.txt            # Backend dependencies
├── pytest.ini                  # Pytest configuration
├── README.md                   # Project overview & quickstart
├── ARCHITECTURE.md             # Complete architectural documentation
├── GRAPH_SCHEMA.md             # FalkorDB node & edge schema documentation
├── DEMO_SCRIPT.md              # Step-by-step change-impact demo walkthrough
│
├── backend/
│   ├── app/
│   │   ├── main.py             # FastAPI entrypoint
│   │   ├── config.py           # Pydantic settings
│   │   ├── core/
│   │   │   ├── db.py           # FalkorDB connection manager & telemetry
│   │   │   ├── parser.py       # AST parser & deterministic call resolver
│   │   │   ├── ingestion.py    # Safe repository ingestion & security filters
│   │   │   ├── graph_builder.py# FalkorDB node/edge builder
│   │   │   ├── impact_engine.py# Cypher-powered bounded traversal engine
│   │   │   ├── diff_analyzer.py# Git diff parser mapped to graph symbols
│   │   │   └── llm_explainer.py# Deterministic & LLM explanation services
│   │   └── api/
│   │       ├── routes.py       # REST API endpoints
│   │       └── schemas.py      # Pydantic validation schemas
│   ├── tests/                  # Automated test suite (14 passing tests)
│   └── fixtures/sample_project/# Synthetic multi-tier Python test repository
│
└── frontend/                   # React + Vite + TypeScript dashboard
    ├── src/
    │   ├── App.tsx             # Main dashboard
    │   ├── api.ts              # Backend API client
    │   ├── types.ts            # TypeScript definitions
    │   └── components/         # React Flow graph, diff view, telemetry console
    └── package.json
```

---

## ⚡ Quickstart Guide

### 1. Prerequisites
- Docker & Docker Compose
- Python 3.11 or 3.12
- Node.js 18+ and npm

### 2. Start FalkorDB
Launch FalkorDB using Docker Compose:
```bash
docker compose up -d
```
Verify the container is running on port `6379`:
```bash
docker ps
```

### 3. Backend Setup
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment (Windows PowerShell)
.\venv\Scripts\Activate.ps1
# On Linux/macOS: source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment variables
copy .env.example .env

# Run automated tests
pytest -v

# Start the FastAPI server
uvicorn app.main:app --reload --port 8000
```
Backend API interactive Swagger docs: `http://localhost:8000/docs`.

### 4. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
Open your browser at `http://localhost:5173`.

---

## 🔍 Example Cypher Queries

### Transitive Dependent Discovery (Bounded 1..5 Hops)
```cypher
MATCH p = (caller)-[:CALLS*1..5]->(target:Symbol {id: $symbol_id})
WHERE caller <> target
RETURN caller.name, caller.file_path, length(p) as hop_count,
       [n in nodes(p) | {id: n.id, name: n.name}] as path_nodes
ORDER BY hop_count ASC
```

### Affected Test Reachability
```cypher
MATCH p = (t:Test)-[:TESTS|CALLS*1..5]->(target:Symbol {id: $symbol_id})
RETURN t.name, t.file_path, length(p) as hop_count,
       [n in nodes(p) | {id: n.id, name: n.name}] as path_nodes
ORDER BY hop_count ASC
```

---

## 🔒 Security & Safe Ingestion

- **Zip Slip Mitigation:** Extraction strictly validates target paths to prevent directory traversal attacks (`../` or absolute paths).
- **Resource Limits:** Enforces a maximum archive size of 25MB and a limit of 500 files to prevent zip bombs.
- **No Code Execution:** Ingested source files are strictly parsed using Python's static Abstract Syntax Tree (`ast.parse`) and never executed.
- **Sensitive File Exclusion:** Automatically ignores `.git`, `.env`, `.pem`, secrets, virtual environments, and binary files.

---

## ⚠️ Limitations & Language Support

- **Language Support:** The primary analysis engine is optimized for **Python** repositories using AST parsing. Non-Python files (e.g. JavaScript, Go, Rust) are detected and documented in the UI as unsupported languages rather than falsely simulated.
- **Dynamic Invocations:** Purely dynamic calls such as `getattr(obj, var)()` or `eval()` cannot be resolved statically and are explicitly labeled as `unresolved` rather than inventing false graph relationships.

---

## 🤖 AI Coding Tool Disclosure

In accordance with Hackathon Track 1 rules:
- Antigravity AI was utilized for boilerplate generation, scaffolding assistance, and test case structuring.
- The graph schema, Cypher query design, AST call resolution algorithm, and FalkorDB integration were custom designed and verified for this project.

---

## 📜 License

MIT License. Built for the FalkorDB Graph Hacks Hackathon.
