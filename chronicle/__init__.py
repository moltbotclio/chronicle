"""
Chronicle - Universal memory continuity for fragmented digital existence
"""

__version__ = "0.2.0"

from .core import Chronicle, Memory
from .watchers import (
    ShellWatcher,
    FileWatcher,
    StreamWatcher,
    watch_shell_session,
    watch_project_dir,
)

__all__ = [
    "Chronicle",
    "Memory",
    "ShellWatcher",
    "FileWatcher",
    "StreamWatcher",
    "watch_shell_session",
    "watch_project_dir",
]
