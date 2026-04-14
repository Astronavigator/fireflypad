#!/usr/bin/env python3
"""
TUI Notepad with split panel interface using Textual
Main panel: Notepad interface
Log panel: Operation logs, saving status, tags, etc.
"""

import asyncio
from datetime import datetime
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, ScrollableContainer
from textual.widgets import Header, Footer, Static, Input, TextArea, Log
from textual.reactive import reactive
from textual.binding import Binding
from textual.message import Message
from manager import NoteManager


class NotepadApp(App):
    """TUI Notepad App with split panels"""
    
    CSS = """
    .main-panel {
        height: 80%;
        border: solid $primary;
    }
    
    .log-panel {
        height: 20%;
        border: solid $secondary;
    }
    
    .input-area {
        height: 3;
        border: solid $accent;
    }
    
    .content-area {
        height: 1fr;
    }
    
    #header {
        text-align: center;
        background: $primary;
    }
    
    #log {
        background: $surface;
        padding: 1;
    }
    """
    
    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit"),
        Binding("ctrl+l", "clear_log", "Clear Log"),
        Binding("ctrl+h", "show_help", "Help"),
    ]
    
    current_input: reactive[str] = reactive("")
    
    def __init__(self):
        super().__init__()
        self.manager = NoteManager()
        self.chat_history = []
        self.title = "AI Notepad TUI"
    
    def compose(self) -> ComposeResult:
        """Create the app layout"""
        yield Header()
        
        with Vertical():
            # Main panel - Notepad interface
            with Vertical(classes="main-panel"):
                yield Static("=== AI NOTEPAD ===", id="header")
                with ScrollableContainer(classes="content-area"):
                    yield Static("Commands: $$ list, $$ find <query>, $$ findai <query>", id="help-text")
                    yield Static("AI Chat: $ <message>", id="help-text2") 
                    yield Static("Just type and Enter to save a note.", id="help-text3")
                    yield Static("", id="content-display")
                
                # Input area
                yield Input(placeholder="Enter note or command...", id="user-input")
            
            # Log panel - Operation logs
            with Vertical(classes="log-panel"):
                yield Static("=== LOG ===", id="log-header")
                yield Log(id="log")
        
        yield Footer()
    
    def on_mount(self) -> None:
        """Initialize the app"""
        self.log_message("AI Notepad started")
        self.log_message("Type help or press Ctrl+H for commands")
        input_widget = self.query_one("#user-input", Input)
        input_widget.focus()
    
    def log_message(self, message: str) -> None:
        """Add message to log panel"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_widget = self.query_one("#log", Log)
        log_widget.write_line(f"[{timestamp}] {message}")
    
    def update_content_display(self, content: str) -> None:
        """Update the main content display area"""
        content_widget = self.query_one("#content-display", Static)
        content_widget.update(content)
    
    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle user input submission"""
        user_input = event.value.strip()
        if not user_input:
            return
        
        self.log_message(f"Input: {user_input}")
        input_widget = self.query_one("#user-input", Input)
        input_widget.value = ""
        
        try:
            if user_input.startswith("$$"):
                await self.handle_command(user_input)
            elif user_input.startswith("$"):
                await self.handle_ai_chat(user_input)
            else:
                await self.handle_note_addition(user_input)
        except Exception as e:
            self.log_message(f"Error: {e}")
    
    async def handle_command(self, command: str) -> None:
        """Handle special commands"""
        cmd_parts = command[2:].strip().split(maxsplit=1)
        cmd = cmd_parts[0].lower()
        arg = cmd_parts[1] if len(cmd_parts) > 1 else None
        
        if cmd == "list":
            limit = int(arg) if arg and arg.isdigit() else 10
            notes = self.manager.list_notes(limit)
            self.log_message(f"Listing {len(notes)} recent notes")
            
            content = "--- Recent Notes ---\n"
            for n in notes:
                content += f"ID {n[0]}: {n[1]} (Tags: {n[2]})\n"
            content += "--------------------\n"
            self.update_content_display(content)
            
        elif cmd == "find":
            if not arg:
                self.log_message("Error: find requires a query")
                return
            results = self.manager.find_notes(arg)
            self.log_message(f"Found {len(results)} results for '{arg}'")
            
            content = "--- Vector Search Results ---\n"
            for r in results:
                dist = r[3] if len(r) > 3 else "N/A"
                dist_str = f"{dist:.4f}" if isinstance(dist, (int, float)) else dist
                content += f"ID {r[0]}: {r[1]} (Tags: {r[2]}) [Dist: {dist_str}]\n"
            content += "-----------------------------\n"
            self.update_content_display(content)
            
        elif cmd == "findai":
            if not arg:
                self.log_message("Error: findai requires a query")
                return
            self.log_message(f"AI searching for: {arg}")
            result = self.manager.find_notes_ai(arg)
            self.log_message("AI search completed")
            self.update_content_display(f"AI Result: {result}")
            
        else:
            self.log_message(f"Unknown command: {cmd}")
    
    async def handle_ai_chat(self, message: str) -> None:
        """Handle AI chat"""
        prompt = message[1:].strip()
        self.log_message(f"AI Chat: {prompt}")
        self.log_message("AI is thinking...")
        
        response = self.manager.ai_chat(prompt, self.chat_history)
        self.log_message("AI response received")
        
        content = f"User: {prompt}\nAI: {response}\n"
        self.update_content_display(content)
        
        # Add to chat history
        self.chat_history.append({'role': 'user', 'content': prompt})
        self.chat_history.append({'role': 'assistant', 'content': response})
        
        # Keep history manageable
        if len(self.chat_history) > 20:
            self.chat_history = self.chat_history[-20:]
    
    async def handle_note_addition(self, note: str) -> None:
        """Handle adding a new note"""
        self.log_message(f"Adding note: {note}")
        self.log_message("Saving...")
        
        # Show saving indicator
        self.update_content_display(f"Saving note: {note}")
        
        await self.manager.add_note_async(note)
        self.log_message("Note saved successfully")
        self.update_content_display(f"Note saved: {note}")
    
    def action_clear_log(self) -> None:
        """Clear the log panel"""
        log_widget = self.query_one("#log", Log)
        log_widget.clear()
        self.log_message("Log cleared")
    
    def action_show_help(self) -> None:
        """Show help information"""
        help_text = """
=== AI NOTEPAD HELP ===

Commands:
  $$ list [N]     - Show last N notes (default: 10)
  $$ find <query> - Search notes by content
  $$ findai <query> - AI-powered search
  $ <message>     - Chat with AI
  <note>          - Save as new note

Keybindings:
  Ctrl+C          - Quit
  Ctrl+L          - Clear log
  Ctrl+H          - Show this help

The log panel shows all operations and status updates.
"""
        self.update_content_display(help_text)
        self.log_message("Help displayed")


if __name__ == "__main__":
    app = NotepadApp()
    app.run()
