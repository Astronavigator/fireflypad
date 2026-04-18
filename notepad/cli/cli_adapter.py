#!/usr/bin/env python3
"""
CLI Adapter for CommandHandler
Converts TUI-style callbacks to console text output
"""

import asyncio
import re
from typing import List, Optional
from notepad.core.command_handler import CommandHandler
from notepad.core.manager import NoteManager


class CLIAdapter:
    """Adapts CommandHandler for console output"""
    
    def __init__(self, manager: NoteManager):
        self.command_handler = CommandHandler(manager)
        self.last_output = ""
        self.chat_history = []
        
        # Set up CLI-specific callbacks
        self.command_handler.set_callbacks(
            update_content=self._handle_content_update,
            log_message=self._handle_log_message,
            add_to_history=self._handle_add_to_history,
            clear_content=self._handle_clear_content,
            streaming=self._handle_streaming_result,
            system_prompt="You are an AI assistant integrated into an intelligent notepad."
        )
    
    def _handle_content_update(self, result) -> None:
        """Handle content update - render structured data for console"""
        # This callback is now handled by _handle_streaming_result for streaming
        # and execute_command for regular commands
        pass
    
    def _handle_streaming_result(self, result) -> None:
        """Handle streaming results from CommandHandler"""
        from notepad.core.command_handler import ResultType
        
        if result.type == ResultType.AI_STREAM_START:
            if result.data.get("type") == "search":
                print(f"\nAI searching for: {result.data['query']}")
            else:
                print(f"\nUser: {result.data['prompt']}")
                print("AI is thinking...")
            
        elif result.type == ResultType.AI_STREAM_CHUNK:
            # For CLI, we'll collect chunks and show at the end
            pass
            
        elif result.type == ResultType.AI_STREAM_END:
            if result.data.get("query"):
                # AI search result
                print(f"AI Result: {result.data['full_response']}")
            else:
                # AI chat result  
                print(f"{result.data['full_response']}")
            
        elif result.type == ResultType.ERROR:
            print(f"Error: {result.message}")
    
    def _render_command_result(self, result) -> str:
        """Render command result as plain text for CLI display"""
        from notepad.core.command_handler import ResultType
        
        if result.command == "list":
            notes = result.data["notes"]
            if not notes:
                return "No notes found"
                
            content = f"Found {result.data['count']} notes:\n"
            content += "-" * 40 + "\n"
            for note in notes:
                tags_str = ", ".join(note["tags"]) if note["tags"] else "none"
                content += f"#{note['id']} {note['title']}\n"
                content += f"{note['content']}\n"
                content += f"Tags: {tags_str}\n\n"
            return content
            
        elif result.command == "find":
            query = result.data["query"]
            results = result.data["results"]
            if not results:
                return f"No results found for '{query}'"
                
            content = f"Results for '{query}' ({result.data['count']} found):\n"
            content += "-" * 40 + "\n"
            for result_note in results:
                dist_str = f"{result_note['distance']:.4f}" if result_note['distance'] else "N/A"
                tags_str = ", ".join(result_note["tags"]) if result_note["tags"] else "none"
                content += f"#{result_note['id']} {result_note['title']}\n"
                content += f"{result_note['content']}\n"
                content += f"Tags: {tags_str} (Distance: {dist_str})\n\n"
            return content
            
        elif result.command == "delete":
            return result.message
            
        elif result.command == "list_databases":
            databases = result.data["databases"]
            current_db = result.data["current_db"]
            content = f"Available databases in {result.data['data_dir']}:\n"
            content += f"Current: {current_db}\n"
            content += "-" * 30 + "\n"
            for db in databases:
                marker = " (current)" if db["is_current"] else ""
                content += f"{db['name']}{marker}\n"
            return content
            
        elif result.command == "change_database":
            return result.message
            
        elif result.command == "export":
            return result.message
            
        else:
            return result.message or "Command executed"
    
    def _handle_log_message(self, message: str) -> None:
        """Handle log message"""
        print(f"[LOG] {message}")
    
    def _handle_add_to_history(self, role: str, content: str) -> None:
        """Handle chat history addition"""
        self.chat_history.append({'role': role, 'content': content})
        
        # Keep history manageable
        if len(self.chat_history) > 20:
            self.chat_history = self.chat_history[-20:]
    
    def _handle_clear_content(self) -> None:
        """Handle content clearing"""
        self.last_output = ""
        self.chat_history = [{'role': 'system', 'content': 'System prompt preserved'}]
    
        
    async def execute_command(self, command_name: str, argument: str = None) -> str:
        """Execute command and return console-friendly output"""
        result = await self.command_handler.execute_command(command_name, argument)
        
        # Render the result for console display
        if result.type.value == "command_result":
            output = self._render_command_result(result)
            self.last_output = output
            return output
        elif result.type.value == "error":
            error_msg = f"Error: {result.message}"
            self.last_output = error_msg
            return error_msg
        else:
            return ""
    
    async def handle_ai_chat(self, message: str) -> str:
        """Handle AI chat - now delegates to CommandHandler"""
        await self.command_handler.handle_ai_chat(message, self.chat_history)
        return ""  # Output is handled by streaming callback
    
    async def handle_note_addition(self, note: str) -> str:
        """Handle note addition"""
        print(f"Adding note: {note}")
        print("Saving...")
        
        await self.command_handler.manager.add_note_async(note)
        
        content = f"Note saved: {note}"
        self._handle_add_to_history('assistant', f"Note added:\n{content}")
        
        return content
