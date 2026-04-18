#!/usr/bin/env python3
"""
TUI Notepad with split panel interface using Textual
Main panel: Notepad interface
Log panel: Operation logs, saving status, tags, etc.
"""

import asyncio
import os
import time
from datetime import datetime
from pathlib import Path

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, ScrollableContainer, Vertical
from textual.message import Message
from textual.reactive import reactive
from textual.widgets import Footer, Header, Input, Log, Markdown, Static

from notepad.core.manager import NoteManager
from notepad.core.command_handler import CommandHandler
from notepad.utils.commands import command_registry, InputMode
from notepad.renderers import TUIRenderer

# Unused function - can be removed if not needed
# async def fake_stream(self):
#     for i in range(10):
#         await asyncio.sleep(0.5) # Имитация ожидания
#         yield f"Токен {i} "

from rich.style import Style

class ChatMarkdown(Markdown):
    DEFAULT_CSS = """
    .strong {
      color: #ebae87;
      text-style: bold;
    }
    """


class NotepadApp(App):
    """TUI Notepad App with split panels"""
    
    def __init__(self):
        super().__init__()
        
        # Load CSS from file
        css_path = Path(__file__).parent.parent / "assets" / "css" / "tui_styles.tcss"
        if css_path.exists():
            with open(css_path, 'r', encoding='utf-8') as f:
                self.CSS = f.read()
        else:
            # Fallback CSS if file doesn't exist
            self.CSS = """
            .main-panel {
                width: 70%;
                height: 1fr;
                border: solid $primary;
            }
            .log-panel {
                width: 30%;
                height: 1fr;
                border: solid $secondary;
            }
            """
        
        # Load system prompt from file
        prompt_path = Path(__file__).parent.parent / "assets" / "prompts" / "system_prompt.md"
        if prompt_path.exists():
            with open(prompt_path, 'r', encoding='utf-8') as f:
                self.system_prompt = f.read().strip()
        else:
            # Fallback system prompt
            self.system_prompt = "You are an AI assistant integrated into an intelligent notepad."
        
        self.manager = NoteManager()
        self.manager.set_log_callback(self._ai_log_callback)
        
        # Initialize renderer
        self.renderer = TUIRenderer()
        
        # Initialize command handler with callbacks
        self.command_handler = CommandHandler(self.manager)
        self.command_handler.set_callbacks(
            update_content=self._handle_content_update,
            log_message=self.log_message,
            add_to_history=self._add_to_chat_history,
            clear_content=self._clear_chat_and_content,
            streaming=self._handle_streaming_result,
            system_prompt=self.system_prompt
        )
        
        # Initialize chat history with system prompt
        self.chat_history = [{'role': 'system', 'content': self.system_prompt}]
        self.title = "AI Notepad TUI"
        self.content_history = []
    
    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit"),
        Binding("ctrl+l", "clear_log", "Clear Log"),
        Binding("ctrl+k", "clear_content", "Clear Content"),
        Binding("ctrl+h", "show_help", "Help"),
    ]
    
    current_input: reactive[str] = reactive("")
    
    
    def action_notify(self, string):
        self.notify(string)

    def compose(self) -> ComposeResult:
        """Create the app layout"""
        yield Header()
        
        with Horizontal():
            # Main panel - Notepad interface (left)
            with Vertical(classes="main-panel"):
                yield Static("=== AI NOTEPAD ===", id="header")
                with ScrollableContainer(classes="content-area"):
                    # yield Static(" [b]test[/b] *abc* [@click=app.hello_world('test')]Click me[/]")
                    yield Static("Commands: list, find <query>, findai <query>, del <id>, changedb <name>, db <name>, export <file>, cls", id="help-text")
                    yield Static("AI Chat: $ <message>", id="help-text2") 
                    yield Static("Notes: just type any text | Prefix with $$ for command-only mode", id="help-text3")
                    yield Vertical(id="content-display", classes="message-container")

                # Input area
                yield Input(placeholder="Enter note or command...", id="user-input")
            
            # Log panel - Operation logs (right)
            with Vertical(classes="log-panel"):
                yield Static("=== LOG ===", id="log-header")
                with ScrollableContainer(classes="log-content"):
                    yield Static("", id="log")
        
        yield Footer()
    
    def on_mount(self) -> None:
        """Initialize the app"""
        self.log_message("AI Notepad started")
        self.log_message("Type help or press Ctrl+H for commands")
        input_widget = self.query_one("#user-input", Input)
        input_widget.focus()
    
    def log_message(self, message: str, new_line: bool = True) -> None:
        """Add message to log panel"""
        if new_line:
            timestamp = datetime.now().strftime("%H:%M:%S")
            log_widget = self.query_one("#log", Static)

            #log_widget.write(f"[{timestamp}] {message}")
            current_text = log_widget.renderable
            log_widget.update(f"{current_text}\n[{timestamp}] {message}")
        else:
            log_widget = self.query_one("#log", Static)
            #log_widget.write(message)
            current_text = log_widget.renderable
            log_widget.update(f"{current_text}{message}")
    
    def _handle_content_update(self, result) -> None:
        """Handle content update from CommandHandler"""
        # For now, keep the old interface for compatibility
        # This will be replaced with proper data rendering
        pass
    
    def _handle_streaming_result(self, result) -> None:
        """Handle streaming results from CommandHandler"""
        content = self.renderer.render_streaming_result(result)
        if content:
            # Determine if this should replace or add new content
            is_chunk = result.type.value == "ai_stream_chunk"
            self.update_content_display(content, new_widget=not is_chunk)
    

    def _ai_log_callback(self, message: str, is_chunk: bool = False) -> None:
        """Callback for AI operations logging"""
        if is_chunk:
            # For streaming chunks, log them directly to show AI thinking process
            log_widget = self.query_one("#log", Static)
            # Add chunks without overwhelming the log
            if len(message.strip()) > 0:  # Only log non-empty chunks
                current_text = log_widget.renderable
                log_widget.update(f"{current_text}{message}")
        else:
            # For regular messages, use normal logging with timestamp
            self.log_message(f"AI: {message}")
    
    def update_content_display(self, content: str, new_widget: bool = True, widget = ChatMarkdown) -> None:
        """Add content to the main content display area"""
        container = self.query_one("#content-display", Vertical)
        
        if new_widget:
            # Добавляем новое сообщение как отдельный виджет
            message_widget = widget(content, classes="message")
            container.mount(message_widget)
            self.content_history.append(content)
        else:
            # Заменяем последнее сообщение
            if container.children:
                container.children[-1].update(content)
            else:
                container.mount(ChatMarkdown(content, classes="message"))
            
            if self.content_history:
                self.content_history[-1] = content
            else:
                self.content_history.append(content)
        
        # Ограничиваем количество сообщений
        if len(container.children) > 50:
            # Удаляем самые старые сообщения
            for child in container.children[:-50]:
                child.remove()
            self.content_history = self.content_history[-50:]
        
        # Auto-scroll to bottom
        self.call_after_refresh(self._scroll_to_bottom)
    
    async def _scroll_to_bottom(self) -> None:
        """Scroll the content area to the bottom"""
        try:
            # Get the scrollable container and scroll to end
            scroll_container = self.query_one(".content-area", ScrollableContainer)
            await asyncio.sleep(0.1)
            scroll_container.scroll_end(animate=False)

        except Exception as e:
            self.log_message(f"Scroll error: {e}")
    
    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle user input submission"""
        self.run_worker(self.do_on_input_submitted(event), exclusive=True)
    
    async def do_on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle user input submission with new parsing logic"""
        user_input = event.value
        if not user_input:
            return
        
        self.log_message(f"Input: {user_input}")
        input_widget = self.query_one("#user-input", Input)
        input_widget.value = ""
        
        try:
            # Parse input using command registry
            mode, command_name, argument = command_registry.parse_input(user_input)
            
            if mode == InputMode.COMMAND_ONLY:
                # $$ prefix - must be a command
                if command_name:
                    is_valid, error_msg = command_registry.validate_command(command_name, argument)
                    if is_valid:
                        await self.handle_command(command_name, argument)
                    else:
                        self.log_message(error_msg)
                        self.update_content_display(f"Error: {error_msg}")
                else:
                    self.log_message("Error: $$ requires a command")
                    self.update_content_display("Error: $$ requires a command")
            
            elif mode == InputMode.COMMAND_OR_AI:
                # $ prefix - command or AI chat
                if command_name and command_registry.is_command(command_name):
                    # It's a command
                    is_valid, error_msg = command_registry.validate_command(command_name, argument)
                    if is_valid:
                        await self.handle_command(command_name, argument)
                    else:
                        self.log_message(error_msg)
                        self.update_content_display(f"Error: {error_msg}")
                else:
                    # It's AI chat
                    await self.handle_ai_chat(user_input)
            
            elif mode == InputMode.COMMAND_OR_NOTE:
                # No prefix - command or note
                if command_name and command_registry.is_command(command_name):
                    # It's a command
                    is_valid, error_msg = command_registry.validate_command(command_name, argument)
                    if is_valid:
                        await self.handle_command(command_name, argument)
                    else:
                        self.log_message(error_msg)
                        self.update_content_display(f"Error: {error_msg}")
                else:
                    # It's a note
                    await self.handle_note_addition(user_input)
            
        except Exception as e:
            self.log_message(f"Error!: {e}")
            import traceback
            self.log_message(traceback.format_exc())

    def _add_to_chat_history(self, role: str, content: str) -> None:
        """Add message to chat history"""
        self.chat_history.append({'role': role, 'content': content})
        
        # Keep history manageable (increased to account for command outputs)
        if len(self.chat_history) > 50:
            # Keep system prompt and last 49 messages
            system_msg = self.chat_history[0] if self.chat_history[0]['role'] == 'system' else None
            self.chat_history = self.chat_history[-49:]
            if system_msg:
                self.chat_history.insert(0, system_msg)
    
    def _clear_chat_and_content(self) -> None:
        """Clear chat history and content display but keep system prompt"""
        self.chat_history = [{'role': 'system', 'content': self.system_prompt}]
        self.action_clear_content()
    
    
    async def handle_command(self, command_name: str, argument: str = None) -> None:
        """Handle commands using command registry - delegates to CommandHandler"""
        result = await self.command_handler.execute_command(command_name, argument)
        
        # Render the result for display
        if result.type.value == "command_result":
            content = self.renderer.render_command_result(result)
            self.update_content_display(content)
            
            # Add to chat history for AI context
            self._add_to_chat_history('assistant', f"Command '{command_name} {argument or ''}' executed:\n{content}")
        elif result.type.value == "error":
            self.update_content_display(f"**Error:** {result.message}")
            self.log_message(f"Command error: {result.message}")
    
    async def handle_ai_chat(self, message: str) -> None:
        """Handle AI chat - now delegates to CommandHandler"""
        await self.command_handler.handle_ai_chat(message, self.chat_history)
    
    async def handle_note_addition(self, note: str) -> None:
        """Handle adding a new note"""
        self.log_message(f"Adding note: {note}")
        self.log_message("Saving...")
        
        # Show saving indicator
        self.update_content_display(f"Saving note: {note}")
        
        await self.manager.add_note_async(note)
        self.log_message("Note saved successfully")
        content = f"Note saved: {note}"
        self.update_content_display(content)
        
        # Add to chat history for AI context using callback
        self._add_to_chat_history('assistant', f"Note added:\n{content}")
        
        # Also log the AI analysis that happened during saving
        # This will be shown through the callback we set
    
    def action_clear_log(self) -> None:
        """Clear the log panel"""
        log_widget = self.query_one("#log", Log)
        log_widget.clear()
        self.log_message("Log cleared")
    
    def action_clear_content(self) -> None:
        """Clear the content panel"""
        self.content_history.clear()
        container = self.query_one("#content-display", Vertical)
        container.remove_children()
        self.log_message("Content cleared")
    
    def action_show_help(self) -> None:
        """Show help information using command registry"""
        help_text = command_registry.get_help_text()
        self.update_content_display(help_text)
        self.log_message("Help displayed")
    
    def action_change_database(self, db_name: str) -> None:
        """Handle database change from clickable links"""
        # Simulate command input
        self.run_worker(self.handle_command("changedb", db_name), exclusive=True)


def main():
    """Main entry point for TUI application"""
    app = NotepadApp()
    app.run()

if __name__ == "__main__":
    main()
