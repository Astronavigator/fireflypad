# AI Notepad

Intelligent note-taking application with vector search and AI integration.

## Features

- Smart note management with semantic search
- AI-powered chat and assistance (Ollama integration)
- Vector-based similarity search using SQLite extensions
- Terminal-based interfaces (CLI and TUI)
- Automatic embedding generation and storage

## Installation

### Development Installation

```bash
# Clone repository
git clone <repository-url>
cd notepad

# Install dependencies with Poetry
poetry install

# Run in development mode (uses local data/ folder)
export NOTEPAD_DEV=1
poetry run python -m notepad.cli.main
```

### Production Installation

```bash
# Install as package
poetry install

# Run CLI interface
poetry run notepad

# Run TUI interface  
poetry run notepad-tui
```

## Usage

### CLI Interface

```bash
# Start CLI
poetry run notepad

# Commands available in CLI:
# $$ list [limit] - List recent notes
# $$ find <query> - Search notes using vector similarity
# $$ findai <query> - AI-powered search
# $ <message> - Chat with AI
# Just type and Enter to save a note
```

### TUI Interface

```bash
# Start TUI with split-panel interface
poetry run notepad-tui
```

## Project Structure

```
notepad/
- notepad/                 # Main package
  - core/                  # Business logic
    - manager.py          # Note management
    - database.py         # Database operations
    - ollama_client.py    # AI client
  - cli/                   # Command-line interfaces
    - main.py            # CLI interface
    - tui_main.py        # TUI interface
  - tui/                   # TUI components
    - components/        # Reusable widgets
    - styles/            # CSS styling
    - themes/            # Visual themes
  - utils/                 # Utilities
    - config.py          # Configuration
    - commands.py        # Command system
    - getch.py           # Character input
- experiments/            # Experimental scripts
- data/                   # Development databases
- tests/                  # Unit tests
- docs/                   # Documentation
```

## Configuration

### Environment Variables

- `NOTEPAD_DEV=1` - Use local data/ folder (development mode)
- `OLLAMA_URL` - Ollama server URL (default: http://localhost:11434)

### AI Models

Configure in `notepad/utils/config.py`:
- `EMBEDDING_MODEL` - Model for text embeddings
- `AI_MODEL` - Chat model for AI assistance

## Data Storage

- **Development**: `data/` folder in project root
- **Production**: `~/.local/share/notepad/`

## Development

### Adding Experiments

Place experimental scripts in `experiments/` folder:

```bash
experiments/
- 01_vector_search_test.py
- 02_ollama_models.py
- README.md
```

### Testing

```bash
# Run tests (when implemented)
poetry run pytest

# Run specific experiment
poetry run python experiments/01_vector_search_test.py
```

## Dependencies

- Python 3.12+
- Poetry for dependency management
- Ollama for AI models
- SQLite with vector extensions
- Textual for TUI interface

## License

MIT License
