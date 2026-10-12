"""Text utilities: HTML → article text and date, scrape validation, summaries, entity tags."""

from __future__ import annotations

import re

from bs4 import BeautifulSoup

NOISE_TAGS = ["script", "style", "noscript", "header", "footer", "nav", "aside", "form", "img", "svg", "iframe", "button"]

# Pages served instead of the article (bot walls, consent walls, HTTP errors).
BLOCKED_PATTERNS = [
    r"enable javascript and cookies to continue",
    r"unusual activity from your computer network",
    r"checking your connection to prevent automated abuse",
    r"security controls triggered",
    r"checking your browser",
    r"access denied",
    r"403 forbidden",
    r"attention required! \| cloudflare",
    r"502 bad gateway",
    r"503 service (temporarily )?unavailable",
    r"404 not found",
    r"451: unavailable due to legal reasons",
    r"errors\.edgesuite\.net",
    r"^just a (quick check|moment)",
    r"verify you are (a )?human",
    r"please turn javascript on and reload the page",
    r"robot check",
    r"please enable cookies",
    r"shieldsquare captcha",
    r"cf-browser-verification",
    r"pardon our interruption",
    r"access to this page (has been )?denied",
    r"sign in to view more content",
    r"join linkedin",
    r"using a security service to protect itself",
    r"the action you just performed triggered the security solution",
]
_BLOCKED_RE = re.compile("|".join(f"(?:{p})" for p in BLOCKED_PATTERNS), re.IGNORECASE)

BOILERPLATE_PATTERNS = [
    r"we value your privacy[^.]*\.?",
    r"we and our partners (store|use)[^.]*\.?",
    r"cookies? (and|to) process personal data[^.]*\.?",
    r"subscribe to (read|continue)[^.]*\.?",
    r"all rights reserved[^.]*\.?",
    r"(terms of (service|use)|privacy policy)[^.]*\.?",
    r"(sign|log) in to[^.]*\.?",
]
_BOILERPLATE_RE = re.compile("|".join(BOILERPLATE_PATTERNS), re.IGNORECASE)
_SKIP_SENTENCE_WORDS = (
    "cookie", "javascript", "subscribe", "sign in", "log in", "advertisement", "copyright", "newsletter",
    "republish", "licensed under", "creative commons", "click here", "read more", "all rights reserved",
)


def strip_html(value: str) -> str:
    if not value or "<" not in value:
        return re.sub(r"\s+", " ", str(value or "")).strip()
    return re.sub(r"\s+", " ", BeautifulSoup(value, "html.parser").get_text(" ")).strip()


def html_to_text(html: str, min_paragraph_chars: int = 40) -> str:
    """Extract the readable body of an article page.

    Prefers <article>/<main>, keeps paragraphs and headings long enough to be
    prose, and drops repeated blocks.
    """
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(NOISE_TAGS):
        tag.decompose()
    container = soup.find("article") or soup.find("main") or soup
    for scope in (container, soup) if container is not soup else (soup,):
        seen, parts = set(), []
        for el in scope.find_all(["h1", "h2", "h3", "p", "li"]):
            text = re.sub(r"\s+", " ", el.get_text(" ")).strip()
            is_heading = el.name in ("h1", "h2", "h3")
            if (is_heading and len(text) >= 15) or len(text) >= min_paragraph_chars:
                if text not in seen:
                    seen.add(text)
                    parts.append(text)
        if parts:
            break
    return "\n".join(parts)


def extract_article(html: str, url: str | None = None) -> tuple[str, str]:
    """Return (text, publication date as YYYY-MM-DD or "").

    trafilatura finds the main content and the page's date metadata; the
    simpler html_to_text heuristic is the fallback when it returns nothing.
    """
    text, date = "", ""
    try:
        import trafilatura

        doc = trafilatura.bare_extraction(
            html, url=url, with_metadata=True, include_comments=False, include_tables=False, deduplicate=True
        )
    except Exception:  # malformed pages must not stop the run
        doc = None
    if doc is not None:
        text = (doc.text or "").strip()
        date = (doc.date or "")[:10]
    if len(text) < 200:
        fallback = html_to_text(html)
        text = fallback if len(fallback) > len(text) else text
    return text, date


def classify_text(text: str, min_chars: int) -> str:
    """Return 'ok', 'blocked' or 'too_short'."""
    t = (text or "").strip()
    if _BLOCKED_RE.search(t[:2000]):
        return "blocked"
    if len(t) < min_chars:
        return "too_short"
    return "ok"


def summarize(text: str, fallback: str = "", max_sentences: int = 3, max_chars: int = 360) -> str:
    """Extractive summary: first clean sentences of the body, else the description."""
    source = text if text and len(text) > 80 else fallback
    # Headings and captions (lines without final punctuation) are not prose.
    lines = [l.strip() for l in (source or "").splitlines() if l.strip()]
    prose = [l for l in lines if l.endswith((".", "!", "?", '"', "”")) or len(l) > 200]
    source = " ".join(prose or lines)
    source = _BOILERPLATE_RE.sub(" ", source)
    source = re.sub(r"\s+", " ", source).strip()
    sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9\"“])", source)  # "U.S. and" is not a break
    clean = [s for s in sentences if len(s) > 30 and not any(w in s.lower() for w in _SKIP_SENTENCE_WORDS)]
    summary = " ".join(clean[:max_sentences]) or source
    if len(summary) <= max_chars:
        return summary
    return summary[: max_chars - 1].rsplit(" ", 1)[0].rstrip(" .,;:") + "…"


def compile_entities(entities: dict[str, list[str]]) -> dict[str, re.Pattern]:
    return {label: re.compile("|".join(f"(?:{p})" for p in patterns), re.IGNORECASE) for label, patterns in entities.items() if patterns}


def tag_entities(text: str, compiled: dict[str, re.Pattern]) -> str:
    return ", ".join(label for label, rx in compiled.items() if rx.search(text or ""))
