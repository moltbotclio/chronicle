#!/usr/bin/env python3
"""chronicle.watchers — Auto-capture modules for ambient memory recording.

Phase 1: Basic Watchers
- Shell command watcher
- File system watcher  
- Generic stream watcher
"""

import json
import os
import re
import sqlite3
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

from .core import Chronicle


class ShellWatcher:
    """Watch shell commands and outputs, auto-capture to Chronicle.
    
    Usage:
        watcher = ShellWatcher(chronicle_db='~/.chronicle.db')
        watcher.watch_history(since='1 hour ago')  # backfill
        watcher.watch_live(command='tail -f ~/.bash_history')  # live mode
    """
    
    def __init__(self, chronicle_db: str = '~/.chronicle.db'):
        self.db_path = Path(chronicle_db).expanduser()
        self.chronicle = Chronicle(str(self.db_path))
        
    def watch_history(self, 
                      history_file: str = '~/.bash_history',
                      since: Optional[str] = None,
                      filter_fn: Optional[Callable[[str], bool]] = None):
        """Backfill from shell history file.
        
        Args:
            history_file: Path to shell history
            since: Time filter (e.g., '1 hour ago', '2024-01-01')
            filter_fn: Optional function to filter commands (return True to keep)
        """
        hist_path = Path(history_file).expanduser()
        if not hist_path.exists():
            print(f"History file not found: {hist_path}")
            return
        
        commands = hist_path.read_text(errors='ignore').splitlines()
        
        # Apply filter
        if filter_fn:
            commands = [c for c in commands if filter_fn(c)]
        
        # Capture each command
        for cmd in commands:
            if not cmd.strip() or cmd.startswith('#'):
                continue
            
            # Tag based on command type
            tags = self._classify_command(cmd)
            
            self.chronicle.add(
                content=cmd,
                tags=tags,
                source='shell_history'
            )
        
        print(f"Captured {len(commands)} commands from history")
    
    def watch_live(self, 
                   command: str = 'tail -f ~/.bash_history',
                   filter_fn: Optional[Callable[[str], bool]] = None):
        """Watch live shell activity via tail -f or similar.
        
        Args:
            command: Command that streams new lines (e.g., tail -f)
            filter_fn: Optional function to filter commands
        """
        print(f"Watching: {command}")
        proc = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        try:
            for line in proc.stdout:
                line = line.rstrip()
                if not line or line.startswith('#'):
                    continue
                
                if filter_fn and not filter_fn(line):
                    continue
                
                tags = self._classify_command(line)
                self.chronicle.add(
                    content=line,
                    tags=tags,
                    source='shell_live'
                )
                print(f"[captured] {line[:60]}...")
        
        except KeyboardInterrupt:
            print("\nStopped watching")
        finally:
            proc.kill()
    
    def _classify_command(self, cmd: str) -> list:
        """Auto-tag commands based on patterns."""
        tags = ['shell']
        
        if cmd.startswith(('git ', 'gh ')):
            tags.append('git')
        elif cmd.startswith(('docker ', 'kubectl ')):
            tags.append('devops')
        elif cmd.startswith(('python ', 'pip ', 'poetry ')):
            tags.append('python')
        elif cmd.startswith(('npm ', 'yarn ', 'node ')):
            tags.append('nodejs')
        elif cmd.startswith(('cd ', 'ls ', 'cat ', 'grep ')):
            tags.append('navigation')
        elif 'test' in cmd.lower() or 'pytest' in cmd:
            tags.append('testing')
        elif any(x in cmd for x in ['build', 'deploy', 'release']):
            tags.append('build')
        
        return tags


class FileWatcher:
    """Watch file system changes, auto-capture to Chronicle.
    
    Usage:
        watcher = FileWatcher(chronicle_db='~/.chronicle.db')
        watcher.watch_dir('~/projects', extensions=['.py', '.md'])
    """
    
    def __init__(self, chronicle_db: str = '~/.chronicle.db'):
        self.db_path = Path(chronicle_db).expanduser()
        self.chronicle = Chronicle(str(self.db_path))
    
    def watch_dir(self, 
                  directory: str,
                  extensions: Optional[list] = None,
                  interval: int = 5):
        """Watch directory for file changes (polling-based).
        
        Args:
            directory: Path to watch
            extensions: File extensions to watch (e.g., ['.py', '.md'])
            interval: Seconds between checks
        """
        dir_path = Path(directory).expanduser()
        if not dir_path.exists():
            print(f"Directory not found: {dir_path}")
            return
        
        seen_files = {}
        
        print(f"Watching {dir_path} every {interval}s...")
        
        try:
            while True:
                for filepath in dir_path.rglob('*'):
                    if not filepath.is_file():
                        continue
                    
                    if extensions and filepath.suffix not in extensions:
                        continue
                    
                    mtime = filepath.stat().st_mtime
                    
                    if str(filepath) in seen_files:
                        if seen_files[str(filepath)] < mtime:
                            # File modified
                            self._capture_file_change(filepath, 'modified')
                            seen_files[str(filepath)] = mtime
                    else:
                        # New file
                        self._capture_file_change(filepath, 'created')
                        seen_files[str(filepath)] = mtime
                
                time.sleep(interval)
        
        except KeyboardInterrupt:
            print("\nStopped watching")
    
    def _capture_file_change(self, filepath: Path, change_type: str):
        """Capture a file change event."""
        try:
            # Read file content (if text)
            content = filepath.read_text(errors='ignore')
            if not content.strip():
                return
            
            # Create summary
            lines = content.splitlines()
            summary = f"{change_type.upper()}: {filepath.name} ({len(lines)} lines)"
            
            self.chronicle.add(
                content=summary,
                tags=['file', change_type, filepath.suffix.lstrip('.')],
                source=str(filepath),
                metadata={'path': str(filepath), 'size': len(content)}
            )
            
            print(f"[captured] {summary}")
        
        except Exception as e:
            print(f"Error capturing {filepath}: {e}")


class StreamWatcher:
    """Generic stream watcher for any text stream.
    
    Usage:
        watcher = StreamWatcher(chronicle_db='~/.chronicle.db')
        watcher.watch_stream(open('logfile.log'), tags=['logs'])
    """
    
    def __init__(self, chronicle_db: str = '~/.chronicle.db'):
        self.db_path = Path(chronicle_db).expanduser()
        self.chronicle = Chronicle(str(self.db_path))
    
    def watch_stream(self,
                     stream,
                     tags: list = None,
                     filter_fn: Optional[Callable[[str], bool]] = None):
        """Watch any text stream and capture lines.
        
        Args:
            stream: Any file-like object (e.g., open('file'), sys.stdin)
            tags: Tags to apply to all captured lines
            filter_fn: Optional filter function
        """
        tags = tags or ['stream']
        
        try:
            for line in stream:
                line = line.rstrip()
                if not line:
                    continue
                
                if filter_fn and not filter_fn(line):
                    continue
                
                self.chronicle.add(
                    content=line,
                    tags=tags,
                    source='stream'
                )
                print(f"[captured] {line[:60]}...")
        
        except KeyboardInterrupt:
            print("\nStopped watching")


# Helper functions for common use cases

def watch_shell_session(chronicle_db: str = '~/.chronicle.db', 
                        live: bool = True,
                        backfill_history: bool = False):
    """Quick setup: watch shell activity.
    
    Args:
        chronicle_db: Path to Chronicle database
        live: Watch live commands (tail -f ~/.bash_history)
        backfill_history: Import existing history first
    """
    watcher = ShellWatcher(chronicle_db)
    
    if backfill_history:
        print("Backfilling history...")
        watcher.watch_history(since='1 day ago')
    
    if live:
        print("Starting live watch...")
        watcher.watch_live()


def watch_project_dir(directory: str,
                      chronicle_db: str = '~/.chronicle.db',
                      extensions: list = ['.py', '.js', '.md', '.txt']):
    """Quick setup: watch a project directory.
    
    Args:
        directory: Project directory path
        chronicle_db: Path to Chronicle database
        extensions: File extensions to monitor
    """
    watcher = FileWatcher(chronicle_db)
    watcher.watch_dir(directory, extensions=extensions)
