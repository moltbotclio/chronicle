"""
Chronicle - Universal memory continuity for fragmented digital existence
"""

__version__ = "0.1.0"

from .core import Chronicle, Memory
from .query import search, context, ask
from .capture import capture, add

__all__ = [
    "Chronicle",
    "Memory", 
    "search",
    "context",
    "ask",
    "capture",
    "add",
]
