"""
Core functionality for AI Notepad.

Contains the main business logic including note management,
database operations, and AI client integration.
"""

from fireflypad.core.manager import NoteManager
from fireflypad.core.database import Database
from fireflypad.core.ollama_client import OllamaClient

__all__ = ["NoteManager", "Database", "OllamaClient"]
