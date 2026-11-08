#!/usr/bin/env bash

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"
export PYTHONPATH="$PROJECT_ROOT:$PROJECT_ROOT/apps/core:$PROJECT_ROOT/data-pipeline${PYTHONPATH:+:$PYTHONPATH}"

mkdir -p apps/telegram_bot/logs

if [[ -f apps/telegram_bot/telegram_bot.pid ]]; then
    existing_pid="$(cat apps/telegram_bot/telegram_bot.pid)"
    if kill -0 "$existing_pid" 2>/dev/null; then
        echo "Bot is already running with PID $existing_pid"
        exit 0
    fi
    rm -f apps/telegram_bot/telegram_bot.pid
fi

nohup python3 -m apps.telegram_bot.main \
    > /dev/null 2>&1 &

echo $! > apps/telegram_bot/telegram_bot.pid
echo "Bot started with PID $(cat apps/telegram_bot/telegram_bot.pid)"
echo "Log: $PROJECT_ROOT/apps/telegram_bot/logs/telegram_bot.log"
