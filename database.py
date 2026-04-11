import sqlite3
import sqlite_vec
import json
import logging
from config import EMBEDDING_DIMENSION

logger = logging.getLogger("notes_cli")

class Database:
    def __init__(self, db_path="notes.db"):
        self.db_path = db_path
        # Initialize DB structure
        conn = sqlite3.connect(self.db_path)
        conn.enable_load_extension(True)
        sqlite_vec.load(conn)
        self.setup(conn)
        conn.close()

    def setup(self, conn):
        cursor = conn.cursor()
        logger.info("Setting up database tables...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                tags TEXT,
                embedding BLOB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

    def _get_conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.enable_load_extension(True)
        sqlite_vec.load(conn)
        # Initialize vector search for the connection
        conn.execute(f"SELECT vector_init('notes', 'embedding', 'dimension={EMBEDDING_DIMENSION}')")
        return conn

    def add_note(self, content, embedding, tags=None):
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            tags_str = tags if isinstance(tags, str) else json.dumps(tags)
            import struct
            embedding_blob = struct.pack(f"{len(embedding)}f", *embedding)
            
            sql = "INSERT INTO notes (content, tags, embedding) VALUES (?, ?, ?)"
            logger.info(f"Executing SQL: {sql} with params: ({content}, {tags_str}, <blob>)")
            cursor.execute(sql, (content, tags_str, embedding_blob))
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    def get_recent(self, limit=10):
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            sql = "SELECT id, content, tags FROM notes ORDER BY id DESC LIMIT ?"
            logger.info(f"Executing SQL: {sql} with params: ({limit},)")
            cursor.execute(sql, (limit,))
            return cursor.fetchall()
        finally:
            conn.close()

    def vector_search(self, query_embedding, limit=5):
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            import struct
            query_blob = struct.pack(f"{len(query_embedding)}f", *query_embedding)

            sql = """
                SELECT n.id, n.content, n.tags, v.distance
                FROM notes AS n
                JOIN vector_full_scan('notes', 'embedding', ?, ?) AS v
                ON n.id = v.rowid
            """
            logger.info(f"Executing SQL: {sql} with params: (<blob>, {limit})")
            cursor.execute(sql, (query_blob, limit))
            return cursor.fetchall()
        finally:
            conn.close()

    def get_note_by_id(self, note_id):
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            sql = "SELECT content, tags FROM notes WHERE id = ?"
            logger.info(f"Executing SQL: {sql} with params: ({note_id},)")
            cursor.execute(sql, (note_id,))
            return cursor.fetchone()
        finally:
            conn.close()
