import sqlite3
import sqlite_vec
import struct
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sql_test")

def test_vector_query():
    db_path = "notes.db"
    conn = sqlite3.connect(db_path)
    conn.enable_load_extension(True)
    sqlite_vec.load(conn)
    
    # 1. Check if we have data
    cursor = conn.cursor()
    cursor.execute("SELECT count(*) FROM notes")
    count = cursor.fetchone()[0]
    logger.info(f"Current notes in DB: {count}")
    
    if count == 0:
        logger.info("DB is empty. Inserting a test note...")
        # Create a dummy embedding (768 floats)
        dummy_embedding = [0.1] * 768
        blob = struct.pack(f"{len(dummy_embedding)}f", *dummy_embedding)
        cursor.execute("INSERT INTO notes (content, tags, embedding) VALUES (?, ?, ?)", 
                       ("Test Note", "test", blob))
        conn.commit()
        logger.info("Test note inserted.")

    # 2. Try different query patterns
    query_vector = [0.11] * 768
    query_blob = struct.pack(f"{len(query_vector)}f", *query_vector)

    test_queries = [
        # Attempt 1: Using the 'k' mentioned in the article
        "SELECT id, content FROM notes WHERE embedding MATCH ? AND k = 5",
        # Attempt 2: Combining MATCH and LIMIT
        "SELECT id, content FROM notes WHERE embedding MATCH ? LIMIT 5",
        # Attempt 3: Just distance calculation without MATCH (brute force)
        "SELECT id, content, vec_distance_f32(embedding, ?) as dist FROM notes ORDER BY dist LIMIT 5",
    ]

    for i, sql in enumerate(test_queries):
        logger.info(f"Testing Query {i+1}: {sql}")
        try:
            cursor.execute(sql, (query_blob,))
            results = cursor.fetchall()
            logger.info(f"Query {i+1} SUCCESS. Found {len(results)} results.")
            for r in results:
                logger.info(f"Result: {r}")
        except Exception as e:
            logger.error(f"Query {i+1} FAILED: {e}")

    conn.close()

if __name__ == "__main__":
    test_vector_query()
