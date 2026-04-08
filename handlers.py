import asyncio
import logging
import re
import threading

from slack_bolt import App

from claude_session import ClaudeSession
from slack_utils import add_reaction, remove_reaction, reply

logger = logging.getLogger(__name__)


def _run_async(coro):
    """非同期コルーチンを別スレッドのイベントループで実行する。"""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def _strip_mention(text: str) -> str:
    """<@BOT_ID> メンション部分を除去して純粋な指示テキストを返す。"""
    return re.sub(r"<@[A-Z0-9]+>\s*", "", text).strip()


def register_handlers(app: App, session: ClaudeSession) -> None:
    @app.event("app_mention")
    def handle_mention(event, say, client):
        text = _strip_mention(event.get("text", ""))
        if not text:
            say(text="指示を入力してください。例: `@claude PRレビューして`", thread_ts=event["ts"])
            return

        channel = event["channel"]
        thread_ts = event.get("thread_ts", event["ts"])
        message_ts = event["ts"]

        add_reaction(client, channel, message_ts, "hourglass_flowing_sand")

        def process():
            try:
                result = _run_async(session.send(text))
                reply(client, channel, thread_ts, result)
                remove_reaction(client, channel, message_ts, "hourglass_flowing_sand")
                add_reaction(client, channel, message_ts, "white_check_mark")
            except Exception:
                logger.exception("Claude execution failed")
                remove_reaction(client, channel, message_ts, "hourglass_flowing_sand")
                add_reaction(client, channel, message_ts, "x")
                reply(client, channel, thread_ts, "エラーが発生しました。ログを確認してください。")

        thread = threading.Thread(target=process, daemon=True)
        thread.start()
