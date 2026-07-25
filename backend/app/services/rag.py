"""Folder RAG chat: build context from a folder's documents and query an LLM.

Documents in a folder are small and few, so retrieval here is context-stuffing:
we strip each document to plain text and pack them (up to a char budget) into the
system prompt as the knowledge base. Swapping in embeddings + vector search later
would only change build_context().
"""
import html
import re

import httpx

from ..core import config

# Kept small so requests fit modest OpenRouter credit budgets.
MAX_CONTEXT_CHARS = 8000
MAX_OUTPUT_TOKENS = 600


class LLMError(Exception):
    """Raised with a user-safe message when the LLM provider call fails."""


def html_to_text(raw: str) -> str:
    """Reduce stored document HTML to readable plain text for the prompt."""
    if not raw:
        return ""
    text = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", raw)
    text = re.sub(r"(?i)</(p|div|li|h[1-6]|br)>", "\n", text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    text = re.sub(r"[ \t]+", " ", text)
    return re.sub(r"\n\s*\n+", "\n\n", text).strip()


def build_context(docs) -> tuple[str, list[str]]:
    """Pack document texts into a bounded context; return (context, sources)."""
    blocks: list[str] = []
    sources: list[str] = []
    total = 0
    for d in docs:
        text = html_to_text(d.content)
        if not text:
            continue
        block = f"[Document: {d.title}]\n{text}\n"
        if total + len(block) > MAX_CONTEXT_CHARS:
            block = block[: max(0, MAX_CONTEXT_CHARS - total)]
        if not block:
            break
        blocks.append(block)
        sources.append(d.title)
        total += len(block)
        if total >= MAX_CONTEXT_CHARS:
            break
    return "\n".join(blocks), sources


def chat(folder_name: str, docs, message: str, history) -> tuple[str, list[str]]:
    """Call OpenRouter with the folder documents as grounding. Raises on API error."""
    context, sources = build_context(docs)
    system = (
        f"You are a helpful assistant answering questions about the '{folder_name}' folder. "
        "Use ONLY the documents below as your knowledge base. When you use information, "
        "mention the document title it came from. If the answer is not in the documents, "
        "say you couldn't find it in this folder.\n\n"
        f"=== DOCUMENTS ===\n{context}\n=== END DOCUMENTS ==="
    )

    messages = [{"role": "system", "content": system}]
    for h in history[-6:]:
        role = h.role if hasattr(h, "role") else h["role"]
        content = h.content if hasattr(h, "content") else h["content"]
        messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": message})

    try:
        resp = httpx.post(
            f"{config.OPENROUTER_BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {config.OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                # OpenRouter attribution headers (optional but recommended).
                "HTTP-Referer": "https://ajaia-docs.onrender.com",
                "X-Title": "Ajaia Docs",
            },
            json={
                "model": config.OPENROUTER_MODEL,
                "messages": messages,
                "temperature": 0.2,
                "max_tokens": MAX_OUTPUT_TOKENS,
            },
            timeout=60,
        )
    except httpx.HTTPError as e:
        raise LLMError(f"Could not reach the AI service: {e}")

    if resp.status_code >= 400:
        # Surface the provider's message (e.g. credit limits) to aid debugging.
        try:
            detail = resp.json()["error"]["message"]
        except Exception:
            detail = resp.text[:200]
        raise LLMError(detail)

    answer = resp.json()["choices"][0]["message"]["content"]
    return answer, sources
