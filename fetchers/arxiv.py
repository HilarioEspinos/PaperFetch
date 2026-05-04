from __future__ import annotations
import html
import re
import sys
from datetime import date, datetime
from time import struct_time

import feedparser
import requests

from filter import Paper

_ARXIV_ID_RE = re.compile(r"arXiv\.org\:(\d{4}\.\d{4,5})")
_HTML_TAG_RE = re.compile(r"<[^>]+>")


def _strip_html(text: str) -> str:
    return _HTML_TAG_RE.sub("", html.unescape(text)).strip()


def _extract_id(entry: feedparser.FeedParserDict) -> str | None:
    raw = getattr(entry, "id", "") or entry.get("id", "")
    m = _ARXIV_ID_RE.search(raw)
    if not m:
        return None
    full = m.group(1)
    # strip version suffix e.g. "2504.12345v2" → "2504.12345"
    return re.sub(r"v\d+$", "", full)


def _extract_authors(entry: feedparser.FeedParserDict) -> list[str]:
    authors = getattr(entry, "authors", None)
    if authors:
        return [a.get("name", "") for a in authors if a.get("name")]
    raw = entry.get("author", "")
    if raw:
        # arXiv often formats as "Smith, J., Doe, A."
        parts = [p.strip() for p in raw.split(",")]
        # re-join pairs (lastname, initials) that got split
        result = []
        i = 0
        while i < len(parts):
            if i + 1 < len(parts) and len(parts[i + 1].strip()) <= 3:
                result.append(f"{parts[i]}, {parts[i+1]}")
                i += 2
            else:
                result.append(parts[i])
                i += 1
        return [r for r in result if r]
    return []


def _extract_date(entry: feedparser.FeedParserDict) -> str:
    for attr in ("published_parsed", "updated_parsed"):
        t = getattr(entry, attr, None)
        if t and isinstance(t, struct_time):
            try:
                return datetime(*t[:3]).date().isoformat()
            except (ValueError, TypeError):
                pass
    return date.today().isoformat()


def fetch_arxiv(url: str, label: str) -> list[Paper]:
    try:
        resp = requests.get(
            url, timeout=20, headers={"User-Agent": "PaperFetch/1.0"}
        )
        resp.raise_for_status()
        feed = feedparser.parse(resp.content)
    except Exception as exc:
        print(f"[WARNING] {label}: {exc}", file=sys.stderr)
        return []

    papers: list[Paper] = []
    for entry in feed.entries:
        announce = entry.get("arxiv_announce_type", "")
        if announce and announce != "new":
            continue

        arxiv_id = _extract_id(entry)
        if not arxiv_id:
            continue

        title = _strip_html(getattr(entry, "title", "") or "")
        abstract = _strip_html(getattr(entry, "summary", "") or "")
        authors = _extract_authors(entry)
        link = getattr(entry, "link", "") or entry.get("link", "")
        pub_date = _extract_date(entry)

        papers.append(
            Paper(
                id=arxiv_id,
                title=title,
                abstract=abstract,
                authors=authors,
                url=link,
                source=label,
                date=pub_date,
            )
        )
    return papers
