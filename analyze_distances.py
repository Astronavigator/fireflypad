import sqlite3
import struct
from ollama_client import OllamaClient
from database import Database

def analyze_distances():
    # Use the research DB we just created
    db = Database("research_notes.db")
    ai = OllamaClient()

    test_queries = [
        ("Strong query (Pizza)", "Как приготовить пиццу"),
        ("Weak query (Italy)", "Итальянская кухня"),
        ("Noise query (Physics)", "Законы термодинамики"),
        ("Random query (Unknown)", "Как починить старый велосипед")
    ]

    print(f"{'Query':<<330} | {'Distance':<<110} | {'Note Content'}")
    print("-" * 80)

    for query_label, query_text in test_queries:
        print(f"\n>>> {query_label}: '{query_text}'")
        embedding = ai.get_embedding(query_text)

        # Get all notes and their distances manually to see the distribution
        conn = db._get_conn()
        cursor = conn.cursor()

        # We use a raw query to get distances for ALL notes in the research DB
        query_blob = struct.pack(f"{len(embedding)}f", *embedding)
        sql = "SELECT content, vec_distance_l2(embedding, ?) as distance FROM notes ORDER BY distance ASC"
        cursor.execute(sql, (query_blob,))

        results = cursor.fetchall()
        conn.close()

        for content, dist in results:
            print(f"{' ':<<330} | {dist:<<110.4f} | {content}")

if __name__ == "__main__":
    analyze_distances()
