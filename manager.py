import asyncio
import json
from typing import List, Tuple, Optional, Set
from database import Database
from ollama_client import OllamaClient


class NoteManager:
    def __init__(self):
        self.db = Database()
        self.ai = OllamaClient()
        self.queue = asyncio.Queue()
        self.is_processing = False
        self._log_callback_fn = None

    def set_log_callback(self, callback):
        """Set callback for logging operations"""
        self._log_callback_fn = callback

    def _log_callback(self, message: str, is_chunk: bool = False):
        """Internal log callback that forwards to set callback"""
        if self._log_callback_fn:
            self._log_callback_fn(message, is_chunk)

    async def add_note_async(self, content):
        """Put the note in the queue to be processed"""
        self._log_callback(f"Adding note: {content}")
        await self.queue.put(content)

        # Start the worker if it's not running
        if not self.is_processing:
            asyncio.create_task(self._worker())

    async def _worker(self):
        """
        6-step note saving process:
        1. Analyze note with AI
        2. Create list of required embeddings
        3. Get existing embeddings from DB
        4. Calculate missing embeddings
        5. Insert new embeddings
        6. Save note and create relationships
        """
        self.is_processing = True
        while not self.queue.empty():
            content = await self.queue.get()
            try:
                loop = asyncio.get_running_loop()

                # ============================================================
                # STEP 1: Analyze note with AI
                # ============================================================
                self._log_callback("Analyzing note with AI...")
                analysis = await self.ai.analyze_note(
                    content,
                    log_callback=self._log_callback
                )
                self._log_callback(
                    f"Analysis complete: {len(analysis.questions)} questions, "
                    f"{len(analysis.tags)} tags"
                )

                # ============================================================
                # STEP 2: Create list of required embeddings (text, kind)
                # ============================================================
                embedding_tasks: List[Tuple[str, str]] = []

                # a. Embedding of the note itself
                embedding_tasks.append((content, 'note'))

                # b. Embeddings of all questions from analysis
                for question in analysis.questions:
                    embedding_tasks.append((question, 'question'))

                # c. Embeddings of all tags
                for tag in analysis.tags:
                    embedding_tasks.append((tag, 'tag'))

                # d. Embedding of sorted tag concatenation
                if analysis.tags:
                    tag_combination = ' '.join(sorted(analysis.tags))
                    embedding_tasks.append((tag_combination, 'tag_combination'))

                self._log_callback(
                    f"Total embeddings needed: {len(embedding_tasks)}"
                )

                # ============================================================
                # STEP 3: Get existing embeddings from DB
                # ============================================================
                self._log_callback("Checking for existing embeddings...")
                existing = await loop.run_in_executor(
                    None,
                    self.db.get_existing_embeddings,
                    embedding_tasks
                )

                # Build lookup maps
                existing_ids_map: Dict[Tuple[str, str], int] = {}
                existing_text_kind_set: Set[Tuple[str, str]] = set()

                for emb_id, text, kind, _ in existing:
                    existing_ids_map[(text, kind)] = emb_id
                    existing_text_kind_set.add((text, kind))

                self._log_callback(f"Found {len(existing)} existing embeddings")

                # Determine which embeddings need to be created
                to_create: List[Tuple[str, str]] = [
                    (text, kind) for text, kind in embedding_tasks
                    if (text, kind) not in existing_text_kind_set
                ]

                # ============================================================
                # STEP 4: Calculate missing embeddings
                # ============================================================
                new_embeddings_data: List[Tuple[str, List[float], str]] = []

                if to_create:
                    self._log_callback(f"Calculating {len(to_create)} new embeddings...")

                    for text, kind in to_create:
                        # Calculate embedding via Ollama
                        embedding = await loop.run_in_executor(
                            None,
                            self.ai.get_embedding,
                            text
                        )
                        new_embeddings_data.append((text, embedding, kind))

                    self._log_callback(
                        f"Calculated {len(new_embeddings_data)} new embeddings"
                    )

                # ============================================================
                # STEP 5: Insert new embeddings into DB
                # ============================================================
                new_ids: List[int] = []
                if new_embeddings_data:
                    self._log_callback("Saving new embeddings to database...")
                    new_ids = await loop.run_in_executor(
                        None,
                        self.db.insert_embeddings,
                        new_embeddings_data
                    )
                    self._log_callback(f"Saved {len(new_ids)} new embeddings")

                # Build map of (text, kind) -> embedding_id for ALL embeddings
                embedding_id_map = existing_ids_map.copy()
                for i, (text, kind) in enumerate(to_create):
                    embedding_id_map[(text, kind)] = new_ids[i]

                # ============================================================
                # STEP 6: Save note and create relationships
                # ============================================================
                self._log_callback("Saving note to database...")

                # 6a. Save the note
                note_id = await loop.run_in_executor(
                    None,
                    self.db.add_note,
                    content
                )
                self._log_callback(f"Note saved with ID {note_id}")

                # 6b. Create note_embeddings relationships for ALL embeddings
                for text, kind in embedding_tasks:
                    emb_id = embedding_id_map[(text, kind)]
                    await loop.run_in_executor(
                        None,
                        self.db.add_note_embedding,
                        note_id,
                        emb_id
                    )

                # 6c. Create note_tags relationships (only for kind='tag')
                for tag in analysis.tags:
                    tag_emb_id = embedding_id_map.get((tag, 'tag'))
                    if tag_emb_id:
                        await loop.run_in_executor(
                            None,
                            self.db.add_note_tag,
                            note_id,
                            tag_emb_id
                        )

                self._log_callback(
                    f"Note {note_id} linked to {len(embedding_tasks)} embeddings"
                )
                self._log_callback(f"Note {note_id} tagged with {len(analysis.tags)} tags")

            except Exception as e:
                self._log_callback(f"Error saving note: {e}")
                import traceback
                self._log_callback(traceback.format_exc())
            finally:
                self.queue.task_done()

        self.is_processing = False

    def list_notes(self, limit=10) -> List[Tuple[int, str, str, List[str]]]:
        """
        Get recent notes with their tags.
        Returns: [(note_id, content, created_at, tags_list), ...]
        """
        notes = self.db.get_recent(limit)
        results = []
        for note_id, content, created_at in notes:
            tags = self.db.get_note_tags(note_id)
            results.append((note_id, content, created_at, tags))
        return results

    def find_notes(self, query, max_dist = 0.7):
        """
        Semantic vector search for notes.
        Returns: [(note_id, content, tags, distance), ...]
        """
        embedding = self.ai.get_embedding(query)
        return self.db.vector_search(embedding, max_dist=max_dist)

    async def find_notes_ai_stream(self, query):
        """Async streaming AI search with logging"""
        self._log_callback(f"AI searching for: {query}")

        # Get top K candidates via vector search
        candidates = self.find_notes(query)
        if not candidates:
            self._log_callback("No relevant notes found")
            return

        # Build context with tags
        context_parts = []
        for note_id, content, tags, distance in candidates:
            tags_str = ", ".join(tags) if tags else "none"
            context_parts.append(
                f"Note {note_id}: {content} (Tags: {tags_str})"
            )
        context = "\n".join(context_parts)

        prompt = (
            f"Based on the following notes, answer the user's question: "
            f"{query}\n\nNotes:\n{context}"
        )

        async for chunk in self.ai.chat_stream(prompt, log_callback=self._log_callback):
            yield chunk

    def find_notes_ai(self, query):
        """Non-streaming AI search for backward compatibility"""
        # Get candidates via vector search
        candidates = self.find_notes(query)
        if not candidates:
            return "No relevant notes found."

        # Build context with tags
        context_parts = []
        for note_id, content, tags, distance in candidates:
            tags_str = ", ".join(tags) if tags else "none"
            context_parts.append(
                f"Note {note_id}: {content} (Tags: {tags_str})"
            )
        context = "\n".join(context_parts)

        prompt = (
            f"Based on the following notes, answer the user's question: "
            f"{query}\n\nNotes:\n{context}"
        )
        return self.ai.chat(prompt)

    async def fake_stream(self):
        for i in range(10):
            await asyncio.sleep(0.5)
            yield f"Token {i} "

    async def ai_chat_stream(self, prompt, history):
        """Async streaming AI chat with logging"""
        async for chunk in self.ai.chat_stream(
            prompt, history, log_callback=self._log_callback
        ):
            yield chunk

    def delete_note(self, note_id: int) -> bool:
        """
        Delete note by ID.
        Returns: True if deleted, False if not found
        """
        self._log_callback(f"Deleting note {note_id}...")
        result = self.db.delete_note(note_id)
        if result:
            self._log_callback(f"Note {note_id} deleted successfully")
        else:
            self._log_callback(f"Note {note_id} not found")
        return result

    def ai_chat(self, prompt, history):
        """Non-streaming AI chat for backward compatibility"""
        return self.ai.chat(prompt, history)
