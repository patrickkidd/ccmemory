"""MCP tools for reference knowledge: cache URLs/PDFs, index for retrieval."""

import os
import re
import hashlib
import subprocess
from pathlib import Path
from typing import Optional

import httpx
from bs4 import BeautifulSoup
from mcp.server.fastmcp import FastMCP

from ..graph import getClient
from ..embeddings import getEmbedding

REFERENCE_DIR = ".ccmemory/reference"


def _getReferencePath(project_root: str) -> Path:
    """Get the reference directory for a project."""
    return Path(project_root) / REFERENCE_DIR


def _cacheUrlImpl(url: str, project_root: str) -> dict:
    """Fetch URL and save as markdown."""
    ref_path = _getReferencePath(project_root) / "cached" / "web"
    ref_path.mkdir(parents=True, exist_ok=True)

    response = httpx.get(url, follow_redirects=True, timeout=30)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    for script in soup(["script", "style", "nav", "footer"]):
        script.decompose()

    title = soup.title.string if soup.title else url

    main = soup.find("main") or soup.find("article") or soup.body
    text = main.get_text(separator="\n", strip=True) if main else ""

    text = re.sub(r"\n{3,}", "\n\n", text)

    url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
    safe_name = re.sub(r"[^\w\-]", "-", str(title)[:50]).strip("-")
    filename = f"{safe_name}-{url_hash}.md"
    filepath = ref_path / filename

    timestamp = subprocess.run(
        ["date", "-Iseconds"], capture_output=True, text=True
    ).stdout.strip()

    content = f"""# {title}

Source: {url}
Cached: {timestamp}

---

{text}
"""
    filepath.write_text(content)

    return {"file": str(filepath), "title": str(title), "chars": len(text)}


def _cachePdfImpl(pdf_path: str, project_root: str) -> dict:
    """Extract PDF content to markdown."""
    import fitz

    ref_path = _getReferencePath(project_root) / "cached" / "pdf"
    ref_path.mkdir(parents=True, exist_ok=True)

    pdf = fitz.open(pdf_path)
    text_parts = []

    for page_num, page in enumerate(pdf):
        text = page.get_text()
        if text.strip():
            text_parts.append(f"## Page {page_num + 1}\n\n{text}")

    pdf.close()

    source_name = Path(pdf_path).stem
    filename = f"{source_name}.md"
    filepath = ref_path / filename

    timestamp = subprocess.run(
        ["date", "-Iseconds"], capture_output=True, text=True
    ).stdout.strip()

    content = f"""# {source_name}

Source: {pdf_path}
Cached: {timestamp}

---

{"".join(text_parts)}
"""
    filepath.write_text(content)

    return {"file": str(filepath), "pages": len(text_parts)}


def _indexAll(project_root: str) -> int:
    """Index all markdown files in reference tree."""
    ref_path = _getReferencePath(project_root)
    if not ref_path.exists():
        return 0

    client = getClient()
    project = os.path.basename(project_root)

    client.clearChunks(project)

    count = 0
    for md_file in ref_path.rglob("*.md"):
        count += _indexFile(md_file, project_root, client)

    return count


def _indexFile(filepath: Path, project_root: str, client=None) -> int:
    """Index a single markdown file into chunks."""
    if client is None:
        client = getClient()

    project = os.path.basename(project_root)
    relative_path = str(filepath.relative_to(project_root))

    content = filepath.read_text()

    sections = re.split(r"^(#{1,3}\s+.+)$", content, flags=re.MULTILINE)

    chunks = []
    current_section = "Overview"

    for part in sections:
        if re.match(r"^#{1,3}\s+", part):
            current_section = part.strip("#").strip()
        elif part.strip():
            chunks.append({"section": current_section, "content": part.strip()[:2000]})

    for i, chunk in enumerate(chunks):
        chunk_id = f"{relative_path}#{i}"
        text_for_embedding = f"{chunk['section']}: {chunk['content'][:500]}"
        embedding = getEmbedding(text_for_embedding)

        client.indexChunk(
            chunk_id=chunk_id,
            project=project,
            source_file=relative_path,
            section=chunk["section"],
            content=chunk["content"],
            embedding=embedding,
        )

    return len(chunks)


from .logging import logTool


def registerReferenceTools(mcp: FastMCP):
    """Register all reference tools with the MCP server."""

    @mcp.tool()
    @logTool
    async def cacheUrl(url: str) -> dict:
        """Cache a URL to the reference knowledge tree.

        Args:
            url: The URL to fetch and cache
        """
        project_root = os.getcwd()
        return _cacheUrlImpl(url, project_root)

    @mcp.tool()
    @logTool
    async def cachePdf(path: str) -> dict:
        """Cache a PDF to the reference knowledge tree.

        Args:
            path: Path to the PDF file
        """
        project_root = os.getcwd()
        return _cachePdfImpl(path, project_root)

    @mcp.tool()
    @logTool
    async def indexReference() -> dict:
        """Rebuild the reference knowledge index from all markdown files."""
        project_root = os.getcwd()
        count = _indexAll(project_root)
        return {"indexed_chunks": count}

    @mcp.tool()
    @logTool
    async def queryReference(query: str, limit: int = 5) -> dict:
        """Search the reference knowledge tree.

        Args:
            query: Search query
            limit: Maximum results
        """
        project_root = os.getcwd()
        project = os.path.basename(project_root)

        embedding = getEmbedding(query)
        client = getClient()
        results = client.searchReference(embedding, project, limit=limit)

        return {
            "results": [
                {
                    "file": r[0].get("source_file"),
                    "section": r[0].get("section"),
                    "content": r[0].get("content", "")[:300],
                    "score": r[1],
                }
                for r in results
            ]
        }

    @mcp.tool()
    @logTool
    async def listReferences() -> dict:
        """List all cached reference files."""
        project_root = os.getcwd()
        ref_path = _getReferencePath(project_root)

        if not ref_path.exists():
            return {"files": []}

        files = []
        for md_file in ref_path.rglob("*.md"):
            relative_path = str(md_file.relative_to(project_root))
            files.append(
                {
                    "path": relative_path,
                    "size": md_file.stat().st_size,
                }
            )

        return {"files": files}
