#!/bin/bash
set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"
echo "=== 栖所 Perch 启动 ==="

# Kill existing processes on target ports
for port in 5000 3000; do
    pid=$(ss -tlnp "sport = :$port" 2>/dev/null | grep -oP 'pid=\K\d+' || true)
    if [ -n "$pid" ]; then
        kill -9 "$pid" 2>/dev/null || true
        sleep 0.5
    fi
done

# Start backend
cd "$ROOT/backend"
python app.py &
BACKEND_PID=$!
echo "[Backend] 启动中... PID: $BACKEND_PID"

# Start frontend
cd "$ROOT/frontend"
npm run dev &
FRONTEND_PID=$!
echo "[Frontend] 启动中... PID: $FRONTEND_PID"

sleep 3

# Verify
if ss -tlnp "sport = :5000" 2>/dev/null | grep -q LISTEN; then
    echo "[Backend]  http://localhost:5000  ✓"
else
    echo "[Backend]  启动失败" >&2
fi

if ss -tlnp "sport = :3000" 2>/dev/null | grep -q LISTEN; then
    IP=$(ip -4 addr show | grep -oP 'inet \K[\d.]+' | grep -v '127.0.0.1' | head -1)
    echo "[Frontend] http://localhost:3000  ✓"
    [ -n "$IP" ] && echo "[Network]  http://${IP}:3000  (其他设备)"
else
    echo "[Frontend] 启动失败" >&2
fi

wait