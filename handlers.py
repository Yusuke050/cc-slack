import logging
import re

from slack_bolt.async_app import AsyncApp

from claude_session import ClaudeSession
from slack_utils import add_reaction, remove_reaction, reply

logger = logging.getLogger(__name__)


def _strip_mention(text: str) -> str:
    """<@BOT_ID> メンション部分を除去して純粋な指示テキストを返す。"""
    return re.sub(r"<@[A-Z0-9]+>\s*", "", text).strip()


def register_handlers(app: AsyncApp, session: ClaudeSession) -> None:
    @app.event("app_mention")
    async def handle_mention(event, say, client):
        logger.info("Received mention event: %s", event)
        text = _strip_mention(event.get("text", ""))
        if not text:
            await say(text="指示を入力してください。例: `@cc PRレビューして`", thread_ts=event["ts"])
            return

        channel = event["channel"]
        thread_ts = event.get("thread_ts", event["ts"])
        message_ts = event["ts"]

        await add_reaction(client, channel, message_ts, "hourglass_flowing_sand")

        try:
            result = await session.send(text)
            await reply(client, channel, thread_ts, result)
            await remove_reaction(client, channel, message_ts, "hourglass_flowing_sand")
            await add_reaction(client, channel, message_ts, "white_check_mark")
        except Exception:
            logger.exception("Claude execution failed")
            await remove_reaction(client, channel, message_ts, "hourglass_flowing_sand")
            await add_reaction(client, channel, message_ts, "x")
            await reply(client, channel, thread_ts, "エラーが発生しました。ログを確認してください。")
