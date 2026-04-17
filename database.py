import sqlite3
import sqlite_vec
import json
import logging
import struct
from typing import List, Tuple, Optional, Dict
from config import EMBEDDING_DIMENSION

logger = logging.getLogger("notes_cli")


class Database:
    def __init__(self, db_path="notes.db"):
        self.db_path = db_path
        self.embedding_dim = EMBEDDING_DIMENSION
        # Initialize DB structure
        conn = sqlite3.connect(self.db_path)
        conn.enable_load_extension(True)
        sqlite_vec.load(conn)
        self.setup(conn)
        conn.close()

    def change_database(self, new_db_path: str):
        """
        Change to a different database file.
        Creates or loads the new database and reinitializes the structure.
        """
        self.db_path = new_db_path
        # Initialize new DB structure
        conn = sqlite3.connect(self.db_path)
        conn.enable_load_extension(True)
        sqlite_vec.load(conn)
        self.setup(conn)
        conn.close()

    def setup(self, conn: sqlite3.Connection):
        cursor = conn.cursor()
        logger.info("Setting up database tables...")

        # Main notes table (simplified - no tags column)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Embeddings metadata table with UNIQUE constraint on text+kind
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS embeddings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT NOT NULL,
                embedding BLOB NOT NULL,
                kind TEXT NOT NULL,
                UNIQUE(text, kind)
            )
        """)

        # Virtual table for vector search (sqlite-vec)
        cursor.execute(f"""
            CREATE VIRTUAL TABLE IF NOT EXISTS vec_embeddings USING vec0(
                embedding float[{self.embedding_dim}]
            )
        """)

        # Note-tags relationship table
        # embedding_id references embeddings where kind='tag'
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS note_tags (
                note_id INTEGER NOT NULL,
                embedding_id INTEGER NOT NULL,
                PRIMARY KEY (note_id, embedding_id),
                FOREIGN KEY (note_id) REFERENCES notes(id) ON DELETE CASCADE,
                FOREIGN KEY (embedding_id) REFERENCES embeddings(id) ON DELETE CASCADE
            )
        """)

        # Note-embeddings relationship table (all embeddings for a note)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS note_embeddings (
                note_id INTEGER NOT NULL,
                embedding_id INTEGER NOT NULL,
                PRIMARY KEY (note_id, embedding_id),
                FOREIGN KEY (note_id) REFERENCES notes(id) ON DELETE CASCADE,
                FOREIGN KEY (embedding_id) REFERENCES embeddings(id) ON DELETE CASCADE
            )
        """)

        conn.commit()

    def _get_conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.enable_load_extension(True)
        sqlite_vec.load(conn)
        return conn

    # =========================================================================
    # Note operations
    # =========================================================================

    def add_note(self, content: str) -> int:
        """
        Save note content to database.
        Returns: note_id
        """
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO notes (content) VALUES (?)",
                (content,)
            )
            note_id = cursor.lastrowid
            conn.commit()
            logger.info(f"Added note with ID {note_id}")
            return note_id
        finally:
            conn.close()

    def get_recent(self, limit: int = 10) -> List[Tuple]:
        """
        Get recent notes.
        Returns: [(id, content, created_at), ...]
        """
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, content, created_at FROM notes ORDER BY id DESC LIMIT ?",
                (limit,)
            )
            return cursor.fetchall()
        finally:
            conn.close()

    def get_note_by_id(self, note_id: int) -> Optional[Tuple]:
        """
        Get note by ID.
        Returns: (id, content, created_at) or None
        """
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, content, created_at FROM notes WHERE id = ?",
                (note_id,)
            )
            return cursor.fetchone()
        finally:
            conn.close()

    def delete_note(self, note_id: int) -> bool:
        """
        Delete note by ID. Cascades to note_tags and note_embeddings.
        Returns: True if deleted, False if not found
        """
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM notes WHERE id = ?", (note_id,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    # =========================================================================
    # Embedding operations
    # =========================================================================

    def get_existing_embeddings(self, text_kind_list: List[Tuple[str, str]]) -> List[Tuple[int, str, str, List[float]]]:
        """
        Get existing embeddings for given (text, kind) pairs.

        Args:
            text_kind_list: List of (text, kind) tuples

        Returns:
            List of (id, text, kind, embedding) tuples
            embedding is returned as Python list of floats
        """
        if not text_kind_list:
            return []

        conn = self._get_conn()
        try:
            cursor = conn.cursor()

            # Build query with OR conditions for each (text, kind) pair
            conditions = []
            params = []
            for text, kind in text_kind_list:
                conditions.append("(text = ? AND kind = ?)")
                params.extend([text, kind])

            sql = f"""
                SELECT id, text, kind, embedding
                FROM embeddings
                WHERE {' OR '.join(conditions)}
            """
            cursor.execute(sql, params)

            results = []
            for row in cursor.fetchall():
                emb_id, text, kind, embedding_blob = row
                # Convert BLOB back to list of floats
                embedding = self._blob_to_embedding(embedding_blob)
                results.append((emb_id, text, kind, embedding))

            return results
        finally:
            conn.close()

    def insert_embeddings(self, embeddings_data: List[Tuple[str, List[float], str]]) -> List[int]:
        """
        Insert new embeddings into database.

        Args:
            embeddings_data: List of (text, embedding_list, kind) tuples

        Returns:
            List of inserted embedding IDs
        """
        if not embeddings_data:
            return []

        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            inserted_ids = []

            for text, embedding_list, kind in embeddings_data:
                # Convert embedding list to BLOB
                embedding_blob = self._embedding_to_blob(embedding_list)

                # Insert into embeddings table
                cursor.execute(
                    "INSERT INTO embeddings (text, embedding, kind) VALUES (?, ?, ?)",
                    (text, embedding_blob, kind)
                )
                emb_id = cursor.lastrowid
                inserted_ids.append(emb_id)

                # Also insert into virtual table for vector search
                embedding_json = json.dumps(embedding_list)
                cursor.execute(
                    "INSERT INTO vec_embeddings(rowid, embedding) VALUES (?, ?)",
                    (emb_id, embedding_json)
                )

            conn.commit()
            logger.info(f"Inserted {len(inserted_ids)} embeddings")
            return inserted_ids
        finally:
            conn.close()

    def get_embedding_by_id(self, embedding_id: int) -> Optional[Tuple[int, str, List[float], str]]:
        """
        Get embedding by ID.
        Returns: (id, text, embedding_list, kind) or None
        """
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, text, embedding, kind FROM embeddings WHERE id = ?",
                (embedding_id,)
            )
            row = cursor.fetchone()
            if row:
                emb_id, text, embedding_blob, kind = row
                embedding_list = self._blob_to_embedding(embedding_blob)
                return (emb_id, text, embedding_list, kind)
            return None
        finally:
            conn.close()

    # =========================================================================
    # Note-Tag relationships
    # =========================================================================

    def add_note_tag(self, note_id: int, embedding_id: int):
        """
        Link a note to a tag (embedding with kind='tag').
        """
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR IGNORE INTO note_tags (note_id, embedding_id) VALUES (?, ?)",
                (note_id, embedding_id)
            )
            conn.commit()
        finally:
            conn.close()

    def get_note_tags(self, note_id: int) -> List[str]:
        """
        Get all tag texts for a note.
        Returns: List of tag strings
        """
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT e.text
                FROM note_tags nt
                JOIN embeddings e ON nt.embedding_id = e.id
                WHERE nt.note_id = ? AND e.kind = 'tag'
            """, (note_id,))
            return [row[0] for row in cursor.fetchall()]
        finally:
            conn.close()

    def get_notes_by_tag(self, tag_text: str) -> List[Tuple[int, str]]:
        """
        Get all notes that have a specific tag.
        Returns: [(note_id, content), ...]
        """
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT n.id, n.content
                FROM notes n
                JOIN note_tags nt ON n.id = nt.note_id
                JOIN embeddings e ON nt.embedding_id = e.id
                WHERE e.text = ? AND e.kind = 'tag'
            """, (tag_text,))
            return cursor.fetchall()
        finally:
            conn.close()

    # =========================================================================
    # Note-Embedding relationships
    # =========================================================================

    def add_note_embedding(self, note_id: int, embedding_id: int):
        """
        Link a note to an embedding.
        """
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR IGNORE INTO note_embeddings (note_id, embedding_id) VALUES (?, ?)",
                (note_id, embedding_id)
            )
            conn.commit()
        finally:
            conn.close()

    def get_note_embeddings(self, note_id: int) -> List[Tuple[int, str, str, List[float]]]:
        """
        Get all embeddings linked to a note.
        Returns: [(embedding_id, text, kind, embedding_list), ...]
        """
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT e.id, e.text, e.kind, e.embedding
                FROM note_embeddings ne
                JOIN embeddings e ON ne.embedding_id = e.id
                WHERE ne.note_id = ?
            """, (note_id,))

            results = []
            for row in cursor.fetchall():
                emb_id, text, kind, embedding_blob = row
                embedding_list = self._blob_to_embedding(embedding_blob)
                results.append((emb_id, text, kind, embedding_list))
            return results
        finally:
            conn.close()

    # =========================================================================
    # Vector Search
    # =========================================================================

    def vector_search(self, query_embedding: List[float], limit: int = 5, max_dist: float = 0.7) -> List[Tuple[int, str, str, List[str], float]]:
        """
        Search for notes by embedding similarity.

        Args:
            query_embedding: The query embedding vector
            limit: Maximum number of results
            max_dist: Maximum distance threshold (lower is more similar)

        Returns:
            List of (note_id, content, tags, distance) tuples
        """
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            # sqlite-vec format: JSON array string for query
            #print(query_embedding)
            query_json = json.dumps(query_embedding)

            # Search in vec_embeddings, join with embeddings to get metadata,
            # then join with note_embeddings to get notes
            sql = """
                SELECT n.id, n.content, n.created_at, min(v.distance)
                FROM vec_embeddings AS v
                JOIN embeddings e ON v.rowid = e.id
                JOIN note_embeddings ne ON e.id = ne.embedding_id
                JOIN notes n ON ne.note_id = n.id
                WHERE v.embedding MATCH ? AND k = ?
                AND v.distance <= ?
                GROUP BY n.id, n.content, n.created_at
                ORDER BY v.distance ASC
            """
            cursor.execute(sql, (query_json, limit, max_dist))

            results = []
            for row in cursor.fetchall():
                note_id, content, created_at, distance = row
                # Get tags for this note
                tags = self.get_note_tags(note_id)
                results.append((note_id, content, created_at, tags, distance))

            return results
        finally:
            conn.close()

    def vector_search_by_kind(self, query_embedding: List[float], kind: str, limit: int = 5) -> List[Tuple[int, str, str, float]]:
        """
        Search embeddings of a specific kind.

        Args:
            query_embedding: The query embedding vector
            kind: Filter by embedding kind ('note', 'tag', 'question', 'tag_combination')
            limit: Maximum number of results

        Returns:
            List of (embedding_id, text, kind, distance) tuples
        """
        conn = self._get_conn()
        try:
            cursor = conn.cursor() 
            query_json = json.dumps(query_embedding)

            sql = """
                SELECT e.id, e.text, e.kind, v.distance
                FROM vec_embeddings AS v
                JOIN embeddings e ON v.rowid = e.id
                WHERE v.embedding MATCH ? AND k = ? AND e.kind = ?
                ORDER BY v.distance ASC
            """
            cursor.execute(sql, (query_json, limit, kind))
            return cursor.fetchall()
        finally:
            conn.close()

    # =========================================================================
    # Utility methods
    # =========================================================================

    def _embedding_to_blob(self, embedding: List[float]) -> bytes:
        """Convert list of floats to BLOB using struct."""
        return struct.pack(f"{len(embedding)}f", *embedding)

    def _blob_to_embedding(self, blob: bytes) -> List[float]:
        """Convert BLOB to list of floats using struct."""
        if not blob:
            return []
        num_floats = len(blob) // 4
        return list(struct.unpack(f"{num_floats}f", blob))

    def export_all_notes_text(self) -> str:
        """
        Export all notes to text format.
        Returns: String with all notes in text format
        """
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, content, created_at
                FROM notes 
                ORDER BY id ASC
            """)
            
            notes = cursor.fetchall()
            result = []
            
            for note_id, content, created_at in notes:
                tags = self.get_note_tags(note_id)
                tags_str = ", ".join(tags) if tags else "none"
                
                result.append(f"=== Note #{note_id} ===")
                result.append(f"Created: {created_at}")
                result.append(f"Tags: {tags_str}")
                result.append(f"Content: {content}")
                result.append("")  # Empty line between notes
            
            return "\n".join(result)
        finally:
            conn.close()

    def export_all_notes_json(self) -> str:
        """
        Export all notes to JSON format.
        Returns: JSON string with all notes
        """
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, content, created_at
                FROM notes 
                ORDER BY id ASC
            """)
            
            notes = cursor.fetchall()
            result = []
            
            for note_id, content, created_at in notes:
                tags = self.get_note_tags(note_id)
                
                note_data = {
                    "id": note_id,
                    "content": content,
                    "created_at": created_at,
                    "tags": tags
                }
                result.append(note_data)
            
            return json.dumps(result, indent=2, ensure_ascii=False)
        finally:
            conn.close()
