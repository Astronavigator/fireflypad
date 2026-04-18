#!/usr/bin/env python3
"""
TUI Renderer for converting CommandHandler results to Markdown format
"""

from typing import Optional, List, Dict, Any
from notepad.core.command_handler import CommandResult, ResultType
from typing import TypedDict

class RenderChunk(TypedDict):
    format: Optional[str] # The format of the content (e.g., "markdown", "static", etc.)
    mode: str  # "add" or "update"
    content: str # The actual content to render

class TUIRenderer:
    """Renders CommandHandler results as Markdown for TUI display"""
    
    def render_command_result(self, result: CommandResult) -> List[RenderChunk]:
        """Render command result as markdown for TUI display"""
        
        if result.command == "list":
            return self._render_list_result(result)
        elif result.command == "find":
            return self._render_find_result(result)
        elif result.command == "delete":
            return [{"format": None, "mode": "add", "content": result.message or "Note deleted"}]
        elif result.command == "list_databases":
            return self._render_list_databases_result(result)
        elif result.command == "change_database":
            return [{"format": None, "mode": "add", "content": result.message or "Database changed"}]
        elif result.command == "clear":
            return [] # nothing to render
        elif result.command == "export":
            return [{"format": None, "mode": "add", "content": result.message or "Export completed"}]
        else:
            return [{"format": None, "mode": "add", "content": result.message or "Command executed"}]
    
    def _render_list_result(self, result: CommandResult) -> List[RenderChunk]:
        """Render list command result"""
        notes = result.data["notes"]
        content = "-----------\n"
        for note in notes:
            tags_str = " ".join(f"[{tag}]" for tag in note["tags"]) if note["tags"] else "none"
            content += f"> **#{note['id']}** {note['title']}\n>\n> {note['content']} \n>\n> {tags_str}\n\n"
        return [{"format": "markdown", "mode": "add", "content": content}]
    
    def _render_find_result(self, result: CommandResult) -> List[RenderChunk]:
        """Render find command result"""
        query = result.data["query"]
        results = result.data["results"]
        content = f"-----------\nResults of search '{query}'\n"
        for result_note in results:
            dist_str = f"{result_note['distance']:.4f}" if result_note['distance'] else "N/A"
            tags_str = " ".join(f"[{tag}]" for tag in result_note["tags"]) if result_note["tags"] else "none"
            content += f"> [{result_note['id']}], {result_note['title']} \n>\n> {result_note['content']} \n>\n>  {tags_str} [Dist: {dist_str}]\n\n"
        return [{"format": "markdown", "mode": "add", "content": content}]
    
    def _render_list_databases_result(self, result: CommandResult) -> List[RenderChunk]:
        """Render list_databases command result"""
        databases = result.data["databases"]
        current_db = result.data["current_db"]
        content = [{"format": "markdown", "mode": "add", "content":
            f"\n Databases Location: `{result.data['data_dir']}`"}]
        
        dbstr = ""
        for db in databases:
            if db["is_current"]:
                dbstr += f"{db['name']} "
            else:
                dbstr += f"[@click=app.change_database('{db['name']}')][b]{db['name']}[/][/] "
        content.append({"format": "static", "mode": "add", "content": dbstr + "\n"})
        return content
    
    def render_streaming_result(self, result: CommandResult) -> Optional[List[RenderChunk]]:
        """Render streaming result for TUI display"""
        if result.type == ResultType.AI_STREAM_START:
            if result.data.get("type") == "search":
                return [
                    {"format": "markdown", "mode": "add", "content": f"AI searching for: {result.data['query']}"},
                    {"format": "markdown", "mode": "add", "content": f"...."} # for future result
                    ]
            else:
                return [
                    {"format": "markdown", "mode": "add", "content": f"**User:** {result.data['prompt']}\n"},
                    {"format": "markdown", "mode": "add", "content": f"...."} # for future result
                ]
                
        elif result.type == ResultType.AI_STREAM_CHUNK:
            if result.data.get("type") == "search":
                return [{"format": None, "mode": "update", "content": f"AI Result: {result.data['full_response']}"}]
            else:
                return [{"format": None, "mode": "update", "content": f"**AI:** {result.data['full_response']}"}]
                
        elif result.type == ResultType.AI_STREAM_END:
            # Final update already handled in chunk
            return None
            
        elif result.type == ResultType.ERROR:
            return [{"format": "markdown", "mode": "add", "content": f"**Error:** {result.message}"}]
        
        return None
