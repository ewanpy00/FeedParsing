from __future__ import annotations

import logging
import os

from dotenv import load_dotenv
from sqlalchemy.orm import Session, sessionmaker

from config import Settings
from db import create_session_factory
from notifier import Notifier
from rss_parser import RSSParser
from storage import Storage

log = logging.getLogger(__name__)


def _load_settings() -> Settings:
    load_dotenv()
    return Settings(
        rss_url=os.environ["RSS_URL"],
        poll_interval_seconds=int(os.getenv("POLL_INTERVAL") or "60"),
        telegram_bot_token=os.environ["BOT_TOKEN"],
        telegram_chat_id=os.environ["CHAT_ID"],
        database_url=os.getenv("DATABASE_URL") or "sqlite:///./feed.db",
    )


def poll_feed(settings: Settings, session_factory: sessionmaker[Session]) -> None:
    parser = RSSParser(settings.rss_url)
    notifier = Notifier(settings.telegram_bot_token, settings.telegram_chat_id)
    storage = Storage()

    _source, posts = parser.fetch_posts()
    if not posts:
        log.debug("No entries in feed")
        return

    session = session_factory()
    try:
        for post in posts:
            storage.process_post(session, post, notifier)
    finally:
        session.close()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    try:
        settings = _load_settings()
    except Exception as e:
        log.error(f"Error loading settings: {e}")
        return

    session_factory = create_session_factory(settings.database_url)

    from apscheduler.schedulers.blocking import BlockingScheduler

    poll_feed(settings, session_factory)

    scheduler = BlockingScheduler()
    scheduler.add_job(
        poll_feed,
        "interval",
        seconds=settings.poll_interval_seconds,
        args=[settings, session_factory],
        id="poll_rss",
        coalesce=True,
        max_instances=1,
    )
    log.info("Polling %s every %s s", settings.rss_url, settings.poll_interval_seconds)
    scheduler.start()


if __name__ == "__main__":
    main()
