import asyncio
import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from slack_sdk import WebClient

from claude_session import ClaudeSession
from config import SCHEDULES
from slack_utils import post_message

logger = logging.getLogger(__name__)


def _run_async(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def _execute_scheduled_job(
    session: ClaudeSession, client: WebClient, channel: str, prompt: str, name: str
):
    logger.info("Scheduled job '%s' started: %s", name, prompt)
    try:
        result = _run_async(session.send(prompt))
        post_message(client, channel, f"*[定期実行: {name}]*\n{result}")
        logger.info("Scheduled job '%s' completed", name)
    except Exception:
        logger.exception("Scheduled job '%s' failed", name)
        post_message(client, channel, f"*[定期実行: {name}]* エラーが発生しました。")


def start_scheduler(session: ClaudeSession, client: WebClient) -> BackgroundScheduler:
    scheduler = BackgroundScheduler()

    for schedule in SCHEDULES:
        name = schedule["name"]
        cron_expr = schedule["cron"]
        channel = schedule["channel"]
        prompt = schedule["prompt"]

        trigger = CronTrigger.from_crontab(cron_expr)
        scheduler.add_job(
            _execute_scheduled_job,
            trigger=trigger,
            args=[session, client, channel, prompt, name],
            id=name,
            name=name,
        )
        logger.info("Registered schedule '%s': %s -> %s", name, cron_expr, prompt)

    if SCHEDULES:
        scheduler.start()
        logger.info("Scheduler started with %d jobs", len(SCHEDULES))
    else:
        logger.info("No schedules configured")

    return scheduler
