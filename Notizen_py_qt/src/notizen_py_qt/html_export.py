from __future__ import annotations

from dataclasses import dataclass
from html import escape
import re

from .models import NoteNode
from .rtf_utils import rtf_to_html, rtf_to_plain_text

_BODY_RE = re.compile(r"<body\b[^>]*>(.*)</body>", re.IGNORECASE | re.DOTALL)


@dataclass(slots=True)
class HtmlExportOptions:
    numbered_headings: bool = True
    include_root_number: bool = False
    title: str = "Notizen"
    include_plain_text_fallback: bool = False


def html_body_fragment(html: str) -> str:
    """Extract a safe body fragment from Qt-friendly HTML returned by rtf_utils."""
    if not html:
        return ""
    match = _BODY_RE.search(html)
    return match.group(1) if match else html


def _walk_numbered(node: NoteNode, depth: int, counters: list[int], options: HtmlExportOptions):
    if depth >= len(counters):
        counters.extend(0 for _ in range(depth - len(counters) + 1))
    else:
        del counters[depth + 1 :]
    counters[depth] += 1
    if options.numbered_headings and (depth > 0 or options.include_root_number):
        start = 0 if options.include_root_number else 1
        number = "".join(f"{counters[i]}." for i in range(start, depth + 1))
        heading = f"{number} {node.title}"
    else:
        heading = node.title
    yield depth, heading, node
    for child in node.children:
        yield from _walk_numbered(child, depth + 1, counters, options)


def node_to_html_fragment(node: NoteNode, *, heading_level: int = 1, heading: str | None = None) -> str:
    """Render one Notizen node to a small HTML fragment."""
    level = max(1, min(6, heading_level))
    title = escape(heading if heading is not None else node.title)
    body = html_body_fragment(rtf_to_html(node.rtf))
    if not body:
        body = ""
    return f'<section class="notizen-node"><h{level}>{title}</h{level}>\n<div class="notizen-body">{body}</div></section>'


def tree_to_html(root: NoteNode, options: HtmlExportOptions | None = None) -> str:
    """Export a Notizen subtree to standalone UTF-8 HTML.

    Numbering mirrors the legacy RTF/TXT subtree export: children are headed as
    ``1.``, ``1.1.`` and so on while the root title stays unnumbered by default.
    """
    options = options or HtmlExportOptions(title=root.title or "Notizen")
    parts: list[str] = [
        "<!doctype html>",
        '<html lang="de">',
        "<head>",
        '<meta charset="utf-8"/>',
        f"<title>{escape(options.title or root.title or 'Notizen')}</title>",
        "<style>",
        "body{font-family:Arial,Helvetica,sans-serif;white-space:normal;margin:2rem;}",
        ".notizen-node{margin:0 0 1.2rem 0;}",
        ".notizen-body{white-space:pre-wrap;}",
        ".notizen-body img{max-width:100%;height:auto;}",
        "h1,h2,h3,h4,h5,h6{margin:1rem 0 .35rem 0;}",
        "</style>",
        "</head>",
        "<body>",
    ]
    for depth, heading, node in _walk_numbered(root, 0, [], options):
        parts.append(node_to_html_fragment(node, heading_level=depth + 1, heading=heading))
        if options.include_plain_text_fallback:
            plain = rtf_to_plain_text(node.rtf).strip()
            if plain:
                parts.append(f'<noscript><pre>{escape(plain)}</pre></noscript>')
    parts.extend(["</body>", "</html>", ""])
    return "\n".join(parts)


def tree_to_html_bytes(root: NoteNode, options: HtmlExportOptions | None = None) -> bytes:
    return tree_to_html(root, options).encode("utf-8")
