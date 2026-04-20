#!/usr/bin/env python3
"""
Command Handler for AI Notepad
Centralized business logic for command execution
"""

import os
import glob
import time
import asyncio
from typing import Optional, Callable, Any, Dict, List, Union
from dataclasses import dataclass
from enum import Enum

from notepad.core.manager import NoteManager
from notepad.utils.config import DATA_DIR


class ResultType(Enum):
    """Types of command results"""
    COMMAND_RESULT = "command_result"
    AI_STREAM_START = "ai_stream_start"
    AI_STREAM_CHUNK = "ai_stream_chunk"
    AI_STREAM_END = "ai_stream_end"
    ERROR = "error"
    LOG = "log"

@dataclass
class CommandResult:
    """Structured result from command execution"""
    type: ResultType
    command: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    message: Optional[str] = None
    stream_id: Optional[str] = None

    def to_string(self) -> str:
        return f"<{self.command}> data: {str(self.data)}, message: {self.message}"


class CommandHandler:
    """Handles all command business logic"""
    
    def __init__(self, manager: NoteManager):
        self.manager = manager
        
        # Callbacks for UI updates
        self.update_content_callback: Optional[Callable] = None
        self.log_message_callback: Optional[Callable] = None
        self.add_to_history_callback: Optional[Callable] = None
        self.clear_content_callback: Optional[Callable] = None
        self.streaming_callback: Optional[Callable] = None
        self.system_prompt: str = ""
    
    def set_callbacks(self, 
                     update_content: Callable,
                     log_message: Callable,
                     add_to_history: Callable,
                     clear_content: Callable,
                     streaming: Callable,
                     system_prompt: str):
        """Set UI callbacks"""
        self.update_content_callback = update_content
        self.log_message_callback = log_message
        self.add_to_history_callback = add_to_history
        self.clear_content_callback = clear_content
        self.streaming_callback = streaming
        self.system_prompt = system_prompt
    
    def tag_str(self, tags: list[str]) -> str:
        return " ".join(f" [{tag}]" for tag in tags) if tags else "none"

    def note_to_dict(self, note: tuple) -> Dict[str, Any]:
        """Convert note tuple to dictionary"""
        return {
            "id": note[0],
            "content": note[1],
            "title": note[2],
            "tags": note[3] if len(note) > 3 else [],
            "distance": note[4] if len(note) > 4 else None,
            "created_at": note[5] if len(note) > 5 else None
        }

    def note_markdown(self, note: tuple) -> str:
        tags_str = self.tag_str(note[3])
        return f"> **\\#{note[0]}** {note[2]}\n>\n> {note[1]} \n>\n> {tags_str}\n\n"
    
    async def handle_ai_chat(self, message: str, chat_history: List[Dict[str, str]] = None) -> None:
        """Handle AI chat with streaming - unified for all interfaces"""
        if chat_history is None:
            chat_history = []
            
        # Remove $ prefix if present
        if message.startswith("$"):
            prompt = message[1:].strip()
        else:
            prompt = message.strip()
        
        # Notify start of AI response
        stream_id = f"ai_chat_{int(time.time())}"
        if self.streaming_callback:
            self.streaming_callback(CommandResult(
                type=ResultType.AI_STREAM_START,
                data={"prompt": prompt},
                stream_id=stream_id
            ))
        
        # Add user message to history
        if self.add_to_history_callback:
            self.add_to_history_callback('user', prompt)
        
        full_response = ""
        last_update_time = 0
        
        try:
            async for chunk in self.manager.ai_chat_stream(prompt, chat_history):
                full_response += chunk
                
                # Send streaming chunk
                if self.streaming_callback and time.time() - last_update_time > 0.1:
                    self.streaming_callback(CommandResult(
                        type=ResultType.AI_STREAM_CHUNK,
                        data={"chunk": chunk, "full_response": full_response},
                        stream_id=stream_id
                    ))
                    last_update_time = time.time()
                
                await asyncio.sleep(0)
            
            # Send final result
            if self.streaming_callback:
                self.streaming_callback(CommandResult(
                    type=ResultType.AI_STREAM_END,
                    data={"full_response": full_response},
                    stream_id=stream_id
                ))
            
            # Add to chat history
            if self.add_to_history_callback:
                self.add_to_history_callback('assistant', full_response)
                
        except Exception as e:
            if self.streaming_callback:
                self.streaming_callback(CommandResult(
                    type=ResultType.ERROR,
                    message=f"AI chat error: {str(e)}",
                    stream_id=stream_id
                ))

    async def execute_command(self, command_name: str, argument: str = None) -> CommandResult:
        """Execute command and return structured result"""
        
        if command_name == "list":
            limit = int(argument) if argument and argument.isdigit() else 10
            notes = self.manager.list_notes(limit)
            
            if self.log_message_callback:
                self.log_message_callback(f"Listing {len(notes)} recent notes")
            
            return CommandResult(
                type=ResultType.COMMAND_RESULT,
                command="list",
                data={
                    "notes": [self.note_to_dict(note) for note in notes],
                    "count": len(notes),
                    "limit": limit
                }
            )
            
        elif command_name == "find":
            results = self.manager.find_notes(argument)
            
            if self.log_message_callback:
                self.log_message_callback(f"Found {len(results)} results for '{argument}'")
            
            return CommandResult(
                type=ResultType.COMMAND_RESULT,
                command="find",
                data={
                    "query": argument,
                    "results": [self.note_to_dict(result) for result in results],
                    "count": len(results)
                }
            )
            
        elif command_name == "findai":
            # Start AI search with streaming
            if self.log_message_callback:
                self.log_message_callback(f"AI searching for: {argument}")
            
            stream_id = f"findai_{int(time.time())}"
            full_response = ""
            
            if self.streaming_callback:
                self.streaming_callback(CommandResult(
                    type=ResultType.AI_STREAM_START,
                    data={"query": argument, "type": "search"},
                    stream_id=stream_id
                ))
            
            try:
                async for chunk in self.manager.find_notes_ai_stream(argument):
                    full_response += chunk
                    
                    if self.streaming_callback:
                        self.streaming_callback(CommandResult(
                            type=ResultType.AI_STREAM_CHUNK,
                            data={"chunk": chunk, "full_response": full_response},
                            stream_id=stream_id
                        ))
                    
                    await asyncio.sleep(0)
                
                # Send final result
                if self.streaming_callback:
                    self.streaming_callback(CommandResult(
                        type=ResultType.AI_STREAM_END,
                        data={"full_response": full_response, "query": argument},
                        stream_id=stream_id
                    ))
                
                return CommandResult(
                    type=ResultType.COMMAND_RESULT,
                    command="findai",
                    data={
                        "query": argument,
                        "result": full_response
                    }
                )
                
            except Exception as e:
                if self.streaming_callback:
                    self.streaming_callback(CommandResult(
                        type=ResultType.ERROR,
                        message=f"AI search error: {str(e)}",
                        stream_id=stream_id
                    ))
                return CommandResult(
                    type=ResultType.ERROR,
                    message=f"AI search failed: {str(e)}"
                )
            
        elif command_name in ["del", "delete", "rm", "remove", "eliminar", "udalit", "udali"]:
            note_id = int(argument)
            success = self.manager.delete_note(note_id)
            
            return CommandResult(
                type=ResultType.COMMAND_RESULT,
                command="delete",
                data={
                    "note_id": note_id,
                    "success": success
                },
                message=f"Note #{note_id} {'deleted successfully' if success else 'not found'}"
            )
            
        elif command_name in ["cls", "clear", "clean"]:
            # Clear chat history and content display but keep system prompt
            if self.clear_content_callback:
                self.clear_content_callback()
            if self.log_message_callback:
                self.log_message_callback("Chat cleared (system prompt preserved)")
            
            return CommandResult(
                type=ResultType.COMMAND_RESULT,
                command="clear",
                data={"cleared": True},
                message="Chat cleared"
            )
            
        elif command_name in ["changedb", "db"]:
            if not argument:
                # List all .db files in data directory
                db_files = glob.glob(str(DATA_DIR / "*.db"))
                current_db = self.manager.db.db_path
                
                return CommandResult(
                    type=ResultType.COMMAND_RESULT,
                    command="list_databases",
                    data={
                        "databases": [
                            {
                                "name": os.path.basename(db_file),
                                "path": db_file,
                                "is_current": os.path.abspath(db_file) == current_db
                            }
                            for db_file in sorted(db_files)
                        ],
                        "current_db": os.path.basename(current_db),
                        "data_dir": str(DATA_DIR)
                    }
                )
            
            # Add .db extension if not present
            db_name = argument if argument.endswith('.db') else f"{argument}.db"
            db_path = str(DATA_DIR / db_name)
            
            try:
                self.manager.change_database(db_path)
                if self.log_message_callback:
                    self.log_message_callback(f"Database changed to: {db_name}")
                
                return CommandResult(
                    type=ResultType.COMMAND_RESULT,
                    command="change_database",
                    data={
                        "database_name": db_name,
                        "database_path": db_path,
                        "success": True
                    },
                    message=f"Switched to database `{db_name}`"
                )
            except Exception as e:
                if self.log_message_callback:
                    self.log_message_callback(f"Failed to change database: {e}")
                
                return CommandResult(
                    type=ResultType.ERROR,
                    message=f"Database change failed: {str(e)}",
                    data={
                        "attempted_database": db_name,
                        "error": str(e)
                    }
                )
            
        elif command_name == "export":
            filename = argument
            try:
                # Determine format based on file extension
                if filename.endswith('.json'):
                    export_content = self.manager.export_notes_json()
                    format_type = "json"
                else:
                    # Default to text format
                    export_content = self.manager.export_notes_text()
                    format_type = "text"
                    if not filename.endswith('.txt'):
                        filename = f"{filename}.txt"
                
                # Write to file
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(export_content)
                
                if self.log_message_callback:
                    self.log_message_callback(f"Exported notes to: {filename}")
                
                return CommandResult(
                    type=ResultType.COMMAND_RESULT,
                    command="export",
                    data={
                        "filename": filename,
                        "format": format_type,
                        "content_length": len(export_content)
                    },
                    message=f"Notes exported to: {filename}"
                )
                
            except Exception as e:
                if self.log_message_callback:
                    self.log_message_callback(f"Export error: {e}")
                
                return CommandResult(
                    type=ResultType.ERROR,
                    message=f"Export failed: {str(e)}",
                    data={
                        "filename": filename,
                        "error": str(e)
                    }
                )
        
        else:
            return CommandResult(
                type=ResultType.ERROR,
                message=f"Unknown command: {command_name}",
                data={"command": command_name, "argument": argument}
            )
