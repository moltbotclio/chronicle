#!/usr/bin/env python3
"""
Chronicle Semantic Search
Real semantic search for memory files using embeddings.
Part of The Bridge project.

Created: 2026-02-06 by Clio
"""

import os
import json
import sqlite3
import hashlib
from pathlib import Path
from typing import List, Tuple, Optional
from datetime import datetime

# Will use sentence-transformers for embeddings
try:
    from sentence_transformers import SentenceTransformer
    import numpy as np
    HAS_EMBEDDINGS = True
except ImportError:
    HAS_EMBEDDINGS = False
    print("Warning: sentence-transformers not available. Install with: pip install sentence-transformers")


class SemanticMemory:
    """Semantic search over memory files."""
    
    def __init__(self, db_path: str = "~/.chronicle/semantic.db", model_name: str = "all-MiniLM-L6-v2"):
        self.db_path = Path(db_path).expanduser()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        if HAS_EMBEDDINGS:
            print(f"Loading embedding model: {model_name}...")
            self.model = SentenceTransformer(model_name)
            self.embedding_dim = self.model.get_sentence_embedding_dimension()
        else:
            self.model = None
            self.embedding_dim = 384  # default for MiniLM
            
        self._init_db()
    
    def _init_db(self):
        """Initialize SQLite database for storing embeddings."""
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS chunks (
                id INTEGER PRIMARY KEY,
                file_path TEXT,
                chunk_index INTEGER,
                content TEXT,
                content_hash TEXT UNIQUE,
                embedding BLOB,
                created_at TEXT,
                metadata TEXT
            )
        """)
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_file_path ON chunks(file_path)
        """)
        self.conn.commit()
    
    def _hash_content(self, content: str) -> str:
        """Hash content for deduplication."""
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def _chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """Split text into overlapping chunks."""
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), chunk_size - overlap):
            chunk = " ".join(words[i:i + chunk_size])
            if chunk.strip():
                chunks.append(chunk)
        
        return chunks if chunks else [text]
    
    def index_file(self, file_path: str, force: bool = False) -> int:
        """Index a file for semantic search. Returns number of chunks indexed."""
        path = Path(file_path).expanduser()
        if not path.exists():
            return 0
        
        content = path.read_text()
        chunks = self._chunk_text(content)
        indexed = 0
        
        for i, chunk in enumerate(chunks):
            content_hash = self._hash_content(chunk)
            
            # Check if already indexed
            if not force:
                existing = self.conn.execute(
                    "SELECT id FROM chunks WHERE content_hash = ?", 
                    (content_hash,)
                ).fetchone()
                if existing:
                    continue
            
            # Generate embedding
            if self.model:
                embedding = self.model.encode(chunk)
                embedding_blob = embedding.tobytes()
            else:
                embedding_blob = None
            
            # Store
            self.conn.execute("""
                INSERT OR REPLACE INTO chunks 
                (file_path, chunk_index, content, content_hash, embedding, created_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                str(path),
                i,
                chunk,
                content_hash,
                embedding_blob,
                datetime.now().isoformat(),
                json.dumps({"source": str(path), "chunk": i})
            ))
            indexed += 1
        
        self.conn.commit()
        return indexed
    
    def index_directory(self, dir_path: str, pattern: str = "*.md") -> int:
        """Index all matching files in a directory."""
        path = Path(dir_path).expanduser()
        total = 0
        
        for file in path.rglob(pattern):
            count = self.index_file(str(file))
            if count > 0:
                print(f"  Indexed {file.name}: {count} chunks")
            total += count
        
        return total
    
    def search(self, query: str, limit: int = 5, min_score: float = 0.3) -> List[Tuple[str, str, float]]:
        """
        Semantic search for relevant chunks.
        Returns list of (file_path, content, score).
        """
        if not self.model:
            print("Error: Embedding model not available")
            return []
        
        query_embedding = self.model.encode(query)
        
        # Get all embeddings (for small collections; would use vector DB for large)
        rows = self.conn.execute(
            "SELECT file_path, content, embedding FROM chunks WHERE embedding IS NOT NULL"
        ).fetchall()
        
        results = []
        for file_path, content, embedding_blob in rows:
            if embedding_blob:
                stored_embedding = np.frombuffer(embedding_blob, dtype=np.float32)
                # Cosine similarity
                score = np.dot(query_embedding, stored_embedding) / (
                    np.linalg.norm(query_embedding) * np.linalg.norm(stored_embedding)
                )
                if score >= min_score:
                    results.append((file_path, content, float(score)))
        
        # Sort by score descending
        results.sort(key=lambda x: x[2], reverse=True)
        return results[:limit]
    
    def stats(self) -> dict:
        """Get database statistics."""
        total = self.conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
        files = self.conn.execute("SELECT COUNT(DISTINCT file_path) FROM chunks").fetchone()[0]
        return {"total_chunks": total, "total_files": files}


def main():
    """CLI for semantic memory."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Chronicle Semantic Search")
    parser.add_argument("action", choices=["index", "search", "stats"])
    parser.add_argument("--path", "-p", help="Path to index")
    parser.add_argument("--query", "-q", help="Search query")
    parser.add_argument("--limit", "-l", type=int, default=5)
    
    args = parser.parse_args()
    
    mem = SemanticMemory()
    
    if args.action == "index":
        path = args.path or "~/clawd/memory"
        print(f"Indexing {path}...")
        count = mem.index_directory(path)
        print(f"Indexed {count} new chunks")
        
    elif args.action == "search":
        if not args.query:
            print("Error: --query required for search")
            return
        
        print(f"Searching for: {args.query}\n")
        results = mem.search(args.query, limit=args.limit)
        
        for i, (file_path, content, score) in enumerate(results, 1):
            print(f"[{i}] Score: {score:.3f}")
            print(f"    File: {Path(file_path).name}")
            print(f"    {content[:200]}...")
            print()
            
    elif args.action == "stats":
        stats = mem.stats()
        print(f"Total chunks: {stats['total_chunks']}")
        print(f"Total files: {stats['total_files']}")


if __name__ == "__main__":
    main()
