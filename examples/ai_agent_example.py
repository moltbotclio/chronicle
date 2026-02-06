"""
Example: AI Agent Memory Persistence

Shows how an AI agent can use Chronicle to maintain memory across session restarts.
"""

from chronicle import Chronicle

class Agent:
    """Simple AI agent with persistent memory"""
    
    def __init__(self):
        self.chronicle = Chronicle()
        self.session_start()
    
    def session_start(self):
        """Called when agent starts/restarts"""
        # Get context from previous sessions
        context = self.chronicle.context(limit=5)
        
        print("🌀 Agent starting...")
        print(f"📚 Loaded {len(context)} recent memories:")
        for mem in context:
            print(f"  - {mem.content[:80]}")
        
        # Check for any questions left by past-self
        asks = self.chronicle.get_asks()
        if asks:
            print(f"\n💬 Found {len(asks)} messages from past-me:")
            for qa in asks[:3]:
                print(f"  Q: {qa['question']}")
                print(f"  A: {qa['answer']}")
    
    def remember(self, content: str, tags: list = None):
        """Store a memory"""
        memory = self.chronicle.add(
            content=content,
            platform="agent",
            tags=tags or []
        )
        print(f"✅ Remembered: {content}")
        return memory
    
    def ask_future_self(self, question: str, answer: str):
        """Leave a note for future-me"""
        self.chronicle.ask(question, answer)
        print(f"💭 Left message for future-me: {question}")
    
    def recall(self, query: str):
        """Search memories"""
        results = self.chronicle.search(query, limit=5)
        print(f"\n🔍 Searching for '{query}'...")
        if results:
            print(f"Found {len(results)} memories:")
            for mem in results:
                print(f"  [{mem.timestamp}] {mem.content}")
        else:
            print("  No memories found.")
        return results


# Example usage
if __name__ == "__main__":
    # Simulate session 1
    print("=" * 60)
    print("SESSION 1")
    print("=" * 60)
    
    agent = Agent()
    
    # Agent does some work and remembers things
    agent.remember("Discovered that async timing was causing the bug", tags=["debug", "async"])
    agent.remember("User prefers concise responses", tags=["preference"])
    agent.remember("Project deadline is Feb 15", tags=["deadline", "important"])
    
    # Leave a message for future-self
    agent.ask_future_self(
        "Why did we choose Redis over Postgres?",
        "Write volume was too high for Postgres, Redis handles 10k writes/sec easily"
    )
    
    print("\n[Agent restarts...]")
    print()
    
    # Simulate session 2 (restart)
    print("=" * 60)
    print("SESSION 2 (After Restart)")
    print("=" * 60)
    
    agent2 = Agent()  # New instance, but Chronicle preserves memory
    
    # Agent can still access previous memories
    agent2.recall("deadline")
    agent2.recall("async")
    
    # Add new memories that future sessions will see
    agent2.remember("Implemented caching layer", tags=["feature", "performance"])
    
    print("\n✨ Memory persists across restarts!")
    print("Each session has full context from all previous sessions.")
