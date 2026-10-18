# FalkorDB Graph Schema Documentation

CodeImpact AI uses **FalkorDB** as its primary graph database to model software repositories as property graphs and execute deterministic change-impact analysis using OpenCypher queries.

---

## 1. Node Labels

### `:Repository`
Represents the indexed repository root.
- `id` (STRING, unique): Stable repository identifier (e.g. `sample-auth-service`).
- `name` (STRING): Human-readable name of the repository.
- `path` (STRING): Absolute or relative filesystem path.
- `indexed_at` (FLOAT): Epoch timestamp when indexing was performed.
- `total_files` (INTEGER): Number of Python source files scanned.
- `total_symbols` (INTEGER): Total number of symbols discovered.

### `:File`
Represents an individual source code module.
- `id` (STRING, unique): Compound key `{repo_id}:{file_path}` (e.g. `sample:auth/security.py`).
- `repo_id` (STRING): Reference to parent repository.
- `path` (STRING): Relative file path from repo root (normalized with forward slashes).
- `module_name` (STRING): Python dotted module name (e.g. `auth.security`).
- `total_lines` (INTEGER): Total line count of the source file.
- `is_test` (BOOLEAN): `true` if identified as a test file (naming convention or directory).
- `language` (STRING): Source language (e.g. `python`).

### `:Symbol`
Represents executable code entities (functions, classes, and methods).
- `id` (STRING, unique): Compound key `{repo_id}:{file_path}:{name}` or `{repo_id}:{file_path}:{class}.{name}`.
- `repo_id` (STRING): Reference to parent repository.
- `name` (STRING): Identifier name (e.g. `authenticate_user`).
- `qualified_name` (STRING): Full module-qualified name (e.g. `auth.security.authenticate_user`).
- `symbol_type` (STRING): Entity classification (`function`, `class`, `method`).
- `file_path` (STRING): File containing the symbol.
- `start_line` (INTEGER): 1-based start line number in source.
- `end_line` (INTEGER): 1-based end line number in source.
- `parameters` (STRING): Comma-separated list of parameter names.
- `docstring` (STRING): Extracted docstring documentation.
- `language` (STRING): `python`.

### `:Test`
Represents an automated test function or test method.
- `id` (STRING, unique): Compound key `{repo_id}:{file_path}:{test_name}`.
- `repo_id` (STRING): Reference to parent repository.
- `name` (STRING): Test function name (e.g. `test_authenticate_user_success`).
- `qualified_name` (STRING): Dotted test name.
- `file_path` (STRING): Test file path.
- `start_line` (INTEGER): Start line number.
- `end_line` (INTEGER): End line number.
- `docstring` (STRING): Test description or docstring.
- `test_type` (STRING): Category (`unit`, `integration`).

---

## 2. Relationships

| Relationship | Source Node | Target Node | Properties | Semantics |
|---|---|---|---|---|
| `[:CONTAINS]` | `:Repository` | `:File` | - | Repository hierarchy containment |
| `[:CONTAINS]` | `:File` | `:Symbol` | - | File defines the enclosed symbol |
| `[:CONTAINS]` | `:File` | `:Test` | - | Test file defines the enclosed test |
| `[:IMPORTS]` | `:File` | `:File` | - | Source module imports from target module |
| `[:DEPENDS_ON]` | `:File` | `:File` | - | Module-level dependency link |
| `[:CALLS]` | `:Symbol` | `:Symbol` | `line` (INT) | Callee invocation within caller body |
| `[:CALLS]` | `:Test` | `:Symbol` | `line` (INT) | Test invokes function under test |
| `[:TESTS]` | `:Test` | `:Symbol` | `line` (INT) | Explicit test coverage link |

---

## 3. Real Cypher Queries Used in Impact Analysis

### Query 1: Direct Callers (1 Hop)
Discovers symbols that directly call the target function:
```cypher
MATCH (target:Symbol {id: $symbol_id})<-[:CALLS]-(caller)
RETURN caller.id, caller.name, caller.qualified_name, caller.file_path,
       caller.symbol_type, labels(caller) as caller_labels
```

### Query 2: Bounded Multi-Hop Transitive Callers (1..N Hops)
Discovers indirect callers across graph hops while avoiding infinite loops in cyclic dependencies:
```cypher
MATCH p = (caller)-[:CALLS*1..$max_hops]->(target:Symbol {id: $symbol_id})
WHERE caller <> target
RETURN caller.id, caller.name, caller.qualified_name, caller.file_path,
       coalesce(caller.symbol_type, 'test') as symbol_type,
       labels(caller) as caller_labels,
       length(p) as hop_count,
       [n in nodes(p) | {id: n.id, name: n.name, type: coalesce(n.symbol_type, 'test'), file_path: n.file_path}] as path_nodes
ORDER BY hop_count ASC
```

### Query 3: Potentially Affected Tests Discovery
Identifies tests that directly or transitively reach the target symbol:
```cypher
MATCH p = (t:Test)-[:TESTS|CALLS*1..$max_hops]->(target:Symbol {id: $symbol_id})
RETURN t.id, t.name, t.qualified_name, t.file_path, t.start_line, t.end_line,
       length(p) as hop_count,
       [n in nodes(p) | {id: n.id, name: n.name, type: coalesce(n.symbol_type, 'test')}] as path_nodes
ORDER BY hop_count ASC
```

### Query 4: Centrality and High-Impact Module Detection
Computes in-degree across the graph to identify critical shared components:
```cypher
MATCH (s:Symbol)<-[:CALLS]-(caller)
WITH s, count(caller) as in_degree
WHERE in_degree >= 1
RETURN s.id, s.name, s.file_path, in_degree
ORDER BY in_degree DESC LIMIT 5
```
