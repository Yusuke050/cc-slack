"""Slack にファイルを送信する CLI スクリプト。

Usage:
    uv run python send_file.py <file_path> <channel_id> [message]

Examples:
    uv run python send_file.py ../papers/pose_estimation_ml/01.pdf C07XXXXXX
    uv run python send_file.py ../papers/pose_estimation_ml/01.pdf C07XXXXXX "論文です"
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")


def send_file(file_path: str, channel: str, message: str = "") -> None:
    from slack_sdk import WebClient
    from slack_sdk.errors import SlackApiError

    token = os.getenv("SLACK_BOT_TOKEN")
    if not token:
        print("Error: SLACK_BOT_TOKEN が設定されていません")
        sys.exit(1)

    client = WebClient(token=token)
    p = Path(file_path)
    if not p.exists():
        print(f"Error: {p} が見つかりません")
        sys.exit(1)

    try:
        resp = client.files_upload_v2(
            channel=channel,
            file=str(p.resolve()),
            filename=p.name,
            title=p.stem,
            initial_comment=message or f"📎 {p.name}",
        )
        if resp["ok"]:
            print(f"送信完了: {p.name} → {channel}")
        else:
            print(f"送信失敗: {resp['error']}")
            sys.exit(1)
    except SlackApiError as e:
        print(f"送信失敗: {e.response['error']}")
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: uv run python send_file.py <file_path> <channel_id> [message]")
        sys.exit(1)

    file_path = sys.argv[1]
    channel = sys.argv[2]
    message = sys.argv[3] if len(sys.argv) > 3 else ""
    send_file(file_path, channel, message)
