# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI-powered console notepad with vector search. Users type notes which are automatically analyzed by AI for tagging, embedded, and stored. Supports semantic search via embeddings and AI-powered retrieval. Features both CLI and advanced TUI interfaces with split-panel design.

## Tech Stack

- Python 3.12
- Poetry for dependency management
- SQLite with `sqlite-vec` extension for vector storage
- Ollama for embeddings (`my-qwen-q4`) and AI chat (`gemma4:e2b`)
- `prompt-toolkit` for async CLI
- `textual` for advanced TUI interface with split panels
- `numpy`, `scipy` for vector operations
- `termcolor`, `colorama` for terminal styling

## Common Commands

```bash
# Install dependencies
poetry install

# Run the simple CLI (prompt-toolkit)
poetry run python -m notepad.cli.main
# OR using script:
poetry run notepad

# Run the TUI version (textual, recommended)
poetry run python -m notepad.tui.tui_main
# OR using script:
poetry run notepad-tui

# Development mode (uses local data/ folder)
export NOTEPAD_DEV=1
poetry run python -m notepad.cli.main

# CLI test tool for debugging
poetry run python experiments/test_cli.py add "Your note here"
poetry run python experiments/test_cli.py find "search query"
poetry run python experiments/test_cli.py findai "AI search query"
poetry run python experiments/test_cli.py list --limit 5
```

## Architecture

### Entry Points
- `notepad/cli/main.py` - Simple async CLI using prompt-toolkit
- `notepad/tui/tui_main.py` - Full TUI with split panels (main content + logs) using Textual

### Package Structure
```
notepad/
  cli/           # Command-line interface
  core/          # Core business logic
  tui/           # Textual TUI interface
  renderers/     # UI-specific data renderers
  utils/         # Utilities and configuration
  assets/        # CSS, icons, themes
```

### Core Components

**command_handler.py** - `CommandHandler`
- Centralized business logic for all command execution
- Returns structured `CommandResult` objects instead of formatted strings
- Unified AI chat handling with streaming support via callbacks
- Clean separation between business logic and UI presentation
- Supports different result types: COMMAND_RESULT, AI_STREAM_*, ERROR, LOG

**manager.py** - `NoteManager`
- Database operations and note processing logic
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

**utils/config.py**
- Model configuration: `EMBEDDING_MODEL` (`my-qwen-q4`), `AI_MODEL` (`gemma4:e2b`), `EMBEDDING_DIMENSION` (1024)
- Data directory configuration with dev/production modes
- Database paths and Ollama URL configuration

**utils/commands.py**
- Centralized command registry and parsing system
- Support for different input modes (COMMAND_ONLY, COMMAND_OR_AI, COMMAND_OR_NOTE)
- Command definitions with aliases and argument requirements
- Extended command set including database management, export, stats, theme switching

**cli/cli_adapter.py** - `CLIAdapter`
- Adapts CommandHandler results for console display
- Uses CLIRenderer for data-to-text conversion
- Handles streaming callbacks for AI operations
- Simple adapter layer without rendering logic

**renderers/tui_renderer.py** - `TUIRenderer`
- Renders CommandHandler results as Markdown for TUI display
- Handles streaming results with proper formatting
- Converts structured data to Textual-compatible Markdown

**renderers/cli_renderer.py** - `CLIRenderer`
- Renders CommandHandler results as plain text for CLI display
- Handles streaming results with console-friendly output
- Converts structured data to terminal-compatible format

### Key Implementation Patterns

**Structured Data Architecture**
CommandHandler returns structured data, UI layers handle presentation:
```python
# command_handler.py
result = await command_handler.execute_command("list", 10)
# Returns CommandResult with data: {"notes": [...], "count": 5}

# UI layers render the data appropriately
content = tui_renderer.render_command_result(result)  # Markdown
output = cli_renderer.render_command_result(result)  # Plain text
```

**Streaming Callback System**
AI operations use unified streaming via callbacks:
```python
# command_handler.py
if self.streaming_callback:
    self.streaming_callback(CommandResult(
        type=ResultType.AI_STREAM_CHUNK,
        data={"chunk": token, "full_response": response}
    ))
```

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

### CLI Commands
- `$$ list [N]` - Show last N notes
- `$$ find <query>` - Semantic vector search
- `$$ findai <query>` - AI-powered search with context synthesis
- `$ <message>` - Chat with AI (uses conversation history)
- Plain text - Save as new note (AI analyzes and tags automatically)

### Extended Commands (TUI & CLI)
- `$$ changedb [name]` / `$$ db [name]` - Change or list databases
- `$$ export <format>` - Export notes (JSON, Markdown, etc.)
- `$$ stats` - Show database statistics
- `$$ theme <name>` - Switch TUI theme
- `$$ help` - Show available commands
- `$$ clear` - Clear screen/logs

### Input Modes
- `$$` - Command only mode
- `$` - Command or AI chat mode  
- No prefix - Command or note mode

## Testing

- Experimental tests: `experiments/test_ai_tools.py`, `experiments/embedding_research.py` - Development and research tests
- CLI tests: `experiments/test_cli.py` - Command-line interface testing tool
- Test directory: `tests/` - Currently empty, ready for structured test suite

## TUI Features

### Split Panel Interface
- **Main Panel**: Note input and display
- **Log Panel**: Operation logs, saving status, tags, AI responses
- **Rich Styling**: Custom CSS themes, syntax highlighting for AI responses
- **Async Operations**: Non-blocking UI with background processing

### TUI-Specific Commands
- Ctrl+C to exit
- Theme switching via `$$ theme`
- Real-time status indicators
- Markdown rendering for AI responses

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

## Development Notes

- **Architecture**: Clean separation between business logic (CommandHandler) and presentation (UI layers)
- **Data Flow**: CommandHandler → Structured Data → UI-specific rendering
- **Data Storage**: Uses `sqlite-vec` extension for vector operations
- **Environment**: Development mode (`NOTEPAD_DEV=1`) uses local `data/` folder, production uses `~/.local/share/notepad/`
- **Database Files**: `notes.db` (main), `abc.db` (alternative), configurable via `$$ changedb`
- **Chat History**: Kept in memory (last 20 messages), not persisted to DB
- **AI Integration**: AI-generated tags and questions stored with each note for RAG retrieval
- **Package Installation**: Poetry scripts `notepad` and `notepad-tui` provide direct command access
- **CSS Styling**: TUI themes located in `notepad/assets/css/`
- **Extensibility**: Command registry system allows easy addition of new commands
- **Streaming**: Unified streaming system works across CLI and TUI interfaces
- **Error Handling**: Centralized error reporting through CommandResult objects
