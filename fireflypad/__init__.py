"""
AI Notepad - Intelligent note-taking with vector search and AI integration.

A Python package for managing notes with semantic search capabilities
using Ollama AI models and SQLite vector extensions.
"""

__version__ = "0.1.0"
__author__ = "Astro <digital.astronavigator@gmail.com>"

from fireflypad.core.manager import NoteManager
from fireflypad.core.database import Database
from fireflypad.utils.config import DATA_DIR, NOTES_DB, ABC_DB

__all__ = [
    "NoteManager",
    "Database", 
    "DATA_DIR",
    "NOTES_DB",
    "ABC_DB"
]
