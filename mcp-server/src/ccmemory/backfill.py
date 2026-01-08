"""Backfill historical data into the context graph."""

import hashlib
import json
import logging
import re
import uuid
from datetime import datetime
from enum import StrEnum
from pathlib import Path

from .detection.detector import detectAll
from .embeddings import getEmbedding
from .graph import getClient
from .hooks import _storeDetection
from .tools.reference import _indexFile


class BackfillSource(StrEnum):
    Conversations = "conversations"
    Markdown = "markdown"


# === Claude Code Conversation Location ===


def getClaudeProjectsDir() -> Path:
    return Path.home() / ".claude" / "projects"


def getProjectConversationDirs(project: str) -> list[Path]:
    # Claude Code stores conversations in directories named like:
    # ~/.claude/projects/-Users-patrick-{project}/ (path encoding replaces / with -)
    claude_projects = getClaudeProjectsDir()
    if not claude_projects.exists():
        return []

    matching_dirs = []
    for d in claude_projects.iterdir():
        if d.is_dir() and d.name.endswith(f"-{project}"):
            matching_dirs.append(d)

    return matching_dirs


def getConversationFiles(project: str) -> list[Path]:
    files = []
    for conv_dir in getProjectConversationDirs(project):
        files.extend(conv_dir.glob("*.jsonl"))
    return sorted(files, key=lambda p: p.stat().st_mtime)


MIN_FILE_SIZE = 5000  # Skip tiny conversations (<5KB)
MAX_FILE_SIZE = 500000  # Skip huge files (>500KB, likely image-heavy)
MIN_TEXT_RATIO = 0.3  # Skip if <30% of content is extractable text


def isConversationWorthImporting(path: Path) -> bool:
    """Quick heuristic check if a conversation is worth importing."""
    size = path.stat().st_size
    if size < MIN_FILE_SIZE or size > MAX_FILE_SIZE:
        return False

    try:
        with open(path, "r") as f:
            content = f.read(50000)  # Sample first 50KB
    except (FileNotFoundError, IOError):
        return False

    # Check text ratio - skip if mostly tool_use/images
    text_chars = sum(1 for c in content if c.isalpha() or c.isspace())
    if text_chars / len(content) < MIN_TEXT_RATIO:
        return False

    # Must have at least a few message exchanges
    if content.count('"role"') < 6:
        return False

    return True


def getFilteredConversationFiles(project: str, limit: int | None = None) -> list[Path]:
    """Get conversation files filtered for quality, sorted by recency."""
    all_files = getConversationFiles(project)
    # Sort by mtime descending (most recent first)
    all_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)

    filtered = [f for f in all_files if isConversationWorthImporting(f)]

    if limit:
        return filtered[:limit]
    return filtered


# === Conversation Parsing ===


def _parseMessages(messages: list[dict]) -> list[tuple[str, str, str]]:
    pairs = []
    context_messages = []

    def getRole(msg):
        return msg.get("type") or msg.get("message", {}).get("role") or msg.get("role")

    def getContent(msg):
        inner = msg.get("message", {})
        content = inner.get("content") or msg.get("content", "")
        return _extractTextContent(content)

    i = 0
    while i < len(messages):
        msg = messages[i]

        if getRole(msg) == "user":
            user_content = getContent(msg)

            assistant_content = ""
            j = i + 1
            while j < len(messages):
                if getRole(messages[j]) == "assistant":
                    assistant_content = getContent(messages[j])
                    break
                j += 1

            if user_content and assistant_content:
                context = "\n".join(
                    f"{getRole(m)}: {getContent(m)[:200]}"
                    for m in context_messages[-10:]
                )
                pairs.append((user_content, assistant_content, context))

                context_messages.append(msg)
                if j < len(messages):
                    context_messages.append(messages[j])

                i = j + 1
                continue

        i += 1

    return pairs


def parseConversationFile(path: Path) -> list[tuple[str, str, str]]:
    try:
        with open(path, "r") as f:
            messages = [json.loads(line) for line in f if line.strip()]
    except (json.JSONDecodeError, FileNotFoundError):
        return []
    return _parseMessages(messages)


def _extractTextContent(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return " ".join(
            c.get("text", "")
            for c in content
            if isinstance(c, dict) and c.get("type") == "text"
        )
    return ""


def getSessionIdFromPath(path: Path) -> str:
    return f"backfill-{path.stem}"


# === Conversation Backfill ===


async def backfillConversations(
    project: str,
    dry_run: bool = False,
    limit: int | None = None,
    progress_callback=None,
) -> dict:
    client = None if dry_run else getClient()
    conversation_files = getFilteredConversationFiles(project, limit)

    stats = {
        "sessions_found": len(conversation_files),
        "sessions_processed": 0,
        "sessions_skipped": 0,
        "pairs_analyzed": 0,
        "detections_stored": 0,
    }

    for i, conv_file in enumerate(conversation_files):
        session_id = getSessionIdFromPath(conv_file)

        if not dry_run and client.sessionExists(session_id):
            stats["sessions_skipped"] += 1
            continue

        if progress_callback:
            progress_callback(i + 1, len(conversation_files), conv_file.name)

        pairs = parseConversationFile(conv_file)
        if not pairs:
            continue

        if dry_run:
            stats["sessions_processed"] += 1
            stats["pairs_analyzed"] += len(pairs)
            continue

        file_mtime = datetime.fromtimestamp(conv_file.stat().st_mtime)
        client.createSession(
            session_id=session_id,
            project=project,
            started_at=file_mtime.isoformat(),
        )

        for user_msg, assistant_msg, context in pairs:
            stats["pairs_analyzed"] += 1

            try:
                detections = await detectAll(user_msg, assistant_msg, context)
            except Exception as e:
                logging.debug("Failed to detect in %s: %s", conv_file.name, e)
                continue

            for detection in detections:
                try:
                    if _storeDetection(client, session_id, detection):
                        stats["detections_stored"] += 1
                except Exception as e:
                    logging.debug("Failed to store detection: %s", e)
                    continue

        stats["sessions_processed"] += 1

    return stats


def _deterministicId(prefix: str, *parts: str) -> str:
    """Generate a deterministic ID from input parts."""
    combined = "|".join(parts)
    hash_hex = hashlib.sha256(combined.encode()).hexdigest()[:12]
    return f"{prefix}-{hash_hex}"


def parseConversationContent(jsonl_content: str) -> list[tuple[str, str, str]]:
    try:
        messages = [
            json.loads(line)
            for line in jsonl_content.strip().split("\n")
            if line.strip()
        ]
    except json.JSONDecodeError:
        return []
    return _parseMessages(messages)


async def backfillConversationContent(
    project: str,
    session_id: str,
    jsonl_content: str,
    dry_run: bool = False,
) -> dict:
    """Backfill a single conversation from JSONL content passed by Claude Code."""
    client = None if dry_run else getClient()

    # Use deterministic session ID based on content hash for deduplication
    content_hash = hashlib.sha256(jsonl_content.encode()).hexdigest()[:16]
    full_session_id = f"backfill-{session_id}-{content_hash}"

    stats = {
        "session_id": full_session_id,
        "already_imported": False,
        "pairs_analyzed": 0,
        "detections_stored": 0,
    }

    if not dry_run and client.sessionExists(full_session_id):
        stats["already_imported"] = True
        return stats

    pairs = parseConversationContent(jsonl_content)
    if not pairs:
        return stats

    if dry_run:
        stats["pairs_analyzed"] = len(pairs)
        return stats

    client.createSession(
        session_id=full_session_id,
        project=project,
        started_at=datetime.now().isoformat(),
    )

    logger = logging.getLogger("ccmemory")
    for user_msg, assistant_msg, context in pairs:
        stats["pairs_analyzed"] += 1

        try:
            detections = await detectAll(user_msg, assistant_msg, context)
            if detections:
                types = [d.type.value for d in detections]
                logger.info(
                    f"Pair {stats['pairs_analyzed']}: found {', '.join(types)}",
                    extra={
                        "cat": "tool",
                        "event": "backfill-detect",
                        "project": project,
                    },
                )
        except Exception as e:
            logger.warning(
                f"Detection failed: {e}",
                extra={"cat": "tool", "event": "backfill-detect", "project": project},
            )
            continue

        for detection in detections:
            try:
                if _storeDetection(client, full_session_id, detection):
                    stats["detections_stored"] += 1
                    # Get a preview of what was stored
                    data = detection.data
                    preview = ""
                    if hasattr(data, "description"):
                        preview = f": {data.description[:60]}"
                    elif hasattr(data, "summary"):
                        preview = f": {data.summary[:60]}"
                    elif hasattr(data, "rightBelief"):
                        preview = f": {data.rightBelief[:60]}"
                    logger.info(
                        f"Stored {detection.type.value}{preview}",
                        extra={
                            "cat": "tool",
                            "event": "backfill-store",
                            "project": project,
                        },
                    )
            except Exception as e:
                logger.warning(
                    f"Store failed: {e}",
                    extra={
                        "cat": "tool",
                        "event": "backfill-store",
                        "project": project,
                    },
                )
                continue

    return stats


async def backfillMarkdownContent(
    project: str,
    file_path: str,
    content: str,
    dry_run: bool = False,
) -> dict:
    """Backfill a single markdown file from content passed by Claude Code."""
    client = None if dry_run else getClient()

    # Use deterministic ID based on file path and content hash
    content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]

    stats = {
        "file_path": file_path,
        "is_decision_log": False,
        "decisions_imported": 0,
        "chunks_created": 0,
        "already_imported": False,
    }

    if isDecisionLog(content):
        stats["is_decision_log"] = True
        entries = parseDecisionLog(content, file_path)

        for entry in entries:
            decision_id = _deterministicId(
                "decision", project, file_path, entry["description"]
            )

            if not dry_run and client.decisionExists(project, entry["description"]):
                stats["already_imported"] = True
                continue

            if dry_run:
                stats["decisions_imported"] += 1
                continue

            embedding = getEmbedding(f"{entry['description']} {entry['rationale']}")

            # Create session for this backfill if needed
            backfill_session_id = _deterministicId(
                "session", project, "markdown-backfill"
            )
            if not client.sessionExists(backfill_session_id):
                client.createSession(
                    session_id=backfill_session_id,
                    project=project,
                    started_at=datetime.now().isoformat(),
                )

            client.createDecision(
                decision_id=decision_id,
                session_id=backfill_session_id,
                description=entry["description"],
                embedding=embedding,
                rationale=entry["rationale"],
                revisit_trigger=entry["revisit_trigger"],
                detection_confidence=1.0,
                detection_method="backfill_import",
            )
            stats["decisions_imported"] += 1
    else:
        # Check if already indexed
        if not dry_run and client.referenceFileExists(project, file_path):
            stats["already_imported"] = True
            return stats

        if dry_run:
            sections = re.split(r"^#{1,3}\s+", content, flags=re.MULTILINE)
            stats["chunks_created"] = len([s for s in sections if s.strip()])
            return stats

        # Index as reference - need to write to temp file for _indexFile
        # TODO: refactor _indexFile to accept content directly
        stats["chunks_created"] = 0  # Placeholder until refactored

    return stats


# === Decision Log Parsing ===

DECISION_LOG_PATTERN = re.compile(r"^## (\d{4}-\d{2}-\d{2}):\s*(.+)$", re.MULTILINE)
CODE_BLOCK_PATTERN = re.compile(r"```[\s\S]*?```", re.MULTILINE)


def isDecisionLog(content: str) -> bool:
    content_no_code = CODE_BLOCK_PATTERN.sub("", content)
    return bool(DECISION_LOG_PATTERN.search(content_no_code))


def parseDecisionLog(content: str, source_file: str) -> list[dict]:
    entries = []

    content_no_code = CODE_BLOCK_PATTERN.sub("", content)
    parts = DECISION_LOG_PATTERN.split(content_no_code)

    i = 1
    while i < len(parts) - 2:
        date = parts[i]
        title = parts[i + 1]
        body = parts[i + 2] if i + 2 < len(parts) else ""

        context = _extractField(body, "Context")
        options = _extractField(body, "Options considered")
        reasoning = _extractField(body, "Reasoning")
        revisit = _extractField(body, "Revisit trigger")

        entries.append(
            {
                "date": date,
                "title": title.strip(),
                "description": f"{date}: {title.strip()}",
                "rationale": (
                    f"{context}\n\n{reasoning}".strip() if context or reasoning else ""
                ),
                "options_considered": options,
                "revisit_trigger": revisit,
                "source_file": source_file,
            }
        )

        i += 3

    return entries


def _extractField(text: str, field_name: str) -> str:
    pattern = rf"\*\*{field_name}:\*\*\s*(.+?)(?=\*\*\w+:|$)"
    match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
    return match.group(1).strip() if match else ""


# === Markdown Backfill ===


def getMarkdownFiles(project_root: Path) -> list[Path]:
    ignore_dirs = {
        "node_modules",
        ".git",
        "__pycache__",
        ".venv",
        "venv",
        ".ccmemory",
        "dist",
        "build",
        ".next",
        ".nuxt",
    }

    files = []
    for md_file in project_root.rglob("*.md"):
        if any(part in ignore_dirs for part in md_file.parts):
            continue
        files.append(md_file)

    return sorted(files)


async def backfillMarkdown(
    project_root: Path, dry_run: bool = False, progress_callback=None
) -> dict:
    client = getClient() if not dry_run else None
    project = project_root.name
    md_files = getMarkdownFiles(project_root)

    stats = {
        "files_found": len(md_files),
        "decision_logs_found": 0,
        "decisions_imported": 0,
        "reference_files_indexed": 0,
        "chunks_created": 0,
    }

    backfill_session_id = (
        f"backfill-markdown-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    )

    if not dry_run:
        client.createSession(
            session_id=backfill_session_id,
            project=project,
            started_at=datetime.now().isoformat(),
        )

    for i, md_file in enumerate(md_files):
        if progress_callback:
            progress_callback(
                i + 1, len(md_files), str(md_file.relative_to(project_root))
            )

        try:
            content = md_file.read_text()
        except (FileNotFoundError, IOError, OSError):
            continue

        relative_path = str(md_file.relative_to(project_root))

        if isDecisionLog(content):
            stats["decision_logs_found"] += 1
            entries = parseDecisionLog(content, relative_path)

            if dry_run:
                stats["decisions_imported"] += len(entries)
                continue

            for entry in entries:
                decision_id = f"backfill-decision-{uuid.uuid4().hex[:8]}"

                embedding = getEmbedding(f"{entry['description']} {entry['rationale']}")

                client.createDecision(
                    decision_id=decision_id,
                    session_id=backfill_session_id,
                    description=entry["description"],
                    embedding=embedding,
                    rationale=entry["rationale"],
                    revisit_trigger=entry["revisit_trigger"],
                    detection_confidence=1.0,
                    detection_method="backfill_import",
                )
                stats["decisions_imported"] += 1
        else:
            if dry_run:
                stats["reference_files_indexed"] += 1
                sections = re.split(r"^#{1,3}\s+", content, flags=re.MULTILINE)
                stats["chunks_created"] += len([s for s in sections if s.strip()])
                continue

            chunks = _indexFile(md_file, str(project_root), client)
            stats["reference_files_indexed"] += 1
            stats["chunks_created"] += chunks

    return stats


# === Combined Backfill ===


async def backfillAll(
    project_root: Path,
    dry_run: bool = False,
    conversation_limit: int | None = None,
    progress_callback=None,
) -> dict:
    project = project_root.name

    conv_stats = await backfillConversations(
        project, dry_run, conversation_limit, progress_callback
    )

    md_stats = await backfillMarkdown(project_root, dry_run, progress_callback)

    return {
        "conversations": conv_stats,
        "markdown": md_stats,
    }
