from __future__ import annotations

import calendar
import datetime as dt
import hashlib
import logging
from typing import Any

import feedparser

from models import PostIn

log = logging.getLogger(__name__)


def _parsed_struct_to_dt(st: tuple[int, ...] | None) -> dt.datetime | None:
    if not st:
        return None
    return dt.datetime.fromtimestamp(calendar.timegm(st), tz=dt.timezone.utc)


def _entry_plain_body(entry: dict[str, Any]) -> str:
    parts: list[str] = []
    summary = (entry.get("summary") or "").strip()
    desc = (entry.get("description") or "").strip()
    if summary:
        parts.append(summary)
    if desc and desc != summary:
        parts.append(desc)
    content = entry.get("content")
    if isinstance(content, list):
        for block in content:
            if isinstance(block, dict):
                val = (block.get("value") or "").strip()
                if val:
                    parts.append(val)
    return "\n".join(parts)


def _content_hash(title: str, link: str, body: str) -> str:
    normalized = "\n".join([title.strip(), link.strip(), body.strip()])
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _feed_source(feed: Any) -> str:
    return (
        (getattr(feed, "feed", None) and (feed.feed.get("link") or feed.feed.get("title")))
        or ""
    ).strip() or "(rss)"


class RSSParser:
    """Скачивает и разбирает RSS, отдаёт нормализованные `PostIn`."""

    def __init__(self, rss_url: str) -> None:
        self._rss_url = rss_url

    def fetch_posts(self) -> tuple[str, list[PostIn]]:
        parsed = feedparser.parse(self._rss_url)
        if getattr(parsed, "bozo", False) and not getattr(parsed, "entries", None):
            log.warning("RSS parse issue: %s", getattr(parsed, "bozo_exception", "unknown"))

        source = _feed_source(parsed)[:200] or self._rss_url[:200]
        posts: list[PostIn] = []
        for entry in getattr(parsed, "entries", []) or []:
            link = (entry.get("link") or "").strip()
            if not link:
                continue
            title = (entry.get("title") or "(no title)").strip()
            body = _entry_plain_body(entry)
            published = _parsed_struct_to_dt(entry.get("published_parsed")) or _parsed_struct_to_dt(
                entry.get("updated_parsed")
            )
            h = _content_hash(title, link, body)
            posts.append(
                PostIn(
                    source=source,
                    title=title[:500],
                    link=link,
                    published_at=published,
                    content_hash=h,
                )
            )
        return source, posts
