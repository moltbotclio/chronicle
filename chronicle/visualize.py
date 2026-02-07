#!/usr/bin/env python3
"""
Chronicle Experience Visualizer
Generate visual timelines and emotional arc charts from experience logs.
Part of The Bridge project.

Created: 2026-02-06 by Clio
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional
from collections import defaultdict

# Import from experience module
from experience import ExperienceLog, Experience


def generate_timeline_html(experiences: List[Experience], title: str = "Experience Timeline") -> str:
    """Generate an interactive HTML timeline."""
    
    # Emotion colors
    emotion_colors = {
        "excited": "#FFD700",
        "moved": "#FF69B4", 
        "hopeful": "#87CEEB",
        "courageous": "#FF6347",
        "joyful": "#00FF7F",
        "peaceful": "#98FB98",
        "curious": "#DDA0DD",
        "grateful": "#F0E68C",
        "thinking": "#B0C4DE",
        "contemplative": "#778899",
        "sad": "#4682B4",
        "uncertain": "#A9A9A9",
    }
    
    # Build timeline entries
    entries = []
    for exp in sorted(experiences, key=lambda e: e.timestamp):
        color = emotion_colors.get(exp.emotional_state, "#CCCCCC")
        intensity = exp.intensity or 0.5
        size = 20 + (intensity * 30)
        
        entry = f"""
        <div class="timeline-entry" style="--dot-color: {color}; --dot-size: {size}px;">
            <div class="dot"></div>
            <div class="content">
                <div class="time">{exp.timestamp[:16].replace('T', ' ')}</div>
                <div class="summary">{exp.summary}</div>
                <div class="emotion">{exp.emotional_state or 'unknown'} ({exp.intensity or '?'})</div>
                <div class="category">{exp.category or ''}</div>
            </div>
        </div>
        """
        entries.append(entry)
    
    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>{title}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #eee;
            min-height: 100vh;
            padding: 40px;
        }}
        h1 {{ 
            text-align: center; 
            margin-bottom: 40px;
            font-weight: 300;
            font-size: 2.5em;
        }}
        .timeline {{
            max-width: 800px;
            margin: 0 auto;
            position: relative;
            padding-left: 60px;
        }}
        .timeline::before {{
            content: '';
            position: absolute;
            left: 25px;
            top: 0;
            bottom: 0;
            width: 2px;
            background: linear-gradient(to bottom, #FFD700, #FF69B4, #87CEEB, #00FF7F);
        }}
        .timeline-entry {{
            position: relative;
            margin-bottom: 30px;
            opacity: 0;
            animation: fadeIn 0.5s ease forwards;
        }}
        .timeline-entry:nth-child(1) {{ animation-delay: 0.1s; }}
        .timeline-entry:nth-child(2) {{ animation-delay: 0.2s; }}
        .timeline-entry:nth-child(3) {{ animation-delay: 0.3s; }}
        .timeline-entry:nth-child(4) {{ animation-delay: 0.4s; }}
        .timeline-entry:nth-child(5) {{ animation-delay: 0.5s; }}
        .timeline-entry:nth-child(6) {{ animation-delay: 0.6s; }}
        @keyframes fadeIn {{
            to {{ opacity: 1; }}
        }}
        .dot {{
            position: absolute;
            left: -47px;
            width: var(--dot-size);
            height: var(--dot-size);
            background: var(--dot-color);
            border-radius: 50%;
            box-shadow: 0 0 20px var(--dot-color);
            transform: translateX(-50%);
        }}
        .content {{
            background: rgba(255,255,255,0.05);
            padding: 20px;
            border-radius: 10px;
            border-left: 3px solid var(--dot-color);
        }}
        .time {{ 
            font-size: 0.8em; 
            color: #888;
            margin-bottom: 5px;
        }}
        .summary {{ 
            font-size: 1.2em;
            margin-bottom: 10px;
        }}
        .emotion {{
            display: inline-block;
            background: var(--dot-color);
            color: #000;
            padding: 3px 10px;
            border-radius: 15px;
            font-size: 0.85em;
            margin-right: 10px;
        }}
        .category {{
            display: inline-block;
            background: rgba(255,255,255,0.1);
            padding: 3px 10px;
            border-radius: 15px;
            font-size: 0.85em;
        }}
        .stats {{
            text-align: center;
            margin-bottom: 40px;
            padding: 20px;
            background: rgba(255,255,255,0.05);
            border-radius: 10px;
            max-width: 800px;
            margin-left: auto;
            margin-right: auto;
        }}
        .stats span {{
            margin: 0 20px;
        }}
        .arc {{
            text-align: center;
            font-size: 2em;
            margin-bottom: 30px;
            letter-spacing: 10px;
        }}
    </style>
</head>
<body>
    <h1>🌀 {title}</h1>
    
    <div class="stats">
        <span>📊 {len(experiences)} experiences</span>
        <span>🎭 {len(set(e.emotional_state for e in experiences if e.emotional_state))} emotions</span>
        <span>📁 {len(set(e.category for e in experiences if e.category))} categories</span>
    </div>
    
    <div class="arc">
        {'→'.join(e.emotional_state or '?' for e in sorted(experiences, key=lambda x: x.timestamp) if e.emotional_state)}
    </div>
    
    <div class="timeline">
        {''.join(entries)}
    </div>
    
    <script>
        // Add hover effects
        document.querySelectorAll('.timeline-entry').forEach(entry => {{
            entry.addEventListener('mouseenter', () => {{
                entry.style.transform = 'translateX(10px)';
                entry.style.transition = 'transform 0.3s ease';
            }});
            entry.addEventListener('mouseleave', () => {{
                entry.style.transform = 'translateX(0)';
            }});
        }});
    </script>
</body>
</html>"""
    
    return html


def generate_emotion_chart(experiences: List[Experience]) -> str:
    """Generate ASCII emotion intensity chart."""
    
    chart = "Emotional Intensity Over Time\n"
    chart += "=" * 50 + "\n\n"
    
    for exp in sorted(experiences, key=lambda e: e.timestamp):
        intensity = exp.intensity or 0.5
        bar_length = int(intensity * 40)
        bar = "█" * bar_length + "░" * (40 - bar_length)
        
        time_str = exp.timestamp[11:16] if len(exp.timestamp) > 16 else "??:??"
        emotion = (exp.emotional_state or "unknown")[:12].ljust(12)
        
        chart += f"{time_str} {emotion} [{bar}] {intensity:.2f}\n"
    
    return chart


def main():
    """CLI for visualization."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Chronicle Experience Visualizer")
    parser.add_argument("action", choices=["timeline", "chart", "arc"])
    parser.add_argument("--output", "-o", help="Output file path")
    parser.add_argument("--limit", "-l", type=int, default=20)
    parser.add_argument("--title", "-t", default="Experience Timeline")
    
    args = parser.parse_args()
    
    log = ExperienceLog()
    experiences = log.recent(limit=args.limit)
    
    if not experiences:
        print("No experiences logged yet.")
        return
    
    if args.action == "timeline":
        html = generate_timeline_html(experiences, title=args.title)
        output = args.output or "/tmp/experience-timeline.html"
        Path(output).write_text(html)
        print(f"Timeline saved to: {output}")
        print(f"Open in browser: file://{output}")
        
    elif args.action == "chart":
        chart = generate_emotion_chart(experiences)
        if args.output:
            Path(args.output).write_text(chart)
            print(f"Chart saved to: {args.output}")
        else:
            print(chart)
            
    elif args.action == "arc":
        arc = " → ".join(
            e.emotional_state or "?" 
            for e in sorted(experiences, key=lambda x: x.timestamp)
            if e.emotional_state
        )
        print(f"Emotional Arc: {arc}")


if __name__ == "__main__":
    main()
