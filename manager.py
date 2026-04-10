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

    async def add_note_async(self, content):
        # Put the note in the queue to be processed
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
                tags = await loop.run_in_executor(None, self.ai.analyze_note, content)
                embedding = await loop.run_in_executor(None, self.ai.get_embedding, content)
                
                # Database operations
                await loop.run_in_executor(None, self.db.add_note, content, embedding, tags)
            except Exception as e:
                print(f"\nError saving note: {e}")
            finally:
                self.queue.task_done()
        self.is_processing = False

    def list_notes(self, limit=10):
        return self.db.get_recent(limit)

    def find_notes(self, query):
        embedding = self.ai.get_embedding(query)
        return self.db.vector_search(embedding)

    def find_notes_ai(self, query):
        # For AI search, we get top K candidates via vector search
        # and then let the AI filter/summarize
        candidates = self.find_notes(query)
        if not candidates:
            return "No relevant notes found."
        
        context = "\n".join([f"Note {n[0]}: {n[1]} (Tags: {n[2]})" for n in candidates])
        prompt = f"Based on the following notes, answer the user's question: {query}\n\nNotes:\n{context}"
        return self.ai.chat(prompt)

    def ai_chat(self, prompt, history):
        return self.ai.chat(prompt, history)
