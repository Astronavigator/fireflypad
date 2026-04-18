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
from notepad.utils.commands import command_registry, InputMode

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

    def tag_str(self, tags: list[str]) -> str:
        return " ".join(f" [{tag}]" for tag in tags) if tags else "none"

    def note_markdown(self, note: tuple) -> str:
        tags_str = self.tag_str(note[3])
        return f"> **\\#{note[0]}** {note[2]}\n>\n> {note[1]} \n>\n> {tags_str}\n\n"

    async def handle_command(self, command_name: str, argument: str = None) -> None:
        """Handle commands using command registry"""
        
        if command_name == "list":
            limit = int(argument) if argument and argument.isdigit() else 10
            notes = self.manager.list_notes(limit)
            self.log_message(f"Listing {len(notes)} recent notes")
            
            content = "-----------\n"
            for n in notes:
                content += self.note_markdown(n)
            self.update_content_display(content)
            
            # Add to chat history for AI context
            self.chat_history.append({'role': 'assistant', 'content': f"Command 'list {limit}' executed:\n{content}"})
            
        elif command_name == "find":
            results = self.manager.find_notes(argument)
            self.log_message(f"Found {len(results)} results for '{argument}'")
            content = "-----------\n"
            content += f"Results of search '{argument}'\n"
            for r in results:
                dist = "N/A"
                if len(r) > 4:
                    dist = r[4]
                dist_str = f"{dist:.4f}" 
                content += f"> [{r[0]}], {r[2]} \n>\n> {r[1]} \n>\n>  {self.tag_str(r[3])} [Dist: {dist_str}]\n\n"
            self.update_content_display(content)
            
            # Add to chat history for AI context
            self.chat_history.append({'role': 'assistant', 'content': f"Command 'find {argument}' executed:\n{content}"})
            
        elif command_name == "findai":
            # Start AI search with streaming
            self.update_content_display(f"AI searching for: {argument}")
            
            full_response = ""
            search_response = "AI Result: "
            self.update_content_display(search_response)
            
            async for chunk in self.manager.find_notes_ai_stream(argument):
                full_response += chunk
                # Update content display with streaming response (replace mode)
                search_response = f"AI Result: {full_response}"
                self.update_content_display(search_response, new_widget=False)                 
            
            # Add final result to content history
            self.update_content_display(search_response, new_widget=True)
            
            # Add to chat history for AI context
            self.chat_history.append({'role': 'assistant', 'content': f"Command 'findai {argument}' executed:\n{search_response}"})
            
        elif command_name in ["del", "delete", "rm", "remove", "eliminar", "udalit", "udali"]:
            note_id = int(argument)
            success = self.manager.delete_note(note_id)
            if success:
                content = f"Note #{note_id} deleted successfully"
                self.update_content_display(content)
            else:
                content = f"Note #{note_id} not found"
                self.update_content_display(content)
            
            # Add to chat history for AI context
            self.chat_history.append({'role': 'assistant', 'content': f"Command '{command_name} {note_id}' executed:\n{content}"})
            
        elif command_name in ["cls", "clear", "clean"]:
            # Clear chat history and content display but keep system prompt
            self.chat_history = [{'role': 'system', 'content': self.system_prompt}]
            self.action_clear_content()
            self.log_message("Chat cleared (system prompt preserved)")
            
        elif command_name in ["changedb", "db"]:
            if not argument:
                # List all .db files in data directory with clickable links
                import os
                import glob
                from notepad.utils.config import DATA_DIR
                
                db_files = glob.glob(str(DATA_DIR / "*.db"))
                if db_files:
                    current_db = self.manager.db.db_path
                    
                    # Create header
                    self.update_content_display("\n[green]📁 Available Databases[/]\n" +\
                        f"[b]Location:[/] `{DATA_DIR}`\n" +\
                        f"[b]Current database:[/] `{os.path.basename(current_db)}`\n",
                        new_widget=True, widget=Static
                    )
                    db_strs = []
                    
                    # Add clickable database files
                    for db_file in sorted(db_files):
                        db_name = os.path.basename(db_file)
                        is_current = os.path.abspath(db_file) == current_db
                        
                        if is_current:
                            db_strs.append(f"[b green]{db_name}[b]")
                        else:
                            # Make it clickable
                            clickable_db = f"[@click=app.change_database('{db_name}')]{db_name}[/]"
                            db_strs.append(clickable_db)
                                        
                    content = " ".join(db_strs) + "\n"
                else:
                    content = f"## 📭 No Database Files\n\nNo `.db` files found in `{DATA_DIR}`.\n\n**Usage:** `{command_name} <database_name>`"
                
                self.update_content_display(content, new_widget=True, widget=Static)
                
                # Add to chat history for AI context
                self.chat_history.append({'role': 'assistant', 'content': f"Command '{command_name}' executed:\n{content}"})
                return
            
            # Add .db extension if not present
            from notepad.utils.config import DATA_DIR
            db_name = argument if argument.endswith('.db') else f"{argument}.db"
            db_path = str(DATA_DIR / db_name)
            
            try:
                self.manager.change_database(db_path)
                content = f"✅ Switched to database `{db_name}`"
                self.log_message(f"Database changed to: {db_name}")
                self.update_content_display(content)
            except Exception as e:
                content = f"❌ Database Change Failed\n\n**Error:** {str(e)}\n**Attempted database:** `{db_name}`"
                self.log_message(f"Failed to change database: {e}")
                self.update_content_display(content)
            
            # Add to chat history for AI context
            self.chat_history.append({'role': 'assistant', 'content': f"Command '{command_name} {argument}' executed:\n{content}"})
            
        elif command_name == "export":
            filename = argument
            try:
                # Determine format based on file extension
                if filename.endswith('.json'):
                    export_content = self.manager.export_notes_json()
                else:
                    # Default to text format
                    export_content = self.manager.export_notes_text()
                    if not filename.endswith('.txt'):
                        filename = f"{filename}.txt"
                
                # Write to file
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(export_content)
                
                self.log_message(f"Exported notes to: {filename}")
                content = f"Notes exported to: {filename}"
                self.update_content_display(content)
                
                # Add to chat history for AI context
                self.chat_history.append({'role': 'assistant', 'content': f"Command 'export {filename}' executed:\n{content}"})
                
            except Exception as e:
                self.log_message(f"Export error: {e}")
                content = f"Export failed: {e}"
                self.update_content_display(content)
                
                # Add to chat history for AI context
                self.chat_history.append({'role': 'assistant', 'content': f"Command 'export {filename}' failed:\n{content}"})

    
    async def handle_ai_chat(self, message: str) -> None:
        """Handle AI chat with streaming"""
        # Remove $ prefix if present
        if message.startswith("$"):
            prompt = message[1:].strip()
        else:
            prompt = message.strip()
        
        self.log_message(f"AI Chat: {prompt}")
        
        # Add user message to content display
        self.update_content_display(f"**User:** {prompt}")
        
        # Start AI response with streaming
        ai_response = "**AI:**"
        self.update_content_display(ai_response)
        
        full_response = ""

        # try not to update too fast
        last_update_time = 0
        async for chunk in self.manager.ai_chat_stream(prompt, self.chat_history):
            full_response += chunk
            # Update content display with streaming response (replace mode)
            ai_response = f"**AI:** {full_response}"
            if time.time() - last_update_time > 0.1:
                self.update_content_display(ai_response, new_widget=False)
                last_update_time = time.time()
            #self.update_content_display(chunk, append=True)
            await asyncio.sleep(0)
            
        
        # Add final message to content history
        self.update_content_display(ai_response, new_widget=False)
        
        # Add to chat history
        self.chat_history.append({'role': 'user', 'content': prompt})
        self.chat_history.append({'role': 'assistant', 'content': full_response})
        
        # Keep history manageable (increased to account for command outputs)
        if len(self.chat_history) > 50:
            # Keep system prompt and last 49 messages
            system_msg = self.chat_history[0] if self.chat_history[0]['role'] == 'system' else None
            self.chat_history = self.chat_history[-49:]
            if system_msg:
                self.chat_history.insert(0, system_msg)
    
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
        
        # Add to chat history for AI context
        self.chat_history.append({'role': 'assistant', 'content': f"Note added:\n{content}"})
        
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
