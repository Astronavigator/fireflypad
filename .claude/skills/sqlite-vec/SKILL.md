---
name: sqlite-vec
description: Guide for using sqlite-vec, a vector search SQLite extension. Use when working with vector databases, semantic search, embeddings, similarity search, or RAG applications in SQLite. Covers creating vec0 virtual tables, inserting vectors, KNN queries, distance functions, and Python/Node.js integration.
license: MIT
metadata:
  author: Assistant
  version: "1.0"
  tags: [sqlite, vector-database, embeddings, semantic-search, rag, knn]
---

# sqlite-vec Skill

This skill provides comprehensive guidance for using **sqlite-vec**, a lightweight vector search SQLite extension that enables storing and querying vector embeddings directly in SQLite databases.

## What is sqlite-vec?

sqlite-vec is a vector search SQLite extension that:
- Stores and queries float32, int8, and binary vectors in `vec0` virtual tables
- Runs anywhere SQLite runs (Linux/MacOS/Windows, browsers with WASM, Raspberry Pis)
- Requires no external servers or dependencies
- Supports K-nearest neighbors (KNN) search with multiple distance metrics

## Installation

### Python
```bash
pip install sqlite-vec
```

### Node.js
```bash
npm install sqlite-vec
```

### Ruby
```bash
gem install sqlite-vec
```

### Go
```bash
go get -u github.com/asg017/sqlite-vec/bindings/go
```

### Rust
```bash
cargo add sqlite-vec
```

## Basic Usage

### 1. Load the Extension (Python)

```python
import sqlite3
import sqlite_vec
from sqlite_vec import serialize_float32

# Connect to database
db = sqlite3.connect(":memory:")  # or "my_vectors.db"

# Load extension
db.enable_load_extension(True)
sqlite_vec.load(db)
db.enable_load_extension(False)

# Verify installation
vec_version = db.execute("SELECT vec_version()").fetchone()[0]
print(f"sqlite-vec version: {vec_version}")
```

### 2. Create a Virtual Table

```sql
-- Create a vec0 virtual table for 768-dimensional float vectors
CREATE VIRTUAL TABLE vec_documents USING vec0(
    document_id INTEGER PRIMARY KEY,
    embedding FLOAT[768]
);
```

### 3. Insert Vectors

```python
# Serialize vectors for storage
embedding = [0.1, 0.2, 0.3, 0.4]  # Your 768-dim vector here
serialized = serialize_float32(embedding)

# Insert into table
db.execute(
    "INSERT INTO vec_documents(document_id, embedding) VALUES (?, ?)",
    [1, serialized]
)
db.commit()
```

### 4. Perform KNN Search

```python
# Query vector
query = [0.15, 0.25, 0.35, 0.45]  # Your query embedding
query_serialized = serialize_float32(query)

# KNN search - find 10 nearest neighbors
results = db.execute("""
    SELECT document_id, distance
    FROM vec_documents
    WHERE embedding MATCH ?
      AND k = 10
    ORDER BY distance
""", [query_serialized]).fetchall()

for doc_id, distance in results:
    print(f"Document {doc_id}: distance = {distance}")
```

## Advanced Table Creation

### With Distance Metrics

```sql
-- Use cosine similarity instead of default L2
CREATE VIRTUAL TABLE vec_items USING vec0(
    item_id INTEGER PRIMARY KEY,
    embedding FLOAT[768] distance_metric=cosine
);
```

Supported metrics: `l2` (default), `cosine`, `hamming` (bit vectors only)

### With Metadata Columns

```sql
CREATE VIRTUAL TABLE vec_knowledge_base USING vec0(
    doc_id INTEGER PRIMARY KEY,
    
    -- Partition keys for sharding (optional)
    organization_id INTEGER partition key,
    
    -- Vector column with cosine distance
    content_embedding FLOAT[768] distance_metric=cosine,
    
    -- Metadata columns (filterable in KNN queries)
    document_type TEXT,
    language TEXT,
    word_count INTEGER,
    is_public BOOLEAN,
    
    -- Auxiliary columns (storage only, not filterable)
    +title TEXT,
    +full_content TEXT,
    +url TEXT
);
```

### Vector Types

```sql
-- Float32 vectors (most common)
CREATE VIRTUAL TABLE vec_float USING vec0(embedding FLOAT[768]);

-- Int8 vectors (smaller, quantized)
CREATE VIRTUAL TABLE vec_int8 USING vec0(embedding INT8[768]);

-- Binary/bit vectors (smallest)
CREATE VIRTUAL TABLE vec_binary USING vec0(embedding BIT[768]);
```

## Query Patterns

### Basic KNN Query

```sql
-- Find 10 nearest neighbors
SELECT document_id, distance
FROM vec_documents
WHERE embedding MATCH '[0.1, 0.2, 0.3, ...]'
  AND k = 10
ORDER BY distance;
```

### With Metadata Filtering

```sql
-- Search within specific category
SELECT doc_id, distance
FROM vec_knowledge_base
WHERE content_embedding MATCH ?
  AND k = 10
  AND document_type = 'article'
  AND language = 'en'
  AND is_public = 1
ORDER BY distance;
```

### Join with Source Table

```sql
-- Get full document content with similarity scores
WITH knn_matches AS (
    SELECT document_id, distance
    FROM vec_documents
    WHERE embedding MATCH ?
      AND k = 10
)
SELECT 
    d.id,
    d.title,
    d.content,
    k.distance
FROM knn_matches k
LEFT JOIN documents d ON d.id = k.document_id
ORDER BY k.distance;
```

### Multi-tenant Search

```sql
-- Search within user's documents only
SELECT doc_id, distance
FROM vec_user_docs
WHERE embedding MATCH ?
  AND k = 10
  AND user_id = 123
ORDER BY distance;
```

## Vector Operations

### Constructor Functions

```sql
-- Create float32 vector from JSON or BLOB
SELECT vec_f32('[0.1, 0.2, 0.3]');

-- Create int8 vector
SELECT vec_int8('[1, 2, 3, 4]');

-- Create binary vector
SELECT vec_bit(X'F0');
```

### Utility Functions

```sql
-- Get vector length (dimensions)
SELECT vec_length('[0.1, 0.2, 0.3]');  -- Returns 3

-- Get vector type
SELECT vec_type(vec_f32('[0.1, 0.2]'));  -- Returns 'float32'

-- Convert vector to JSON
SELECT vec_to_json(vec_f32(X'AABBCCDD'));

-- Slice a vector
SELECT vec_slice('[1, 2, 3, 4]', 0, 2);  -- Returns [1, 2]

-- Normalize a vector
SELECT vec_normalize('[3, 4]');  -- Returns [0.6, 0.8]
```

### Distance Functions

```sql
-- L2 (Euclidean) distance
SELECT vec_distance_L2('[0, 0]', '[3, 4]');  -- Returns 5.0

-- Cosine distance
SELECT vec_distance_cosine(vec1, vec2);

-- Hamming distance (for bit vectors)
SELECT vec_distance_hamming(bit_vec1, bit_vec2);
```

### Vector Arithmetic

```sql
-- Add vectors
SELECT vec_add('[0.1, 0.2]', '[0.3, 0.4]');  -- Returns [0.4, 0.6]

-- Subtract vectors
SELECT vec_sub('[0.5, 0.5]', '[0.1, 0.2]');  -- Returns [0.4, 0.3]
```

### Quantization

```sql
-- Quantize to binary
SELECT vec_quantize_binary('[0.1, -0.2, 0.3, -0.4]');

-- Quantize to int8
SELECT vec_quantize_i8('[0.1, 0.2, 0.3]', 0, 3);
```

## Complete Python Example

```python
import sqlite3
import sqlite_vec
from sqlite_vec import serialize_float32
from typing import List

# Setup
db = sqlite3.connect("semantic_search.db")
db.enable_load_extension(True)
sqlite_vec.load(db)
db.enable_load_extension(False)

# Create tables
db.execute("""
    CREATE TABLE documents (
        id INTEGER PRIMARY KEY,
        title TEXT,
        content TEXT
    )
""")

db.execute("""
    CREATE VIRTUAL TABLE vec_documents USING vec0(
        document_id INTEGER PRIMARY KEY,
        embedding FLOAT[384] distance_metric=cosine
    )
""")

# Insert sample documents
documents = [
    (1, "SQLite Introduction", "SQLite is a C library..."),
    (2, "Vector Databases", "Vector databases store embeddings..."),
    (3, "Machine Learning", "ML models can generate embeddings..."),
]

for doc_id, title, content in documents:
    db.execute(
        "INSERT INTO documents (id, title, content) VALUES (?, ?, ?)",
        [doc_id, title, content]
    )
    # In real app, generate embedding from content
    embedding = [0.1] * 384  # Placeholder
    db.execute(
        "INSERT INTO vec_documents (document_id, embedding) VALUES (?, ?)",
        [doc_id, serialize_float32(embedding)]
    )

db.commit()

# Search
query_embedding = [0.1] * 384  # Your query embedding
results = db.execute("""
    SELECT d.title, d.content, v.distance
    FROM vec_documents v
    JOIN documents d ON d.id = v.document_id
    WHERE v.embedding MATCH ?
      AND v.k = 5
    ORDER BY v.distance
""", [serialize_float32(query_embedding)]).fetchall()

for title, content, distance in results:
    print(f"{title} (distance: {distance:.4f})")
```

## Integration with Embedding APIs

### OpenAI

```python
from openai import OpenAI
from sqlite_vec import serialize_float32

client = OpenAI()

# Generate embedding
response = client.embeddings.create(
    input="Your text here",
    model="text-embedding-3-small"
)
embedding = response.data[0].embedding

# Store in sqlite-vec
db.execute(
    "INSERT INTO vec_documents (document_id, embedding) VALUES (?, ?)",
    [doc_id, serialize_float32(embedding)]
)
```

### Sentence Transformers (Local)

```python
from sentence_transformers import SentenceTransformer
from sqlite_vec import serialize_float32

model = SentenceTransformer('all-MiniLM-L6-v2')

# Generate embedding
text = "Your document text here"
embedding = model.encode(text).tolist()

# Store
db.execute(
    "INSERT INTO vec_documents (document_id, embedding) VALUES (?, ?)",
    [doc_id, serialize_float32(embedding)]
)
```

## Performance Tips

1. **Use partition keys** for multi-tenant or temporally-filtered queries
2. **Keep k reasonable** (10-100 for most use cases)
3. **Filter with metadata columns** when possible
4. **Choose appropriate distance metric** for your embeddings
5. **Batch operations** in transactions
6. **Use auxiliary columns** for large data not needed in filtering
7. **Ensure partition keys have 100+ vectors** per unique value

## Common Use Cases

### Semantic Search
```sql
-- Find documents similar to query
SELECT document_id, distance
FROM vec_documents
WHERE embedding MATCH ?
  AND k = 10
ORDER BY distance;
```

### Recommendation System
```sql
-- Find similar products
SELECT product_id, distance
FROM vec_products
WHERE embedding MATCH ?
  AND k = 20
  AND category = 'electronics'
  AND price < 1000
ORDER BY distance;
```

### RAG (Retrieval-Augmented Generation)
```python
# 1. Embed user query
query_embedding = get_embedding(user_query)

# 2. Retrieve relevant context
context_docs = db.execute("""
    SELECT d.content
    FROM vec_documents v
    JOIN documents d ON d.id = v.document_id
    WHERE v.embedding MATCH ?
      AND v.k = 5
    ORDER BY v.distance
""", [serialize_float32(query_embedding)]).fetchall()

# 3. Use context in LLM prompt
context = "\n".join([doc[0] for doc in context_docs])
prompt = f"Context: {context}\n\nQuestion: {user_query}"
```

## Resources

- **Official Documentation**: https://alexgarcia.xyz/sqlite-vec
- **GitHub Repository**: https://github.com/asg017/sqlite-vec
- **Python Package**: https://pypi.org/project/sqlite-vec/
- **API Reference**: https://alexgarcia.xyz/sqlite-vec/api-reference.html
