import asyncio
import logging

from slack_bolt.async_app import AsyncApp
from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler

from claude_session import ClaudeSession
from config import SLACK_APP_TOKEN, SLACK_BOT_TOKEN
from handlers import register_handlers
# from scheduler import start_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def main():
    app = AsyncApp(token=SLACK_BOT_TOKEN)

    session = ClaudeSession()
    await session.connect()
    logger.info("Claude session ready")

    register_handlers(app, session)

    logger.info("Starting Slack bot (Socket Mode)...")
    handler = AsyncSocketModeHandler(app, SLACK_APP_TOKEN)

    try:
        await handler.start_async()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        await session.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
