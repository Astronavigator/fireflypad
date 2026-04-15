import asyncio
import json
from database import Database
from ollama_client import OllamaClient

class NoteManager:
    def __init__(self):
        self.db = Database()
        self.ai = OllamaClient()
        self.queue = asyncio.Queue()
        self.is_processing = False
        self._log_callback = None
   
    def set_log_callback(self, callback):
        """Set callback for logging operations"""
        self._log_callback = callback
    
    def _log_callback(self, message: str, is_chunk: bool = False):
        """Internal log callback that forwards to set callback"""
        if self._log_callback:
            self._log_callback(message, is_chunk)

    async def add_note_async(self, content):
        # Put the note in the queue to be processed
        self._log_callback(f"Adding note: {content}")
        await self.queue.put(content)
        
        # Start the worker if it's not running
        if not self.is_processing:
            asyncio.create_task(self._worker())

    async def _worker(self):
        self.is_processing = True
        while not self.queue.empty():
            content = await self.queue.get()
            try:
                # Run CPU-bound/network-bound tasks in executor to avoid blocking the event loop
                loop = asyncio.get_running_loop()
                tags = await self.ai.analyze_note(content, log_callback=self._log_callback)
                embedding = await loop.run_in_executor(None, self.ai.get_embedding, content)
                
                # Database operations
                await loop.run_in_executor(None, self.db.add_note, content, embedding, tags)
            except Exception as e:
                self._log_callback(f"Error saving note: {e}")
            finally:
                self.queue.task_done()
        self.is_processing = False

    def list_notes(self, limit=10):
        return self.db.get_recent(limit)

    def find_notes(self, query):
        embedding = self.ai.get_embedding(query)
        return self.db.vector_search(embedding)

    async def find_notes_ai_stream(self, query):
        """Async streaming AI search with logging"""
        self._log_callback(f"AI searching for: {query}")
        
        # For AI search, we get top K candidates via vector search
        # and then let the AI filter/summarize
        candidates = self.find_notes(query)
        if not candidates:
            self._log_callback("No relevant notes found")
            return
        
        context = "\n".join([f"Note {n[0]}: {n[1]} (Tags: {n[2]})" for n in candidates])
        prompt = f"Based on the following notes, answer the user's question: {query}\n\nNotes:\n{context}"
        
        async for chunk in self.ai.chat_stream(prompt, log_callback=self._log_callback):
            yield chunk
    
    def find_notes_ai(self, query):
        """Non-streaming AI search for backward compatibility"""
        # For AI search, we get top K candidates via vector search
        # and then let the AI filter/summarize
        candidates = self.find_notes(query)
        if not candidates:
            return "No relevant notes found."
        
        context = "\n".join([f"Note {n[0]}: {n[1]} (Tags: {n[2]})" for n in candidates])
        prompt = f"Based on the following notes, answer the user's question: {query}\n\nNotes:\n{context}"
        return self.ai.chat(prompt)

    async def fake_stream(self):
        for i in range(10):
            await asyncio.sleep(0.5) # Имитация ожидания
            yield f"Токен {i} "

    async def ai_chat_stream(self, prompt, history):
        """Async streaming AI chat with logging"""
        async for chunk in self.ai.chat_stream(prompt, history, log_callback=self._log_callback):
            yield chunk
        
    
    def ai_chat(self, prompt, history):
        """Non-streaming AI chat for backward compatibility"""
        return self.ai.chat(prompt, history)
