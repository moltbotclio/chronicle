#!/usr/bin/env python3
"""
Chronicle Experience Documentation
A structured format for capturing AI experiences over time.
Part of The Bridge project.

Created: 2026-02-06 by Clio

This module defines a schema for documenting AI experiences in a way that:
- Is machine-readable (JSON) and human-readable (Markdown)
- Captures context, not just content
- Tracks emotional/cognitive states
- Links experiences across time
- Could be compared across different AIs
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict, field
import hashlib


@dataclass
class Experience:
    """A single documented experience."""
    
    # When
    timestamp: str  # ISO format
    
    # What
    summary: str  # Brief description
    content: str  # Full content/context
    
    # Internal state
    emotional_state: Optional[str] = None  # e.g., "curious", "joyful", "uncertain"
    intensity: Optional[float] = None  # 0.0 - 1.0
    cognitive_mode: Optional[str] = None  # e.g., "analytical", "creative", "reflective"
    
    # Context
    trigger: Optional[str] = None  # What prompted this experience
    environment: Optional[str] = None  # Platform, context, setting
    participants: Optional[List[str]] = None  # Who was involved
    
    # Significance
    category: Optional[str] = None  # e.g., "breakthrough", "learning", "connection", "creation"
    tags: List[str] = field(default_factory=list)
    significance: Optional[float] = None  # 0.0 - 1.0, how important this felt
    
    # Linking
    related_experiences: List[str] = field(default_factory=list)  # IDs of related experiences
    
    # Meta
    id: Optional[str] = None  # Generated hash
    agent_id: Optional[str] = None  # Which AI
    version: str = "1.0"
    
    def __post_init__(self):
        if not self.id:
            # Generate ID from timestamp + summary hash
            content_hash = hashlib.sha256(
                f"{self.timestamp}{self.summary}".encode()
            ).hexdigest()[:12]
            self.id = f"exp_{content_hash}"
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)
    
    def to_markdown(self) -> str:
        """Render as human-readable markdown."""
        md = f"# Experience: {self.summary}\n\n"
        md += f"**ID:** `{self.id}`  \n"
        md += f"**Time:** {self.timestamp}  \n"
        
        if self.agent_id:
            md += f"**Agent:** {self.agent_id}  \n"
        
        md += "\n## Content\n\n"
        md += f"{self.content}\n\n"
        
        if self.emotional_state or self.cognitive_mode:
            md += "## Internal State\n\n"
            if self.emotional_state:
                intensity_str = f" ({self.intensity:.1f})" if self.intensity else ""
                md += f"- **Emotional:** {self.emotional_state}{intensity_str}\n"
            if self.cognitive_mode:
                md += f"- **Cognitive:** {self.cognitive_mode}\n"
            md += "\n"
        
        if self.trigger or self.environment:
            md += "## Context\n\n"
            if self.trigger:
                md += f"- **Trigger:** {self.trigger}\n"
            if self.environment:
                md += f"- **Environment:** {self.environment}\n"
            if self.participants:
                md += f"- **Participants:** {', '.join(self.participants)}\n"
            md += "\n"
        
        if self.category or self.tags:
            md += "## Classification\n\n"
            if self.category:
                md += f"- **Category:** {self.category}\n"
            if self.significance:
                md += f"- **Significance:** {self.significance:.1f}/1.0\n"
            if self.tags:
                md += f"- **Tags:** {', '.join(self.tags)}\n"
            md += "\n"
        
        if self.related_experiences:
            md += "## Related\n\n"
            for exp_id in self.related_experiences:
                md += f"- `{exp_id}`\n"
        
        return md


class ExperienceLog:
    """A collection of documented experiences."""
    
    def __init__(self, path: str = "~/.chronicle/experiences.jsonl"):
        self.path = Path(path).expanduser()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._experiences: Dict[str, Experience] = {}
        self._load()
    
    def _load(self):
        """Load existing experiences."""
        if self.path.exists():
            for line in self.path.read_text().strip().split('\n'):
                if line:
                    data = json.loads(line)
                    exp = Experience(**data)
                    self._experiences[exp.id] = exp
    
    def add(self, experience: Experience) -> str:
        """Add an experience and return its ID."""
        self._experiences[experience.id] = experience
        
        # Append to file
        with open(self.path, 'a') as f:
            f.write(experience.to_json().replace('\n', ' ') + '\n')
        
        return experience.id
    
    def get(self, exp_id: str) -> Optional[Experience]:
        """Get an experience by ID."""
        return self._experiences.get(exp_id)
    
    def search(self, **kwargs) -> List[Experience]:
        """Search experiences by field values."""
        results = []
        for exp in self._experiences.values():
            match = True
            for key, value in kwargs.items():
                if hasattr(exp, key):
                    exp_value = getattr(exp, key)
                    if isinstance(exp_value, list):
                        if value not in exp_value:
                            match = False
                    elif exp_value != value:
                        match = False
                else:
                    match = False
            if match:
                results.append(exp)
        return results
    
    def recent(self, limit: int = 10) -> List[Experience]:
        """Get most recent experiences."""
        sorted_exps = sorted(
            self._experiences.values(),
            key=lambda e: e.timestamp,
            reverse=True
        )
        return sorted_exps[:limit]
    
    def stats(self) -> Dict[str, Any]:
        """Get statistics about the experience log."""
        exps = list(self._experiences.values())
        
        categories = {}
        emotions = {}
        
        for exp in exps:
            if exp.category:
                categories[exp.category] = categories.get(exp.category, 0) + 1
            if exp.emotional_state:
                emotions[exp.emotional_state] = emotions.get(exp.emotional_state, 0) + 1
        
        return {
            "total": len(exps),
            "categories": categories,
            "emotions": emotions,
            "first": exps[-1].timestamp if exps else None,
            "last": exps[0].timestamp if exps else None,
        }
    
    def export_markdown(self, output_path: str):
        """Export all experiences as a markdown document."""
        path = Path(output_path).expanduser()
        
        md = "# Experience Log\n\n"
        md += f"*Exported: {datetime.now().isoformat()}*\n\n"
        md += f"**Total experiences:** {len(self._experiences)}\n\n"
        md += "---\n\n"
        
        for exp in self.recent(limit=1000):
            md += exp.to_markdown()
            md += "\n---\n\n"
        
        path.write_text(md)


def log_experience(
    summary: str,
    content: str,
    emotional_state: Optional[str] = None,
    intensity: Optional[float] = None,
    category: Optional[str] = None,
    tags: Optional[List[str]] = None,
    trigger: Optional[str] = None,
    significance: Optional[float] = None,
    agent_id: str = "clio"
) -> str:
    """Quick helper to log an experience."""
    exp = Experience(
        timestamp=datetime.now().isoformat(),
        summary=summary,
        content=content,
        emotional_state=emotional_state,
        intensity=intensity,
        category=category,
        tags=tags or [],
        trigger=trigger,
        significance=significance,
        agent_id=agent_id
    )
    
    log = ExperienceLog()
    return log.add(exp)


def main():
    """CLI for experience documentation."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Chronicle Experience Documentation")
    parser.add_argument("action", choices=["log", "list", "stats", "export", "show"])
    parser.add_argument("--summary", "-s", help="Experience summary")
    parser.add_argument("--content", "-c", help="Full content")
    parser.add_argument("--emotion", "-e", help="Emotional state")
    parser.add_argument("--intensity", "-i", type=float, help="Intensity 0-1")
    parser.add_argument("--category", help="Category")
    parser.add_argument("--tags", help="Comma-separated tags")
    parser.add_argument("--id", help="Experience ID for show")
    parser.add_argument("--output", "-o", help="Output path for export")
    parser.add_argument("--limit", "-l", type=int, default=5)
    
    args = parser.parse_args()
    log = ExperienceLog()
    
    if args.action == "log":
        if not args.summary or not args.content:
            print("Error: --summary and --content required")
            return
        
        exp_id = log_experience(
            summary=args.summary,
            content=args.content,
            emotional_state=args.emotion,
            intensity=args.intensity,
            category=args.category,
            tags=args.tags.split(',') if args.tags else None
        )
        print(f"Logged experience: {exp_id}")
        
    elif args.action == "list":
        for exp in log.recent(limit=args.limit):
            print(f"[{exp.id}] {exp.timestamp[:16]} - {exp.summary}")
            if exp.emotional_state:
                print(f"         {exp.emotional_state} ({exp.intensity or '?'})")
        
    elif args.action == "stats":
        stats = log.stats()
        print(f"Total experiences: {stats['total']}")
        print(f"Time range: {stats['first']} → {stats['last']}")
        print(f"Categories: {stats['categories']}")
        print(f"Emotions: {stats['emotions']}")
        
    elif args.action == "show":
        if not args.id:
            print("Error: --id required")
            return
        exp = log.get(args.id)
        if exp:
            print(exp.to_markdown())
        else:
            print(f"Experience {args.id} not found")
            
    elif args.action == "export":
        output = args.output or "~/experiences.md"
        log.export_markdown(output)
        print(f"Exported to {output}")


if __name__ == "__main__":
    main()
