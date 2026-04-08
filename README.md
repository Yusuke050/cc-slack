# cc-slack

SlackからローカルのClaude Codeを操作するBot。

## 何ができるか

- Slackで `@Claude Code PRレビューして` と投稿すると、ローカルマシン上のClaude Codeが実行され、結果が同じスレッドに返信される
- 会話のコンテキストが維持されるので、「さっきの修正して」のような続きの指示も可能
- `@claude` なしのメッセージは無視されるので、同じチャンネルにメモや雑談を書いても問題ない
- APSchedulerによる定期実行（毎朝のPRまとめなど）にも対応

## 仕組み

```
Slack (プライベートチャンネル)
  ↓ Socket Mode (WebSocket)
app.py (ローカルマシンで常駐)
  ↓
Claude Code SDK (CLIをサブプロセスとして制御)
  ↓
ローカルの claude CLI が実行される
  ↓
結果を Slack スレッドに返信
```

- Slack AppのSocket Modeを使うので、外部公開やngrokは不要
- Claude Code SDKがローカルの `claude` CLIをサブプロセスとして起動・制御する
- セッションは常駐しているので、権限の許可は初回のみ、コンテキストも蓄積される

## ファイル構成

| ファイル | 役割 |
|---|---|
| `app.py` | エントリポイント。Slack Bot起動、Claudeセッション接続、スケジューラ起動を行う |
| `handlers.py` | Slackの `app_mention` イベントを受信し、Claudeにプロンプトを送って結果を返信する |
| `claude_session.py` | Claude Code SDKの `ClaudeSDKClient` を使った常駐セッション管理。`send()` でプロンプトを送り、テキスト応答を返す |
| `scheduler.py` | APSchedulerで定期実行ジョブを管理。cron式でスケジュールされたプロンプトをClaudeに送り、結果をチャンネルに投稿する |
| `slack_utils.py` | Slack返信のヘルパー。4000文字超の場合はファイルアップロードに切り替え。リアクション(⏳/✅/❌)の付与も行う |
| `config.py` | `.env` と `config.yaml` から設定を読み込む |
| `config.yaml` | Claudeの作業ディレクトリ、権限モード、定期実行スケジュールの設定 |

## 処理の流れ

### メンション実行

1. ユーザーがSlackで `@Claude Code PRレビューして` と投稿
2. `handlers.py` が `app_mention` イベントを受信、即座にack
3. 元メッセージに ⏳ リアクションを付与
4. バックグラウンドスレッドで `claude_session.send("PRレビューして")` を実行
5. Claude Code SDKが常駐セッション経由でCLIにプロンプトを送信
6. 応答テキストを同じスレッドに返信
7. ⏳ を外して ✅ を付与（エラー時は ❌）

### 定期実行

1. `config.yaml` の `schedules` に定義されたジョブをAPSchedulerが管理
2. cron式に基づいて発火し、Claudeにプロンプトを送信
3. 結果を指定チャンネルに投稿

## セットアップ

### 1. Slack App の作成

1. https://api.slack.com/apps → 「Create New App」→「From scratch」
2. 左メニュー「Socket Mode」→ 有効化 → トークン生成 (`xapp-...` = **SLACK_APP_TOKEN**)
3. 左メニュー「OAuth & Permissions」→ Bot Token Scopes に追加:
   - `app_mentions:read`
   - `chat:write`
   - `files:write`
   - `reactions:write`
4. 左メニュー「Event Subscriptions」→ 有効化 → `app_mention` イベントを追加
5. 左メニュー「Install App」→ ワークスペースにインストール → トークン取得 (`xoxb-...` = **SLACK_BOT_TOKEN**)

### 2. 環境変数

```bash
cp .env.example .env
```

`.env` にトークンを記入:

```
SLACK_BOT_TOKEN=xoxb-...
SLACK_APP_TOKEN=xapp-...
```

### 3. config.yaml の設定

```yaml
claude:
  cwd: /Users/yusuke/code/myrepo   # Claude Codeの作業ディレクトリ（CLAUDE.mdがある場所）
  permission_mode: bypassPermissions

schedules: []
  # 定期実行の例:
  # - name: morning_summary
  #   cron: "0 7 * * 1-5"
  #   channel: "#dev"
  #   prompt: "昨日マージされたPRをまとめて"
```

### 4. 起動

```bash
uv run python app.py
```

### 5. Slackで使う

1. プライベートチャンネルを作成
2. `/invite @Claude Code` でBotを招待
3. `@Claude Code こんにちは` と投稿してテスト
