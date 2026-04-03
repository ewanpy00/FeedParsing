from __future__ import annotations

import html
import time
import requests
from requests.exceptions import RequestException, ReadTimeout

class Notifier:
    def __init__(self, bot_token: str, chat_id: str) -> None:
        self._token = bot_token
        self._chat_id = chat_id

    def send_new_post(self, title: str, link: str) -> None:
        text = f"<b>{html.escape(title)}</b>\n{html.escape(link)}"
        
        try:
            r = requests.post(
                f"https://api.telegram.org/bot{self._token}/sendMessage",
                json={
                    "chat_id": self._chat_id,
                    "text": text,
                    "parse_mode": "HTML",
                    "disable_web_page_preview": False,
                },
                timeout=30,
            )
            r.raise_for_status()
            time.sleep(1)

        except (requests.exceptions.RequestException, ConnectionError) as e:
            print(f"Ошибка Telegram API: {e}")
