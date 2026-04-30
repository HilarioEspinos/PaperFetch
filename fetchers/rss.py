from __future__ import annotations
import hashlib
import html
import re
import sys
from datetime import date, datetime
from time import struct_time

import feedparser
import requests

from filter import Paper

_HTML_TAG_RE = re.compile(r"<[^>]+>")


def _strip_html(text: str) -> str:
    return _HTML_TAG_RE.sub("", html.unescape(text)).strip()


def _extract_id(entry: feedparser.FeedParserDict, label: str) -> str:
    raw = getattr(entry, "id", "") or entry.get("id", "")
    if not raw:
        raw = getattr(entry, "link", "") or entry.get("link", "")
    if not raw:
        raw = (getattr(entry, "title", "") or "") + label
    slug = hashlib.sha256(f"{label}:{raw}".encode()).hexdigest()[:20]
    return slug


def _extract_abstract(entry: feedparser.FeedParserDict) -> str:
    summary = getattr(entry, "summary", None) or entry.get("summary", "")
    if summary:
        return _strip_html(summary)
    content = entry.get("content", [])
    if content:
        return _strip_html(content[0].get("value", ""))
    return ""


def _extract_authors(entry: feedparser.FeedParserDict) -> list[str]:
    authors = getattr(entry, "authors", None)
    if authors:
        names = [a.get("name", "") for a in authors if a.get("name")]
        if names:
            return names
    raw = getattr(entry, "author", "") or entry.get("author", "")
    if raw:
        # split on "; " first, then ", " as fallback
        if ";" in raw:
            return [p.strip() for p in raw.split(";") if p.strip()]
        return [p.strip() for p in raw.split(",") if p.strip()]
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


def fetch_rss(url: str, label: str) -> list[Paper]:
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
        paper_id = _extract_id(entry, label)
        title = _strip_html(getattr(entry, "title", "") or "")
        abstract = _extract_abstract(entry)
        authors = _extract_authors(entry)
        link = getattr(entry, "link", "") or entry.get("link", "")
        pub_date = _extract_date(entry)

        if not title:
            continue

        papers.append(
            Paper(
                id=paper_id,
                title=title,
                abstract=abstract,
                authors=authors,
                url=link,
                source=label,
                date=pub_date,
            )
        )
    return papers
