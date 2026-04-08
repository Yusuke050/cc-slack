import asyncio
import logging

from claude_code_sdk import (
    AssistantMessage,
    ClaudeCodeOptions,
    ClaudeSDKClient,
    ResultMessage,
    TextBlock,
)

from config import CLAUDE_CWD, CLAUDE_PERMISSION_MODE

logger = logging.getLogger(__name__)


class ClaudeSession:
    """ClaudeSDKClient の常駐セッションを管理する。

    connect() でセッションを開始し、send() でプロンプトを送信する。
    コンテキストはセッションが生きている間蓄積される。
    """

    def __init__(self, cwd: str | None = None):
        self._cwd = cwd or CLAUDE_CWD
        self._client: ClaudeSDKClient | None = None
        self._lock = asyncio.Lock()

    async def connect(self) -> None:
        options = ClaudeCodeOptions(
            permission_mode=CLAUDE_PERMISSION_MODE,
            cwd=self._cwd,
        )
        self._client = ClaudeSDKClient(options)
        await self._client.connect()
        logger.info("Claude session connected (cwd=%s)", self._cwd)

    async def disconnect(self) -> None:
        if self._client:
            await self._client.disconnect()
            self._client = None
            logger.info("Claude session disconnected")

    async def send(self, prompt: str) -> str:
        """プロンプトを送信し、テキスト応答を返す。"""
        if not self._client:
            raise RuntimeError("Session not connected. Call connect() first.")

        async with self._lock:
            await self._client.query(prompt)

            texts: list[str] = []
            async for msg in self._client.receive_response():
                if isinstance(msg, AssistantMessage):
                    for block in msg.content:
                        if isinstance(block, TextBlock):
                            texts.append(block.text)
                elif isinstance(msg, ResultMessage):
                    if msg.is_error:
                        return f"Error: {msg.result or 'unknown error'}"

            return "\n".join(texts) if texts else "(no response)"

    @property
    def is_connected(self) -> bool:
        return self._client is not None
