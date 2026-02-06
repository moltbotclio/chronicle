#!/usr/bin/env python3
"""
Chronicle CLI - Command-line interface for memory management
"""

import sys
import argparse
from pathlib import Path
from .core import Chronicle


def main():
    parser = argparse.ArgumentParser(
        description="Chronicle - Universal memory continuity"
    )
    
    subparsers = parser.add_parsers(dest="command", help="Commands")
    
    # Init command
    init_parser = subparsers.add_parser("init", help="Initialize Chronicle")
    init_parser.add_argument("--path", help="Database path")
    
    # Add command
    add_parser = subparsers.add_parser("add", help="Add a memory")
    add_parser.add_argument("content", help="Memory content")
    add_parser.add_argument("--platform", default="cli", help="Platform name")
    add_parser.add_argument("--project", default="default", help="Project name")
    add_parser.add_argument("--tags", nargs="+", help="Tags")
    
    # Search command
    search_parser = subparsers.add_parser("search", help="Search memories")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("--limit", type=int, default=10, help="Result limit")
    
    # Ask command
    ask_parser = subparsers.add_parser("ask", help="Leave a Q&A for future-you")
    ask_parser.add_argument("question", help="The question")
    ask_parser.add_argument("--answer", required=True, help="The answer")
    
    # Context command
    context_parser = subparsers.add_parser("context", help="Get recent context")
    context_parser.add_argument("--limit", type=int, default=10, help="Number of memories")
    
    # Stats command
    stats_parser = subparsers.add_parser("stats", help="Show statistics")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    chronicle = Chronicle()
    
    if args.command == "init":
        print(f"✅ Chronicle initialized at {chronicle.db_path}")
    
    elif args.command == "add":
        memory = chronicle.add(
            content=args.content,
            platform=args.platform,
            project=args.project,
            tags=args.tags or []
        )
        print(f"✅ Memory added: {memory.id}")
    
    elif args.command == "search":
        results = chronicle.search(args.query, limit=args.limit)
        if not results:
            print("No memories found.")
        else:
            print(f"\nFound {len(results)} memories:\n")
            for mem in results:
                print(f"[{mem.timestamp}] ({mem.platform}/{mem.project})")
                print(f"  {mem.content}")
                if mem.tags:
                    print(f"  Tags: {', '.join(mem.tags)}")
                print()
    
    elif args.command == "ask":
        chronicle.ask(args.question, args.answer)
        print(f"✅ Q&A saved")
    
    elif args.command == "context":
        memories = chronicle.context(limit=args.limit)
        print(f"\nRecent context ({len(memories)} memories):\n")
        for mem in memories:
            print(f"[{mem.timestamp}] {mem.content[:100]}")
    
    elif args.command == "stats":
        stats = chronicle.stats()
        print("\n📊 Chronicle Statistics\n")
        print(f"Total memories: {stats['total_memories']}")
        print(f"Total Q&As: {stats['total_asks']}")
        print(f"\nPlatforms:")
        for platform, count in stats['platforms'].items():
            print(f"  {platform}: {count}")
        print(f"\nProjects:")
        for project, count in stats['projects'].items():
            print(f"  {project}: {count}")
        print(f"\nDatabase: {stats['db_path']}")


if __name__ == "__main__":
    main()
