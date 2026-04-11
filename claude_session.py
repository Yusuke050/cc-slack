import asyncio
import json
import logging
from pathlib import Path

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ResultMessage,
    query,
)

from config import CLAUDE_CWD, CLAUDE_PERMISSION_MODE

logger = logging.getLogger(__name__)

SESSION_ID_FILE = Path(__file__).parent / ".session_id"


class ClaudeSession:
    """claude_agent_sdk を使った Claude Code セッション管理。

    send() でプロンプトを送信し、テキスト応答を返す。
    セッションIDを保存し、再起動後も会話を復元する。
    """

    def __init__(self, cwd: str | None = None):
        self._cwd = cwd or CLAUDE_CWD
        self._lock = asyncio.Lock()
        self._session_id: str | None = None
        self._connected = False

    def _load_session_id(self) -> str | None:
        try:
            if SESSION_ID_FILE.exists():
                sid = SESSION_ID_FILE.read_text().strip()
                if sid:
                    logger.info("Loaded saved session_id: %s", sid)
                    return sid
        except OSError:
            logger.warning("Failed to load session_id", exc_info=True)
        return None

    def _save_session_id(self, sid: str) -> None:
        try:
            SESSION_ID_FILE.write_text(sid)
            logger.info("Saved session_id: %s", sid)
        except OSError:
            logger.warning("Failed to save session_id", exc_info=True)

    def _load_mcp_servers(self) -> dict:
        config_path = Path.home() / ".claude.json"
        try:
            if config_path.exists():
                data = json.loads(config_path.read_text())
                best_proj, best_servers = "", {}
                for proj, cfg in data.get("projects", {}).items():
                    if self._cwd.startswith(proj) and len(proj) > len(best_proj):
                        servers = cfg.get("mcpServers", {})
                        if servers:
                            best_proj, best_servers = proj, servers
                if best_servers:
                    # stdio型サーバーのPATHにシステムパスを追加
                    for name, srv in best_servers.items():
                        if srv.get("env", {}).get("PATH"):
                            sys_path = "/usr/local/bin:/usr/bin:/bin"
                            srv["env"]["PATH"] = srv["env"]["PATH"] + ":" + sys_path
                        srv.setdefault("env", {})["HOME"] = str(Path.home())
                    logger.info("Loaded MCP servers from %s: %s", best_proj, list(best_servers.keys()))
                    return best_servers
        except (OSError, json.JSONDecodeError):
            logger.warning("Failed to load MCP servers", exc_info=True)
        return {}

    def _build_options(self) -> ClaudeAgentOptions:
        saved_id = self._load_session_id()
        mcp = self._load_mcp_servers()

        allowed = []
        for name in mcp:
            allowed.append(f"mcp__{name}__*")

        opts = ClaudeAgentOptions(
            permission_mode=CLAUDE_PERMISSION_MODE,
            cwd=self._cwd,
            resume=saved_id,
            mcp_servers=mcp,
            allowed_tools=allowed,
        )
        return opts

    async def connect(self) -> None:
        self._session_id = self._load_session_id()
        self._connected = True
        if self._session_id:
            logger.info("Claude session ready (resume=%s, cwd=%s)", self._session_id, self._cwd)
        else:
            logger.info("Claude session ready (new, cwd=%s)", self._cwd)

    async def disconnect(self) -> None:
        self._connected = False
        logger.info("Claude session disconnected")

    async def send(self, prompt: str) -> str:
        if not self._connected:
            raise RuntimeError("Session not connected. Call connect() first.")

        async with self._lock:
            options = self._build_options()
            texts: list[str] = []

            try:
                async for msg in query(prompt=prompt, options=options):
                    if isinstance(msg, AssistantMessage):
                        for block in msg.content:
                            if hasattr(block, "text"):
                                texts.append(block.text)
                    elif isinstance(msg, ResultMessage):
                        if msg.session_id:
                            self._session_id = msg.session_id
                            self._save_session_id(msg.session_id)
                        if msg.is_error:
                            return f"Error: {msg.result or 'unknown error'}"
                        break
            except Exception:
                logger.exception("Query failed")
                return "エラーが発生しました。ログを確認してください。"

            return "\n".join(texts) if texts else "(no response)"

    @property
    def is_connected(self) -> bool:
        return self._connected
