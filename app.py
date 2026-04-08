import asyncio
import logging

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from claude_session import ClaudeSession
from config import SLACK_APP_TOKEN, SLACK_BOT_TOKEN
from handlers import register_handlers
from scheduler import start_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    app = App(token=SLACK_BOT_TOKEN)

    session = ClaudeSession()
    asyncio.get_event_loop().run_until_complete(session.connect())
    logger.info("Claude session ready")

    register_handlers(app, session)
    start_scheduler(session, app.client)

    logger.info("Starting Slack bot (Socket Mode)...")
    handler = SocketModeHandler(app, SLACK_APP_TOKEN)

    try:
        handler.start()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        asyncio.get_event_loop().run_until_complete(session.disconnect())


if __name__ == "__main__":
    main()
