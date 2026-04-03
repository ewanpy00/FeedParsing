from __future__ import annotations

import datetime as dt
from typing import Optional

from pydantic import BaseModel, HttpUrl


class PostIn(BaseModel):
    source: str
    title: str
    link: HttpUrl
    published_at: Optional[dt.datetime] = None
    content_hash: str


class PostOut(PostIn):
    id: int
    sent_at: Optional[dt.datetime] = None
