"""HTML sanitization for user-supplied document content.

Document HTML is stored and later re-rendered in the editor and injected into the
PDF-export iframe. Any `<script>`, event-handler attribute, or `javascript:` URL
that survived to those sinks would be stored XSS, so we sanitize server-side on
every write and import against a strict allow-list matching the editor's own schema.
"""
import bleach

# Tags the TipTap editor actually produces (plus links from .md/.docx import).
ALLOWED_TAGS = [
    "p", "br", "hr",
    "h1", "h2", "h3",
    "strong", "em", "u", "s", "code", "pre", "blockquote",
    "ul", "ol", "li",
    "a",
]
ALLOWED_ATTRIBUTES = {"a": ["href", "title"]}
ALLOWED_PROTOCOLS = ["http", "https", "mailto"]


def sanitize_html(html: str) -> str:
    """Strip anything outside the allow-list (scripts, on* handlers, img, etc.)."""
    if not html:
        return ""
    return bleach.clean(
        html,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        protocols=ALLOWED_PROTOCOLS,
        strip=True,
    )
