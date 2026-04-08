import logging

logger = logging.getLogger(__name__)

SLACK_MESSAGE_LIMIT = 4000


async def add_reaction(client, channel: str, timestamp: str, name: str) -> None:
    try:
        await client.reactions_add(channel=channel, timestamp=timestamp, name=name)
    except Exception:
        logger.warning("Failed to add reaction :%s:", name, exc_info=True)


async def remove_reaction(client, channel: str, timestamp: str, name: str) -> None:
    try:
        await client.reactions_remove(channel=channel, timestamp=timestamp, name=name)
    except Exception:
        logger.warning("Failed to remove reaction :%s:", name, exc_info=True)


async def reply(client, channel: str, thread_ts: str, text: str) -> None:
    """スレッドに返信する。4000文字を超える場合はファイルとしてアップロード。"""
    if len(text) <= SLACK_MESSAGE_LIMIT:
        await client.chat_postMessage(channel=channel, thread_ts=thread_ts, text=text)
    else:
        await client.files_upload_v2(
            channel=channel,
            thread_ts=thread_ts,
            content=text,
            filename="response.md",
            title="Claude Code Response",
        )
        await client.chat_postMessage(
            channel=channel,
            thread_ts=thread_ts,
            text=f"結果をファイルとして添付しました ({len(text)}文字)",
        )


async def post_message(client, channel: str, text: str) -> None:
    """チャンネルにメッセージを投稿する（定期実行用）。"""
    if len(text) <= SLACK_MESSAGE_LIMIT:
        await client.chat_postMessage(channel=channel, text=text)
    else:
        await client.files_upload_v2(
            channel=channel,
            content=text,
            filename="response.md",
            title="Claude Code Response",
        )
