import os
from pathlib import Path

import yaml
from dotenv import load_dotenv

load_dotenv()

SLACK_BOT_TOKEN = os.environ["SLACK_BOT_TOKEN"]
SLACK_APP_TOKEN = os.environ["SLACK_APP_TOKEN"]


def load_config() -> dict:
    config_path = Path(__file__).parent / "config.yaml"
    if config_path.exists():
        with open(config_path) as f:
            return yaml.safe_load(f) or {}
    return {}


CONFIG = load_config()

CLAUDE_CWD = CONFIG.get("claude", {}).get("cwd", str(Path.home()))
CLAUDE_PERMISSION_MODE = CONFIG.get("claude", {}).get("permission_mode", "bypassPermissions")
SCHEDULES = CONFIG.get("schedules", [])
