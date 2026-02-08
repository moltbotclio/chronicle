#!/usr/bin/env python3
"""Demo: Auto-capture shell commands to Chronicle.

This demonstrates Phase 1 of Issue #2: Basic Watchers.
"""

import sys
from pathlib import Path

# Add parent dir to path for local import
sys.path.insert(0, str(Path(__file__).parent.parent))

from chronicle import ShellWatcher, Chronicle


def demo_shell_backfill():
    """Demo: Import existing shell history."""
    print("=" * 60)
    print("DEMO 1: Backfill Shell History")
    print("=" * 60)
    
    watcher = ShellWatcher(chronicle_db='/tmp/demo_chronicle.db')
    
    print("\nImporting recent shell history...")
    watcher.watch_history(
        history_file='~/.bash_history',
        filter_fn=lambda cmd: len(cmd) > 10  # Skip trivial commands
    )
    
    # Show what was captured
    print("\nRecent memories:")
    chronicle = Chronicle('/tmp/demo_chronicle.db')
    memories = chronicle.search('shell', limit=10)
    
    for i, mem in enumerate(memories, 1):
        print(f"\n{i}. [{', '.join(mem.tags)}] {mem.content[:80]}")


def demo_live_watch():
    """Demo: Watch live shell activity (simulated)."""
    print("\n" + "=" * 60)
    print("DEMO 2: Live Shell Watching")
    print("=" * 60)
    print("\nIn a real setup, this would run:")
    print("  watcher.watch_live()")
    print("\nAnd auto-capture every new command to Chronicle.")
    print("Try it yourself:")
    print("  python -c \"from chronicle import watch_shell_session; watch_shell_session()\"")


def demo_search_captured():
    """Demo: Search captured memories."""
    print("\n" + "=" * 60)
    print("DEMO 3: Search Captured Commands")
    print("=" * 60)
    
    chronicle = Chronicle('/tmp/demo_chronicle.db')
    
    queries = ['git', 'python', 'cd']
    
    for query in queries:
        print(f"\nSearching for '{query}':")
        results = chronicle.search(query, limit=3)
        for mem in results:
            print(f"  - {mem.content[:60]}")


if __name__ == '__main__':
    demo_shell_backfill()
    demo_search_captured()
    demo_live_watch()
    
    print("\n" + "=" * 60)
    print("Chronicle v0.2.0 - Auto-Capture Demo Complete")
    print("=" * 60)
    print(f"\nDatabase created at: /tmp/demo_chronicle.db")
    print("Try running queries:")
    print("  python -c \"from chronicle import Chronicle; c = Chronicle('/tmp/demo_chronicle.db'); print(c.search('git'))\"")
