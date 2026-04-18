#!/usr/bin/env python3
"""
CLI Renderer for converting CommandHandler results to plain text format
"""

from typing import Optional
from notepad.core.command_handler import CommandResult, ResultType


class CLIRenderer:
    """Renders CommandHandler results as plain text for CLI display"""
    
    def render_command_result(self, result: CommandResult) -> str:
        """Render command result as plain text for CLI display"""
        
        if result.command == "list":
            return self._render_list_result(result)
        elif result.command == "find":
            return self._render_find_result(result)
        elif result.command == "delete":
            return result.message or "Note deleted"
        elif result.command == "list_databases":
            return self._render_list_databases_result(result)
        elif result.command == "change_database":
            return result.message or "Database changed"
        elif result.command == "export":
            return result.message or "Export completed"
        else:
            return result.message or "Command executed"
    
    def _render_list_result(self, result: CommandResult) -> str:
        """Render list command result"""
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
    
    def _render_find_result(self, result: CommandResult) -> str:
        """Render find command result"""
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
    
    def _render_list_databases_result(self, result: CommandResult) -> str:
        """Render list_databases command result"""
        databases = result.data["databases"]
        current_db = result.data["current_db"]
        content = f"Available databases in {result.data['data_dir']}:\n"
        content += f"Current: {current_db}\n"
        content += "-" * 30 + "\n"
        for db in databases:
            marker = " (current)" if db["is_current"] else ""
            content += f"{db['name']}{marker}\n"
        return content
    
    def render_streaming_result(self, result: CommandResult) -> Optional[str]:
        """Render streaming result for CLI display"""
        if result.type == ResultType.AI_STREAM_START:
            if result.data.get("type") == "search":
                return f"\nAI searching for: {result.data['query']}"
            else:
                return f"\nUser: {result.data['prompt']}\nAI is thinking..."
            
        elif result.type == ResultType.AI_STREAM_CHUNK:
            # For CLI, we'll collect chunks and show at the end
            return None
            
        elif result.type == ResultType.AI_STREAM_END:
            if result.data.get("query"):
                # AI search result
                return f"AI Result: {result.data['full_response']}"
            else:
                # AI chat result  
                return f"{result.data['full_response']}"
            
        elif result.type == ResultType.ERROR:
            return f"Error: {result.message}"
        
        return None
