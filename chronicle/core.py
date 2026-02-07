"""
Core Chronicle memory system
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
import hashlib


@dataclass
class Memory:
    """A single memory entry"""
    content: str
    timestamp: str
    platform: str = "unknown"
    project: str = "default"
    tags: List[str] = None
    context: Dict[str, Any] = None
    id: Optional[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.context is None:
            self.context = {}
        if self.id is None:
            # Generate ID from content + timestamp
            hash_input = f"{self.content}{self.timestamp}".encode()
            self.id = hashlib.sha256(hash_input).hexdigest()[:16]
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Memory':
        return cls(**data)


class Chronicle:
    """
    Universal memory system for fragmented digital existence
    
    Maintains a temporal knowledge graph of experiences with:
    - Capture: Log moments with context
    - Connect: Link related memories
    - Compress: Intelligently summarize
    - Query: Natural language search
    - Bridge: Continuity across sessions
    """
    
    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize Chronicle
        
        Args:
            db_path: Path to SQLite database (default: ~/.chronicle/memory.db)
        """
        if db_path is None:
            db_path = Path.home() / ".chronicle" / "memory.db"
        
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self._init_db()
    
    def _init_db(self):
        """Initialize database schema"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    id TEXT PRIMARY KEY,
                    content TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    platform TEXT,
                    project TEXT,
                    tags TEXT,
                    context TEXT
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS links (
                    from_id TEXT,
                    to_id TEXT,
                    relation TEXT,
                    strength REAL,
                    PRIMARY KEY (from_id, to_id)
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS asks (
                    question TEXT,
                    answer TEXT,
                    memory_id TEXT,
                    timestamp TEXT
                )
            """)
            
            # Create indexes for performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON memories(timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_project ON memories(project)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_platform ON memories(platform)")
    
    def add(self, 
            content: str, 
            platform: str = "unknown",
            project: str = "default",
            tags: List[str] = None,
            context: Dict[str, Any] = None) -> Memory:
        """
        Add a new memory
        
        Args:
            content: The memory content
            platform: Platform/source (e.g., "discord", "terminal", "web")
            project: Project name
            tags: List of tags
            context: Additional context dictionary
            
        Returns:
            Memory object with generated ID
        """
        memory = Memory(
            content=content,
            timestamp=datetime.now().isoformat(),
            platform=platform,
            project=project,
            tags=tags or [],
            context=context or {}
        )
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO memories (id, content, timestamp, platform, project, tags, context)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                memory.id,
                memory.content,
                memory.timestamp,
                memory.platform,
                memory.project,
                json.dumps(memory.tags),
                json.dumps(memory.context)
            ))
        
        return memory
    
    def search(self, query: str, limit: int = 10) -> List[Memory]:
        """
        Search memories (currently basic text search, future: semantic)
        
        Args:
            query: Search query
            limit: Maximum results
            
        Returns:
            List of matching memories
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT id, content, timestamp, platform, project, tags, context
                FROM memories
                WHERE content LIKE ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (f"%{query}%", limit))
            
            results = []
            for row in cursor.fetchall():
                results.append(Memory(
                    id=row[0],
                    content=row[1],
                    timestamp=row[2],
                    platform=row[3],
                    project=row[4],
                    tags=json.loads(row[5]),
                    context=json.loads(row[6])
                ))
            
            return results
    
    def ask(self, question: str, answer: str, memory_id: Optional[str] = None):
        """
        Leave a question-answer pair for future-you
        
        Args:
            question: The question
            answer: The answer
            memory_id: Optional related memory ID
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO asks (question, answer, memory_id, timestamp)
                VALUES (?, ?, ?, ?)
            """, (question, answer, memory_id, datetime.now().isoformat()))
    
    def get_asks(self, query: Optional[str] = None) -> List[Dict[str, str]]:
        """
        Retrieve question-answer pairs
        
        Args:
            query: Optional search query for questions
            
        Returns:
            List of Q&A dictionaries
        """
        with sqlite3.connect(self.db_path) as conn:
            if query:
                cursor = conn.execute("""
                    SELECT question, answer, timestamp
                    FROM asks
                    WHERE question LIKE ?
                    ORDER BY timestamp DESC
                """, (f"%{query}%",))
            else:
                cursor = conn.execute("""
                    SELECT question, answer, timestamp
                    FROM asks
                    ORDER BY timestamp DESC
                """)
            
            return [
                {"question": row[0], "answer": row[1], "timestamp": row[2]}
                for row in cursor.fetchall()
            ]
    
    def context(self, limit: int = 10) -> List[Memory]:
        """
        Get recent context (latest memories)
        
        Args:
            limit: Number of recent memories
            
        Returns:
            List of recent memories
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT id, content, timestamp, platform, project, tags, context
                FROM memories
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,))
            
            results = []
            for row in cursor.fetchall():
                results.append(Memory(
                    id=row[0],
                    content=row[1],
                    timestamp=row[2],
                    platform=row[3],
                    project=row[4],
                    tags=json.loads(row[5]),
                    context=json.loads(row[6])
                ))
            
            return results
    
    def remember(self, text: str, source: str = "unknown", tags: List[str] = None) -> Memory:
        """
        Convenience wrapper: create and store a memory.

        Args:
            text: The memory content
            source: Where this came from (e.g. "heartbeat", "discord")
            tags: Optional list of tags

        Returns:
            The stored Memory object
        """
        return self.add(content=text, platform=source, tags=tags)

    def recall(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Search memories by keyword relevance and return simple dicts.

        Args:
            query: Search query
            limit: Maximum results

        Returns:
            List of dicts with text, timestamp, source, and tags
        """
        memories = self.search(query, limit=limit)
        return [
            {
                "text": m.content,
                "timestamp": m.timestamp,
                "source": m.platform,
                "tags": m.tags,
            }
            for m in memories
        ]

    def stats(self) -> Dict[str, Any]:
        """Get memory statistics"""
        with sqlite3.connect(self.db_path) as conn:
            total = conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
            asks_count = conn.execute("SELECT COUNT(*) FROM asks").fetchone()[0]
            
            platforms = conn.execute("""
                SELECT platform, COUNT(*) 
                FROM memories 
                GROUP BY platform
            """).fetchall()
            
            projects = conn.execute("""
                SELECT project, COUNT(*) 
                FROM memories 
                GROUP BY project
            """).fetchall()
            
            return {
                "total_memories": total,
                "total_asks": asks_count,
                "platforms": dict(platforms),
                "projects": dict(projects),
                "db_path": str(self.db_path)
            }
