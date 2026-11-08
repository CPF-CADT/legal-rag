#!/usr/bin/env bash

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"
PID_FILE="apps/telegram_bot/telegram_bot.pid"

if [[ ! -f "$PID_FILE" ]]; then
    echo "Bot is not running: PID file not found"
    exit 0
fi

pid="$(cat "$PID_FILE")"
if ! [[ "$pid" =~ ^[0-9]+$ ]]; then
    echo "Invalid PID file: $PID_FILE" >&2
    exit 1
fi

if ! kill -0 "$pid" 2>/dev/null; then
    rm -f "$PID_FILE"
    echo "Bot was not running; removed stale PID file"
    exit 0
fi

process_command="$(ps -p "$pid" -o command= || true)"
if [[ "$process_command" != *"apps.telegram_bot.main"* ]]; then
    echo "Refusing to stop PID $pid because it is not the LegalRAG bot:" >&2
    echo "$process_command" >&2
    exit 1
fi

kill "$pid"
for _ in {1..10}; do
    if ! kill -0 "$pid" 2>/dev/null; then
        rm -f "$PID_FILE"
        echo "Bot stopped"
        exit 0
    fi
    sleep 1
done

echo "Bot did not stop within 10 seconds; PID $pid remains running" >&2
exit 1
