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
from textual.widgets import Markdown, MarkdownViewer
from manager import NoteManager
import time

async def fake_stream(self):
    for i in range(10):
        await asyncio.sleep(0.5) # Имитация ожидания
        yield f"Токен {i} "

class NotepadApp(App):
    """TUI Notepad App with split panels"""
    
    CSS = """
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

    .log-content {
      text-style: italic;
    }
    
    .input-area {
        height: 3;
        border: solid $accent;
    }
    
    .content-area {
        height: 1fr;
    }
    
    .message-container {
        height: auto;       /* Позволяет контейнеру расти вниз */
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
        Binding("ctrl+k", "clear_content", "Clear Content"),
        Binding("ctrl+h", "show_help", "Help"),
    ]
    
    current_input: reactive[str] = reactive("")
    
    def __init__(self):
        super().__init__()
        self.manager = NoteManager()
        self.manager.set_log_callback(self._ai_log_callback)
        self.chat_history = []
        self.title = "AI Notepad TUI"
        self.content_history = []
    
    def compose(self) -> ComposeResult:
        """Create the app layout"""
        yield Header()
        
        with Horizontal():
            # Main panel - Notepad interface (left)
            with Vertical(classes="main-panel"):
                yield Static("=== AI NOTEPAD ===", id="header")
                with ScrollableContainer(classes="content-area"):
                    yield Static("Commands: $$ list, $$ find <query>, $$ findai <query>", id="help-text")
                    yield Static("AI Chat: $ <message>", id="help-text2") 
                    yield Static("Just type and Enter to save a note.", id="help-text3")
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
    
    def update_content_display(self, content: str, append: bool = True) -> None:
        """Add content to the main content display area"""
        container = self.query_one("#content-display", Vertical)
        
        if append:
            # Добавляем новое сообщение как отдельный виджет
            message_widget = Markdown(content, classes="message")
            container.mount(message_widget)
            self.content_history.append(content)
        else:
            # Заменяем последнее сообщение
            if container.children:
                container.children[-1].update(content)
            else:
                container.mount(Markdown(content, classes="message"))
            
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
    
    def _scroll_to_bottom(self) -> None:
        """Scroll the content area to the bottom"""
        try:
            # Get the scrollable container and scroll to end
            scroll_container = self.query_one(".content-area", ScrollableContainer)
            scroll_container.scroll_end(animate=False)
        except Exception as e:
            self.log_message(f"Scroll error: {e}")
    
    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle user input submission"""
        self.run_worker(self.do_on_input_submitted(event), exclusive=True)
    
    async def do_on_input_submitted(self, event: Input.Submitted) -> None:
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
            self.log_message(f"Error!: {e}")
            import traceback
            self.log_message(traceback.format_exc())

    def tag_str(self, tags: list[str]) -> str:
        return " ".join(f" [{tag}]" for tag in tags) if tags else "none"

    def note_markdown(self, note: tuple) -> str:
        tags_str = self.tag_str(note[3])
        return f"> **\\#{note[0]}** {note[2]}\n>\n> {note[1]} \n>\n> {tags_str}\n\n"

    async def handle_command(self, command: str) -> None:
        """Handle special commands"""
        cmd_parts = command[2:].strip().split(maxsplit=1)
        cmd = cmd_parts[0].lower()
        arg = cmd_parts[1] if len(cmd_parts) > 1 else None
        
        if cmd == "list":
            limit = int(arg) if arg and arg.isdigit() else 10
            notes = self.manager.list_notes(limit)
            self.log_message(f"Listing {len(notes)} recent notes")
            
            content = "-----------\n"
            for n in notes:
                content += self.note_markdown(n)
            self.update_content_display(content)
            
        elif cmd == "find":
            if not arg:
                self.log_message("Error: find requires a query")
                return
            results = self.manager.find_notes(arg)
            self.log_message(f"Found {len(results)} results for '{arg}'")
            content = "-----------\n"
            content += f"Резульаты поиска '{arg}'\n"
            for r in results:
                dist = "N/A"
                if len(r) > 4:
                    dist = r[4]
                dist_str = f"{dist:.4f}" 
                content += f"> [{r[0]}], {r[2]} \n>\n> {r[1]} \n>\n>  {self.tag_str(r[3])} [Dist: {dist_str}]\n\n"
            self.update_content_display(content)
            
        elif cmd == "findai":
            if not arg:
                self.log_message("Error: findai requires a query")
                return
            
            # Start AI search with streaming
            self.update_content_display(f"AI searching for: {arg}")
            
            full_response = ""
            search_response = "AI Result: "
            self.update_content_display(search_response)
            
            async for chunk in self.manager.find_notes_ai_stream(arg):
                full_response += chunk
                # Update content display with streaming response (replace mode)
                search_response = f"AI Result: {full_response}"
                self.update_content_display(search_response, append=False)                 
            
            # Add final result to content history
            self.update_content_display(search_response, append=True)
            
        else:
            self.log_message(f"Unknown command: {cmd}")
    
    async def handle_ai_chat(self, message: str) -> None:
        """Handle AI chat with streaming"""
        prompt = message[1:].strip()
        self.log_message(f"AI Chat: {prompt}")
        
        # Add user message to content display
        self.update_content_display(f"User: {prompt}")
        
        # Start AI response with streaming
        ai_response = "AI: "
        self.update_content_display(ai_response)
        
        full_response = ""

        # try not to update too fast
        last_update_time = 0
        async for chunk in self.manager.ai_chat_stream(prompt, self.chat_history):
            full_response += chunk
            # Update content display with streaming response (replace mode)
            ai_response = f"AI: {full_response}"
            if time.time() - last_update_time > 0.1:
                self.update_content_display(ai_response, append=False)
                last_update_time = time.time()
            #self.update_content_display(chunk, append=True)
            await asyncio.sleep(0)
            
        
        # Add final message to content history
        self.update_content_display(ai_response, append=False)
        
        # Add to chat history
        self.chat_history.append({'role': 'user', 'content': prompt})
        self.chat_history.append({'role': 'assistant', 'content': full_response})
        
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
  Ctrl+K          - Clear content
  Ctrl+H          - Show this help

The log panel shows all operations and status updates.
"""
        self.update_content_display(help_text)
        self.log_message("Help displayed")


if __name__ == "__main__":
    app = NotepadApp()
    app.run()
