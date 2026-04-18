"""
Utility functions and modules for AI Notepad.

Contains helper functions, configuration management, and command system.
"""

from notepad.utils.config import DATA_DIR, NOTES_DB, ABC_DB
from notepad.utils.commands import command_registry, InputMode

__all__ = ["DATA_DIR", "NOTES_DB", "ABC_DB", "command_registry", "InputMode"]
