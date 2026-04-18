#!/usr/bin/env python3
"""
TUI Renderer for converting CommandHandler results to Markdown format
"""

from typing import Optional
from notepad.core.command_handler import CommandResult, ResultType


class TUIRenderer:
    """Renders CommandHandler results as Markdown for TUI display"""
    
    def render_command_result(self, result: CommandResult) -> str:
        """Render command result as markdown for TUI display"""
        
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
        content = "-----------\n"
        for note in notes:
            tags_str = " ".join(f"[{tag}]" for tag in note["tags"]) if note["tags"] else "none"
            content += f"> **#{note['id']}** {note['title']}\n>\n> {note['content']} \n>\n> {tags_str}\n\n"
        return content
    
    def _render_find_result(self, result: CommandResult) -> str:
        """Render find command result"""
        query = result.data["query"]
        results = result.data["results"]
        content = f"-----------\nResults of search '{query}'\n"
        for result_note in results:
            dist_str = f"{result_note['distance']:.4f}" if result_note['distance'] else "N/A"
            tags_str = " ".join(f"[{tag}]" for tag in result_note["tags"]) if result_note["tags"] else "none"
            content += f"> [{result_note['id']}], {result_note['title']} \n>\n> {result_note['content']} \n>\n>  {tags_str} [Dist: {dist_str}]\n\n"
        return content
    
    def _render_list_databases_result(self, result: CommandResult) -> str:
        """Render list_databases command result"""
        databases = result.data["databases"]
        current_db = result.data["current_db"]
        content = f"\n?? Available Databases\nLocation: `{result.data['data_dir']}`\nCurrent database: `{current_db}`\n\n"
        
        for db in databases:
            if db["is_current"]:
                content += f"**{db['name']}** (current)\n"
            else:
                content += f"{db['name']}\n"
        return content
    
    def render_streaming_result(self, result: CommandResult) -> Optional[str]:
        """Render streaming result for TUI display"""
        if result.type == ResultType.AI_STREAM_START:
            if result.data.get("type") == "search":
                return f"AI searching for: {result.data['query']}"
            else:
                return f"**User:** {result.data['prompt']}\n**AI:**"
                
        elif result.type == ResultType.AI_STREAM_CHUNK:
            if result.data.get("type") == "search":
                return f"AI Result: {result.data['full_response']}"
            else:
                return f"**AI:** {result.data['full_response']}"
                
        elif result.type == ResultType.AI_STREAM_END:
            # Final update already handled in chunk
            return None
            
        elif result.type == ResultType.ERROR:
            return f"**Error:** {result.message}"
        
        return None
