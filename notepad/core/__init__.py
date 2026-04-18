"""
Core functionality for AI Notepad.

Contains the main business logic including note management,
database operations, and AI client integration.
"""

from notepad.core.manager import NoteManager
from notepad.core.database import Database
from notepad.core.ollama_client import OllamaClient

__all__ = ["NoteManager", "Database", "OllamaClient"]
