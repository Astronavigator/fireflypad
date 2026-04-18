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
            system_prompt="You are an AI assistant integrated into an intelligent notepad."
        )
    
    def _handle_content_update(self, content: str, **kwargs) -> None:
        """Handle content update - convert markdown to plain text"""
        # Remove markdown formatting for console
        plain_text = self._markdown_to_plain(content)
        self.last_output = plain_text
    
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
    
    def _markdown_to_plain(self, markdown_text: str) -> str:
        """Convert markdown to plain text for console display"""
        # Remove bold formatting
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', markdown_text)
        
        # Remove italic formatting  
        text = re.sub(r'\*(.*?)\*', r'\1', text)
        
        # Remove code formatting
        text = re.sub(r'`(.*?)`', r'\1', text)
        
        # Remove headers
        text = re.sub(r'^#+\s*', '', text, flags=re.MULTILINE)
        
        # Remove blockquote markers and clean up
        text = re.sub(r'^>\s*', '', text, flags=re.MULTILINE)
        
        # Remove specific markdown patterns but keep text
        text = re.sub(r'\\#(\d+)', r'#\1', text)  # Fix note numbers
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)  # Remove links, keep text
        
        # Clean up extra whitespace but preserve structure
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = text.strip()
        
        return text if text else "No results"
    
    async def execute_command(self, command_name: str, argument: str = None) -> str:
        """Execute command and return console-friendly output"""
        await self.command_handler.execute_command(command_name, argument)
        return self.last_output
    
    async def handle_ai_chat(self, message: str) -> str:
        """Handle AI chat and return response"""
        # Remove $ prefix if present
        if message.startswith("$"):
            prompt = message[1:].strip()
        else:
            prompt = message.strip()
        
        print(f"\nAI Chat: {prompt}")
        print("AI is thinking...")
        
        # Use manager directly for streaming
        full_response = ""
        async for chunk in self.command_handler.manager.ai_chat_stream(prompt, self.chat_history):
            full_response += chunk
        
        # Add to history
        self._handle_add_to_history('user', prompt)
        self._handle_add_to_history('assistant', full_response)
        
        return full_response
    
    async def handle_note_addition(self, note: str) -> str:
        """Handle note addition"""
        print(f"Adding note: {note}")
        print("Saving...")
        
        await self.command_handler.manager.add_note_async(note)
        
        content = f"Note saved: {note}"
        self._handle_add_to_history('assistant', f"Note added:\n{content}")
        
        return content
