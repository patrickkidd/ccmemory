#!/usr/bin/env python3
"""
ccmemory SessionEnd hook for automatic conversation logging.

Runs when a Claude Code session ends and:
1. Copies the raw JSONL transcript to .ccmemory/conversations/raw/
2. Converts it to readable markdown
3. Updates the conversation index

Directory structure:
  .ccmemory/
    conversations/
      raw/           - Raw JSONL transcripts (for programmatic access)
      summaries/     - Markdown versions (for human reading)
      index.jsonl    - Session metadata index
"""

import json
import os
import re
import sys
import shutil
from pathlib import Path
from datetime import datetime


def log_debug(msg: str):
    if os.environ.get('CCMEMORY_DEBUG') == '1':
        log_file = Path.home() / '.ccmemory-debug.log'
        with open(log_file, 'a') as f:
            f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")


def strip_system_tags(text: str) -> str:
    text = re.sub(r'<system-reminder>.*?</system-reminder>', '', text, flags=re.DOTALL)
    text = re.sub(r'<ide_selection>.*?</ide_selection>', '', text, flags=re.DOTALL)
    text = re.sub(r'<ide_opened_file>.*?</ide_opened_file>', '', text, flags=re.DOTALL)
    text = re.sub(r'<ccmemory-trigger>.*?</ccmemory-trigger>', '', text, flags=re.DOTALL)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def extract_text_from_content(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        text_parts = []
        for block in content:
            if isinstance(block, dict) and block.get('type') == 'text':
                text_parts.append(block.get('text', ''))
            elif isinstance(block, str):
                text_parts.append(block)
        return '\n'.join(text_parts)
    return ''


def parse_jsonl_to_markdown(jsonl_path: Path) -> tuple[str, list[str]]:
    """Convert JSONL transcript to readable markdown. Returns (markdown, user_prompts)."""
    lines = []
    user_prompts = []

    lines.append(f"# Claude Code Session\n")
    lines.append(f"**Transcript:** `{jsonl_path.name}`\n")
    lines.append(f"**Exported:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    lines.append("\n---\n")

    with open(jsonl_path, 'r') as f:
        for line in f:
            if not line.strip():
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue

            event_type = event.get('type', '')

            if event_type == 'user':
                message = event.get('message', {})
                if isinstance(message, dict):
                    content = message.get('content', '')
                else:
                    content = str(message)

                text = extract_text_from_content(content)
                text = strip_system_tags(text)

                if text:
                    lines.append(f"\n## User\n\n{text}\n")
                    first_line = text.split('\n')[0][:100].strip()
                    if first_line:
                        user_prompts.append(first_line)

            elif event_type == 'assistant':
                message = event.get('message', {})
                content_blocks = message.get('content', [])

                text_parts = []
                tool_uses = []

                for block in content_blocks:
                    if isinstance(block, dict):
                        if block.get('type') == 'text':
                            text_parts.append(block.get('text', ''))
                        elif block.get('type') == 'tool_use':
                            tool_name = block.get('name', 'unknown')
                            tool_uses.append(tool_name)

                if text_parts or tool_uses:
                    lines.append(f"\n## Assistant\n")
                    if text_parts:
                        lines.append('\n'.join(text_parts))
                    if tool_uses:
                        lines.append(f"\n*Tools used: {', '.join(tool_uses)}*\n")

    return '\n'.join(lines), user_prompts


def extract_topic_keywords(text: str) -> list[str]:
    text = text.lower().strip()

    skip_patterns = [
        r'^continue\.?$',
        r'^go ahead\.?$',
        r'^yes\.?$',
        r'^no\.?$',
        r'^ok\.?$',
        r'^thanks\.?$',
        r'^\[request interrupted',
        r'^sounds good',
        r'^that.s (good|fine|great)',
    ]
    for pattern in skip_patterns:
        if re.match(pattern, text, re.IGNORECASE):
            return []

    stopwords = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'into', 'through', 'during', 'before',
        'after', 'above', 'below', 'between', 'under', 'about',
        'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has',
        'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should',
        'may', 'might', 'must', 'can', 'don', 'doesn', 'didn', 'won', 'isn',
        'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it',
        'we', 'they', 'my', 'your', 'his', 'her', 'its', 'our', 'their',
        'me', 'him', 'us', 'them', 'who', 'whom', 'which', 'what', 'whose',
        'where', 'when', 'why', 'how', 'all', 'each', 'every', 'both',
        'few', 'more', 'most', 'some', 'any', 'no', 'not', 'only', 'same',
        'so', 'than', 'too', 'very', 'just', 'also', 'now', 'here', 'there',
        'please', 'help', 'need', 'want', 'like', 'think', 'know', 'see',
        'look', 'make', 'get', 'go', 'come', 'take', 'use', 'find', 'give',
        'sure', 'good', 'well', 'right', 'something', 'anything', 'either',
        'new', 'old', 'first', 'last', 'long', 'great', 'little', 'own',
        'way', 'thing', 'things', 'stuff', 'file', 'files', 'code',
    }

    words = re.findall(r'\b[a-z][a-z0-9_-]+\b', text)
    keywords = []
    for word in words:
        if word not in stopwords and len(word) > 2:
            keywords.append(word)

    return keywords[:10]


def generate_title(user_prompts: list[str], max_length: int = 60) -> str:
    """Generate a concise title summarizing topics from user prompts."""
    if not user_prompts:
        return "Untitled Session"

    keyword_counts = {}
    for prompt in user_prompts:
        keywords = extract_topic_keywords(prompt)
        for kw in keywords:
            keyword_counts[kw] = keyword_counts.get(kw, 0) + 1

    if not keyword_counts:
        return user_prompts[0][:max_length]

    sorted_keywords = sorted(keyword_counts.keys(),
                            key=lambda k: (-keyword_counts[k], k))

    title_parts = []
    current_len = 0
    for kw in sorted_keywords:
        sep_len = 2 if title_parts else 0
        if current_len + sep_len + len(kw) <= max_length:
            title_parts.append(kw)
            current_len += sep_len + len(kw)
        if len(title_parts) >= 5:
            break

    return ', '.join(title_parts) if title_parts else "Untitled Session"


def sanitize_filename(title: str) -> str:
    safe = re.sub(r',\s*', '_', title)
    safe = re.sub(r'\s+', '_', safe)
    safe = re.sub(r'[<>:"/\\|?*]', '', safe)
    safe = re.sub(r'_+', '_', safe)
    safe = safe.strip('_')
    return safe[:50]


def main():
    log_debug("Stop hook (log-session.py) fired")
    try:
        hook_input = json.load(sys.stdin)
        log_debug(f"Hook input keys: {list(hook_input.keys())}")
    except json.JSONDecodeError:
        log_debug("Failed to parse hook input JSON")
        print("Failed to parse hook input", file=sys.stderr)
        sys.exit(1)

    session_id = hook_input.get('session_id', 'unknown')
    transcript_path = hook_input.get('transcript_path', '')
    reason = hook_input.get('reason', 'unknown')
    cwd = hook_input.get('cwd', '')
    log_debug(f"Session: {session_id}, reason: {reason}, cwd: {cwd}")

    if not transcript_path:
        print("No transcript path provided", file=sys.stderr)
        sys.exit(1)

    transcript_path = Path(transcript_path)
    if not transcript_path.exists():
        print(f"Transcript not found: {transcript_path}", file=sys.stderr)
        sys.exit(1)

    if transcript_path.stat().st_size < 500:
        sys.exit(0)

    # Set up paths - use .ccmemory in project directory
    project_dir = Path(cwd) if cwd else Path.cwd()
    ccmemory_dir = project_dir / '.ccmemory'
    conversations_dir = ccmemory_dir / 'conversations'
    raw_dir = conversations_dir / 'raw'
    summaries_dir = conversations_dir / 'summaries'

    # Ensure directories exist
    raw_dir.mkdir(parents=True, exist_ok=True)
    summaries_dir.mkdir(parents=True, exist_ok=True)

    # Parse transcript
    markdown_content, user_prompts = parse_jsonl_to_markdown(transcript_path)

    # Generate title
    title = generate_title(user_prompts)
    title_slug = sanitize_filename(title)

    # Generate timestamped filename
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    base_name = f"{timestamp}_{title_slug}"

    # Copy raw JSONL
    raw_file = raw_dir / f"{base_name}.jsonl"
    shutil.copy2(transcript_path, raw_file)

    # Write markdown
    markdown_with_title = markdown_content.replace(
        "# Claude Code Session\n",
        f"# {title}\n"
    )
    summary_file = summaries_dir / f"{base_name}.md"
    with open(summary_file, 'w') as f:
        f.write(markdown_with_title)

    # Update index
    index_entry = {
        'session_id': session_id,
        'timestamp': timestamp,
        'title': title,
        'topics': user_prompts[:5],
        'end_reason': reason,
        'raw_file': str(raw_file.relative_to(project_dir)),
        'summary_file': str(summary_file.relative_to(project_dir)),
        'original_transcript': str(transcript_path),
        'logged_at': datetime.now().isoformat()
    }

    index_file = conversations_dir / 'index.jsonl'
    with open(index_file, 'a') as f:
        f.write(json.dumps(index_entry) + '\n')

    print(f"Session logged: {title[:40]}...")
    sys.exit(0)


if __name__ == '__main__':
    main()
