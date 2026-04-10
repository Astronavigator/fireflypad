import sqlite3
import sqlite_vec
import json
import logging

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
            
            # Based on the function list, vec_distance_l2 is the correct function for L2 distance
            sql = """
                SELECT id, content, tags, 
                       vec_distance_l2(embedding, ?) as distance
                FROM notes
                ORDER BY distance ASC
                LIMIT ?
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
