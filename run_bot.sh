#!/usr/bin/env bash

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

mkdir -p bot/logs

if [[ -f bot/telegram_bot.pid ]]; then
    existing_pid="$(cat bot/telegram_bot.pid)"
    if kill -0 "$existing_pid" 2>/dev/null; then
        echo "Bot is already running with PID $existing_pid"
        exit 0
    fi
    rm -f bot/telegram_bot.pid
fi

nohup python3 bot/telegram_bot.py \
    > /dev/null 2>&1 &

echo $! > bot/telegram_bot.pid
echo "Bot started with PID $(cat bot/telegram_bot.pid)"
echo "Log: $PROJECT_ROOT/bot/logs/telegram_bot.log"
