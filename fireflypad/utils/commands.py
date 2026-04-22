#!/usr/bin/env python3
"""
Command management system for AI Notepad
Centralized command definitions and parsing logic
"""

from enum import Enum
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


class InputMode(Enum):
    """Input parsing modes"""
    COMMAND_ONLY = "command_only"      # $$ - must be a command
    COMMAND_OR_AI = "command_or_ai"    # $ - command or AI chat
    COMMAND_OR_NOTE = "command_or_note" # no prefix - command or note


@dataclass
class Command:
    """Command definition"""
    name: str
    aliases: List[str]
    description: str
    requires_arg: bool = False
    arg_description: str = ""


class CommandRegistry:
    """Centralized command registry and parser"""
    
    def __init__(self):
        self.commands: Dict[str, Command] = {}
        self._register_commands()
    
    def _register_commands(self):
        """Register all available commands"""
        
        # Database management commands
        self.register(Command(
            name="changedb",
            aliases=["db"],
            description="Change database file (creates or loads <name>.db)",
            requires_arg=False,  # Optional - lists databases if no arg
            arg_description="<database_name>"
        ))
        
        self.register(Command(
            name="export",
            aliases=[],
            description="Export all notes to file (.txt or .json format, default: .txt)",
            requires_arg=True,
            arg_description="<filename>"
        ))
        
        # Note management commands
        self.register(Command(
            name="list",
            aliases=[],
            description="Show last N notes (default: 10)",
            requires_arg=False,
            arg_description="[N]"
        ))
        
        self.register(Command(
            name="find",
            aliases=[],
            description="Search notes by content",
            requires_arg=True,
            arg_description="<query>"
        ))
        
        self.register(Command(
            name="findai",
            aliases=[],
            description="AI-powered search",
            requires_arg=True,
            arg_description="<query>"
        ))
        
        self.register(Command(
            name="del",
            aliases=["delete", "rm", "remove", "eliminar", "udalit", "udali"],
            description="Delete note by ID",
            requires_arg=True,
            arg_description="<id>"
        ))
        
        self.register(Command(
            name="cls",
            aliases=["clear", "clean"],
            description="Clear chat history",
            requires_arg=False
        ))
    
    def register(self, command: Command):
        """Register a command with all its aliases"""
        # Register main command name
        self.commands[command.name] = command
        
        # Register all aliases
        for alias in command.aliases:
            self.commands[alias] = command
    
    def get_command(self, name: str) -> Optional[Command]:
        """Get command by name or alias"""
        return self.commands.get(name)
    
    def is_command(self, name: str) -> bool:
        """Check if a name is a valid command"""
        return name in self.commands
    
    def get_all_commands(self) -> List[Command]:
        """Get all unique commands (without duplicates from aliases)"""
        seen = set()
        unique_commands = []
        
        for command in self.commands.values():
            if command.name not in seen:
                seen.add(command.name)
                unique_commands.append(command)
        
        return unique_commands
    
    def parse_input(self, input_text: str) -> Tuple[InputMode, Optional[str], Optional[str]]:
        """
        Parse user input and determine mode and command
        
        Returns:
            Tuple[mode, command_name, argument]
        """
        if not input_text:
            return InputMode.COMMAND_OR_NOTE, None, None
        
        # Strip leading whitespace for parsing
        stripped = input_text.lstrip()
        
        # Determine mode based on prefix
        if stripped.startswith("$$"):
            # Command only mode - must be a command
            mode = InputMode.COMMAND_ONLY
            remaining = stripped[2:].strip()
            
        elif stripped.startswith("$"):
            # Command or AI mode
            mode = InputMode.COMMAND_OR_AI
            remaining = stripped[1:].strip()
            
        else:
            # Command or note mode
            mode = InputMode.COMMAND_OR_NOTE
            remaining = stripped
        
        # Parse command and argument
        if not remaining:
            return mode, None, None
        
        # Split into command and argument
        parts = remaining.split(maxsplit=1)
        command_name = parts[0].lower()
        argument = parts[1] if len(parts) > 1 else None
        
        # Additional validation: only treat as command if it's actually a known command
        # This prevents treating any word as a command in command_or_note mode
        if command_name and mode == InputMode.COMMAND_OR_NOTE:
            if not self.is_command(command_name):
                # Not a known command, treat as note
                return mode, None, input_text.strip()
        
        return mode, command_name, argument
    
    def validate_command(self, command_name: str, argument: Optional[str]) -> Tuple[bool, str]:
        """
        Validate command and argument
        
        Returns:
            Tuple[is_valid, error_message]
        """
        command = self.get_command(command_name)
        
        if not command:
            return False, f"Unknown command: {command_name}"
        
        if command.requires_arg and not argument:
            return False, f"Error: {command.name} requires {command.arg_description}"
        
        return True, ""
    
    def get_help_text(self) -> str:
        """Generate help text for all commands"""
        help_lines = [
            "# AI NOTEPAD HELP ",
            "",
            "## Commands:",
        ]
        
        for command in self.get_all_commands():
            aliases_str = ""
            if command.aliases:
                aliases_str = f" (aliases: {', '.join(command.aliases)})"
            
            arg_str = ""
            if command.arg_description:
                arg_str = f" {command.arg_description}"
            
            help_lines.append(f" * {command.name}{arg_str}{aliases_str} - *{command.description}*")
        
        help_lines.extend([
            "## Notes:",
            "  Any text which is not a command will be saved as a new note.",
            "  Use $$ to force command mode. Use $ to use ai chat.",
            "## AI Chat:",
            "  $ <message>     - Chat with AI",
            "## Keybindings:",
            " * ```Ctrl+C``` - Quit",
            " * ```Ctrl+L``` - Clear log",
            " * ```Ctrl+X``` - Clear content",
            " * ```Ctrl+J``` - Show this help",
            "The log panel shows all operations and status updates.",
            "## Examples:",
            "```",
            "  $$ list         - List notes (command only mode)",
            "  list 5          - List 5 notes (command or note mode)",
            "  $ find apples   - Search for apples (command or AI mode)",
            "  $ hello         - AI chat (command or AI mode)",
            "  my note text    - Save as note (command or note mode)",
            "```"
        ])
        
        return "\n".join(help_lines)


# Global command registry instance
command_registry = CommandRegistry()
