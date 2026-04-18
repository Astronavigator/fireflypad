#!/usr/bin/env python3
"""
Command Handler for AI Notepad
Centralized business logic for command execution
"""

import os
import glob
import time
import asyncio
from typing import Optional, Callable, Any
from textual.widgets import Static

from notepad.core.manager import NoteManager
from notepad.utils.config import DATA_DIR


class CommandHandler:
    """Handles all command business logic"""
    
    def __init__(self, manager: NoteManager):
        self.manager = manager
        
        # Callbacks for UI updates
        self.update_content_callback: Optional[Callable] = None
        self.log_message_callback: Optional[Callable] = None
        self.add_to_history_callback: Optional[Callable] = None
        self.clear_content_callback: Optional[Callable] = None
        self.system_prompt: str = ""
    
    def set_callbacks(self, 
                     update_content: Callable,
                     log_message: Callable,
                     add_to_history: Callable,
                     clear_content: Callable,
                     system_prompt: str):
        """Set UI callbacks"""
        self.update_content_callback = update_content
        self.log_message_callback = log_message
        self.add_to_history_callback = add_to_history
        self.clear_content_callback = clear_content
        self.system_prompt = system_prompt
    
    def tag_str(self, tags: list[str]) -> str:
        return " ".join(f" [{tag}]" for tag in tags) if tags else "none"

    def note_markdown(self, note: tuple) -> str:
        tags_str = self.tag_str(note[3])
        return f"> **\\#{note[0]}** {note[2]}\n>\n> {note[1]} \n>\n> {tags_str}\n\n"
    
    async def execute_command(self, command_name: str, argument: str = None) -> None:
        """Execute command with exact same logic as tui_main.py"""
        
        if command_name == "list":
            limit = int(argument) if argument and argument.isdigit() else 10
            notes = self.manager.list_notes(limit)
            self.log_message_callback(f"Listing {len(notes)} recent notes")
            
            content = "-----------\n"
            for n in notes:
                content += self.note_markdown(n)
            self.update_content_callback(content)
            
            # Add to chat history for AI context
            self.add_to_history_callback('assistant', f"Command 'list {limit}' executed:\n{content}")
            
        elif command_name == "find":
            results = self.manager.find_notes(argument)
            self.log_message_callback(f"Found {len(results)} results for '{argument}'")
            content = "-----------\n"
            content += f"Results of search '{argument}'\n"
            for r in results:
                dist = "N/A"
                if len(r) > 4:
                    dist = r[4]
                dist_str = f"{dist:.4f}" 
                content += f"> [{r[0]}], {r[2]} \n>\n> {r[1]} \n>\n>  {self.tag_str(r[3])} [Dist: {dist_str}]\n\n"
            self.update_content_callback(content)
            
            # Add to chat history for AI context
            self.add_to_history_callback('assistant', f"Command 'find {argument}' executed:\n{content}")
            
        elif command_name == "findai":
            # Start AI search with streaming
            self.update_content_callback(f"AI searching for: {argument}")
            
            full_response = ""
            search_response = "AI Result: "
            self.update_content_callback(search_response)
            
            async for chunk in self.manager.find_notes_ai_stream(argument):
                full_response += chunk
                # Update content display with streaming response (replace mode)
                search_response = f"AI Result: {full_response}"
                self.update_content_callback(search_response, new_widget=False)                 
            
            # Add final result to content history
            self.update_content_callback(search_response, new_widget=True)
            
            # Add to chat history for AI context
            self.add_to_history_callback('assistant', f"Command 'findai {argument}' executed:\n{search_response}")
            
        elif command_name in ["del", "delete", "rm", "remove", "eliminar", "udalit", "udali"]:
            note_id = int(argument)
            success = self.manager.delete_note(note_id)
            if success:
                content = f"Note #{note_id} deleted successfully"
                self.update_content_callback(content)
            else:
                content = f"Note #{note_id} not found"
                self.update_content_callback(content)
            
            # Add to chat history for AI context
            self.add_to_history_callback('assistant', f"Command '{command_name} {note_id}' executed:\n{content}")
            
        elif command_name in ["cls", "clear", "clean"]:
            # Clear chat history and content display but keep system prompt
            self.clear_content_callback()
            self.log_message_callback("Chat cleared (system prompt preserved)")
            
        elif command_name in ["changedb", "db"]:
            if not argument:
                # List all .db files in data directory with clickable links
                db_files = glob.glob(str(DATA_DIR / "*.db"))
                if db_files:
                    current_db = self.manager.db.db_path
                    
                    # Create header
                    self.update_content_callback("\n[green]?? Available Databases[/]\n" +\
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
                    content = f"## ?? No Database Files\n\nNo `.db` files found in `{DATA_DIR}`.\n\n**Usage:** `{command_name} <database_name>`"
                
                self.update_content_callback(content, new_widget=True, widget=Static)
                
                # Add to chat history for AI context
                self.add_to_history_callback('assistant', f"Command '{command_name}' executed:\n{content}")
                return
            
            # Add .db extension if not present
            db_name = argument if argument.endswith('.db') else f"{argument}.db"
            db_path = str(DATA_DIR / db_name)
            
            try:
                self.manager.change_database(db_path)
                content = f"?? Switched to database `{db_name}`"
                self.log_message_callback(f"Database changed to: {db_name}")
                self.update_content_callback(content)
            except Exception as e:
                content = f"?? Database Change Failed\n\n**Error:** {str(e)}\n**Attempted database:** `{db_name}`"
                self.log_message_callback(f"Failed to change database: {e}")
                self.update_content_callback(content)
            
            # Add to chat history for AI context
            self.add_to_history_callback('assistant', f"Command '{command_name} {argument}' executed:\n{content}")
            
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
                
                self.log_message_callback(f"Exported notes to: {filename}")
                content = f"Notes exported to: {filename}"
                self.update_content_callback(content)
                
                # Add to chat history for AI context
                self.add_to_history_callback('assistant', f"Command 'export {filename}' executed:\n{content}")
                
            except Exception as e:
                self.log_message_callback(f"Export error: {e}")
                content = f"Export failed: {e}"
                self.update_content_callback(content)
                
                # Add to chat history for AI context
                self.add_to_history_callback('assistant', f"Command 'export {filename}' failed:\n{content}")
