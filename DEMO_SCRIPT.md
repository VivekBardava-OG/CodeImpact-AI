# CodeImpact AI Demo Script: Change Impact Scenario

This demo script demonstrates the full workflow of **CodeImpact AI** on a realistic repository change scenario.

---

## Scenario: Modifying `authenticate_user()`

### The Developer's Question:
> *"If I modify the `authenticate_user()` function in `auth/security.py`, what could break, which tests should I run, and why?"*

---

## Step 1: Start Services & Open Dashboard

1. Ensure FalkorDB is running:
   ```bash
   docker compose up -d
   ```
2. Start the Backend:
   ```bash
   .\venv\Scripts\uvicorn app.main:app --reload --port 8000
   ```
3. Start the Frontend:
   ```bash
   cd frontend && npm run dev
   ```
4. Navigate to `http://localhost:5173` in your browser.
5. Verify the **FalkorDB Connected** pill is green in the top right.

---

## Step 2: Ingest & Index the Sample Repository

1. In the **Repository Source & Ingestion** card, click **Load & Index Sample**.
2. Observe the indexing progress:
   - FalkorDB creates nodes for `Repository`, `File`, `Symbol`, and `Test`.
   - Relationships created: `[:CONTAINS]`, `[:IMPORTS]`, `[:CALLS]`, and `[:TESTS]`.
3. The repository statistics ribbon displays:
   - **8 Python Files**
   - **15+ Extracted Symbols**
   - **5 Discovered Tests**
   - **20+ FalkorDB Relationships**

---

## Step 3: Select Target & Run Graph Impact Analysis

1. In the **Select Target Component** panel:
   - Select or search for: `authenticate_user` (`auth/security.py:18`).
   - Leave the traversal depth slider at **5 Hops**.
2. Click **Analyze Blast Radius**.
3. CodeImpact AI executes real Cypher queries on FalkorDB:
   ```cypher
   MATCH p = (caller)-[:CALLS*1..5]->(target:Symbol {name: 'authenticate_user'})
   RETURN caller.name, length(p) as hop_count, ...
   ```

---

## Step 4: Inspect Verified Impact Results

The dashboard presents the following verified facts:

### 1. Direct Dependents (1 Graph Hop)
- **`services/user_service.py::login_user()`**
  - *Relationship:* Verified `[:CALLS]` edge from `login_user` to `authenticate_user`.
  - *Impact:* Modifying the signature or return type of `authenticate_user` immediately breaks user logins.

### 2. Transitive Dependents (2+ Graph Hops)
- **`api/auth_controller.py::handle_login_request()`**
  - *Graph Path:* `handle_login_request` ➔ `login_user` ➔ `authenticate_user`
  - *Hop Distance:* 2 Hops away.
  - *Impact:* The HTTP endpoint handling API login requests will fail if login semantics change.

### 3. Potentially Affected Tests (Prioritized Recommendations)
- **`test_authenticate_user_success`** (`tests/test_auth.py`)
  - *Confidence:* **HIGH** (1 Hop)
  - *Rationale:* Directly calls and exercises `authenticate_user`.
  - *Status:* `NOT_RUN` (Must be executed before opening a PR).
- **`test_authenticate_user_invalid_password`** (`tests/test_auth.py`)
  - *Confidence:* **HIGH** (1 Hop)
  - *Rationale:* Verifies invalid password rejection.
  - *Status:* `NOT_RUN`.
- **`test_login_endpoint`** (`tests/test_api.py`)
  - *Confidence:* **MEDIUM** (3 Hops)
  - *Rationale:* Tests `handle_login_request` which transitively depends on `authenticate_user`.
  - *Status:* `NOT_RUN`.

---

## Step 5: Explore Interactive React Flow Graph

1. View the **Interactive Multi-Hop Dependency Graph**:
   - The purple target node (`authenticate_user()`) sits at the center.
   - Directed animated edges trace upstream callers.
   - Direct callers are highlighted in amber.
   - Indirect callers are styled in indigo.
   - Test suites appear in emerald green.
2. Click any node to open the **Node Inspection Modal** showing line numbers, file path, and graph distance.

---

## Step 6: Test Git Diff Blast Radius

1. Switch to the **Git Diff Blast Radius** tab.
2. Click **Load Sample Diff** (which simulates changing line 20 in `auth/security.py`).
3. Click **Analyze Diff Impact**.
4. Observe the diff analyzer mapping the changed line number to the enclosing `authenticate_user()` function and computing the combined blast radius!

---

## Step 7: Inspect Live Cypher Queries

1. Switch to the **Live Cypher Queries** tab.
2. Review the exact OpenCypher queries executed against FalkorDB, complete with execution durations in milliseconds and row counts.
