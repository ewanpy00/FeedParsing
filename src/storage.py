from __future__ import annotations

import datetime as dt

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from db import PostRow
from models import PostIn
from notifier import Notifier


class Storage:
    def find_existing(self, session: Session, post: PostIn) -> PostRow | None:
        link = str(post.link)
        row = session.scalar(select(PostRow).where(PostRow.source == post.source, PostRow.link == link))
        if row:
            return row
        return session.scalar(
            select(PostRow).where(PostRow.source == post.source, PostRow.content_hash == post.content_hash)
        )

    def notify_if_pending(self, session: Session, notifier: Notifier, row: PostRow) -> None:
        if row.sent_at is not None:
            return
        notifier.send_new_post(row.title, row.link)
        row.sent_at = dt.datetime.now(dt.timezone.utc)
        session.commit()

    def process_post(self, session: Session, post: PostIn, notifier: Notifier) -> None:
        row = PostRow(
            source=post.source,
            title=post.title,
            link=str(post.link),
            published_at=post.published_at,
            content_hash=post.content_hash,
        )
        session.add(row)
        try:
            session.commit()
        except IntegrityError:
            session.rollback()
            existing = self.find_existing(session, post)
            if existing:
                self.notify_if_pending(session, notifier, existing)
            return
        session.refresh(row)
        self.notify_if_pending(session, notifier, row)
