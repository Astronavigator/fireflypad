# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI-powered console notepad with vector search. Users type notes which are automatically analyzed by AI for tagging, embedded, and stored. Supports semantic search via embeddings and AI-powered retrieval.

## Tech Stack

- Python 3.12
- Poetry for dependency management
- SQLite with `sqlite-vec` extension for vector storage
- Ollama for embeddings (`nomic-embed-text:latest`) and AI chat (`gemma4:e2b`)
- `prompt-toolkit` for async CLI
- `textual` for TUI interface

## Common Commands

```bash
# Install dependencies
poetry install

# Run the simple CLI (prompt-toolkit)
poetry run python main.py

# Run the TUI version (textual, recommended)
poetry run python tui_main.py

# Run a single test file (use poetry run for proper dependencies)
poetry run python -m unittest test_ollama_client
poetry run python -m unittest test_ollama_integration
poetry run python -m unittest discover -v  # Run all tests

# CLI test tool for debugging
poetry run python test_cli.py add "Your note here"
poetry run python test_cli.py find "search query"
poetry run python test_cli.py findai "AI search query"
poetry run python test_cli.py list --limit 5
```

## Architecture

### Entry Points
- `main.py` - Simple async CLI using prompt-toolkit
- `tui_main.py` - Full TUI with split panels (main content + logs) using Textual

### Core Components

**manager.py** - `NoteManager`
- Central business logic coordinator
- Manages async queue (`asyncio.Queue`) for note processing to avoid UI blocking
- Uses `run_in_executor` for blocking operations (Ollama calls, DB writes)
- Streaming support for AI chat via `chat_stream()`

**database.py** - `Database`
- SQLite with `sqlite-vec` extension for vector search
- Thread-local connections: `_get_conn()` opens/closes per operation to avoid `ProgrammingError` with `run_in_executor`
- Virtual table `vec_notes` for KNN search using `vec0` module
- Embeddings stored as JSON arrays in the virtual table

**ollama_client.py** - `OllamaClient`
- Sync and async clients for Ollama API
- `retry_on_exception` / `async_retry_on_exception` decorators for resilience
- `analyze_note()` - AI analyzes content to extract tags and potential RAG questions
- Uses custom XML-like tags (`<result>`, `<note>`) for structured output parsing
- `extract_tag()` helper for parsing AI responses

**config.py**
- Model configuration: `EMBEDDING_MODEL`, `AI_MODEL`, `EMBEDDING_DIMENSION`

### Key Implementation Patterns

**Async Queue Processing**
Notes are processed asynchronously to avoid blocking the UI:
```python
# manager.py
await manager.add_note_async(content)  # Adds to queue
# Worker processes: AI analysis -> embedding deduplication -> DB insert
```

**6-Step Note Saving Process** (manager.py:_worker)
1. Analyze note with AI (extract tags & questions)
2. Create list of required embeddings (note, questions, tags, tag_combination)
3. Get existing embeddings from DB (text+kind unique constraint)
4. Calculate missing embeddings via Ollama
5. Insert new embeddings into DB (embeddings + vec_embeddings tables)
6. Save note and create relationships (note_embeddings + note_tags)

**SQLite Extension Loading**
Required for every connection:
```python
conn.enable_load_extension(True)
sqlite_vec.load(conn)
```

**Vector Search Query Format**
```sql
SELECT n.id, n.content, n.tags, v.distance
FROM vec_notes AS v
JOIN notes AS n ON n.id = v.rowid
WHERE v.embedding MATCH ? AND k = ?
ORDER BY v.distance ASC
```

## User Commands (Runtime)

- `$$ list [N]` - Show last N notes
- `$$ find <query>` - Semantic vector search
- `$$ findai <query>` - AI-powered search with context synthesis
- `$ <message>` - Chat with AI (uses conversation history)
- Plain text - Save as new note (AI analyzes and tags automatically)

## Testing

- Unit tests: `test_ollama_client.py` - Mocked tests for structure validation
- Integration tests: `test_ollama_integration.py` - Real Ollama calls, rate-limited with delays
- CLI tests: `test_cli.py` - Command-line interface testing tool

## Database Schema

```sql
-- Main notes table (simplified)
CREATE TABLE notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Embeddings with unique constraint on text+kind
CREATE TABLE embeddings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    text TEXT NOT NULL,
    embedding BLOB NOT NULL,  -- struct.pack format
    kind TEXT NOT NULL,  -- 'note', 'tag', 'question', 'tag_combination'
    UNIQUE(text, kind)
);

-- Virtual table for vector search
CREATE VIRTUAL TABLE vec_embeddings USING vec0(
    embedding float[{EMBEDDING_DIMENSION}]
);

-- Note-tag relationships (embedding_id points to kind='tag')
CREATE TABLE note_tags (
    note_id INTEGER NOT NULL,
    embedding_id INTEGER NOT NULL,
    PRIMARY KEY (note_id, embedding_id),
    FOREIGN KEY (note_id) REFERENCES notes(id) ON DELETE CASCADE,
    FOREIGN KEY (embedding_id) REFERENCES embeddings(id) ON DELETE CASCADE
);

-- Note-embedding relationships (all embeddings for a note)
CREATE TABLE note_embeddings (
    note_id INTEGER NOT NULL,
    embedding_id INTEGER NOT NULL,
    PRIMARY KEY (note_id, embedding_id),
    FOREIGN KEY (note_id) REFERENCES notes(id) ON DELETE CASCADE,
    FOREIGN KEY (embedding_id) REFERENCES embeddings(id) ON DELETE CASCADE
);
```

## Notes

- The `vec0.so` file is the sqlite-vec extension binary for Linux x64
- Chat history is kept in memory (last 20 messages), not persisted to DB
- AI-generated tags and questions are stored with each note for RAG retrieval
