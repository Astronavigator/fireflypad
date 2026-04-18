# Project Summary: AI Notepad

## Core Functionality
- Console-based notepad with an editable input field.
- Async saving queue: Notes are processed in a background worker to avoid UI blocking.
- AI Integration (Ollama):
    - Embeddings: `nomic-embed-text:latest`
    - AI Chat/Analysis: `kimi-k2.5:cloud`
    - Automatic tagging during the saving process.
- Vector Search: Semantic retrieval using `sqlite-vec`.

## Technical Stack
- Language: Python 3.12
- Package Manager: Poetry
- Database: SQLite with `sqlite-vec` extension.
- UI: `prompt-toolkit` for async console interaction.

## Critical Implementation Details (Key Takeaways)

### 1. SQLite Extension Loading
The `sqlite-vec` extension must be loaded for every connection. 
Correct sequence: 
`conn.enable_load_extension(True)` -> `sqlite_vec.load(conn)`.

### 2. Vector Storage & Search
- **Storage**: Vectors are stored as `BLOB`s in a standard table (not a virtual table).
- **Conversion**: Python lists of floats MUST be converted to bytes using `struct.pack(f"{len(embedding)}f", *embedding)`.
- **Search**: To avoid the "vec0 knn queries" error (which requires a strict `LIMIT` or `k=X` constraint), we use a linear scan with the scalar function `vec_distance_l2(embedding, query_blob)`. This is reliable and performant for small to medium datasets.

### 3. Async & Threading
- **SQLite Threading**: SQLite connections are thread-local. The `Database` class implements a `_get_conn()` method to open/close connections per operation, allowing `run_in_executor` to work without `ProgrammingError`.
- **Event Loop**: All blocking AI (Ollama) and DB calls are wrapped in `await loop.run_in_executor(None, ...)` to prevent the `prompt-toolkit` UI from freezing.

## Commands Reference
- `$$ list [n]` - Show last n notes.
- `$$ find "query"` - Semantic vector search.
- `$$ findai "query"` - AI-powered retrieval and synthesis.
- `$ message` - AI Chat with conversational history.
