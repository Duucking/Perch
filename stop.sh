#!/bin/bash
echo "=== 栖所 Perch 停止 ==="

stopped=0
for port in 5000 3000; do
    pid=$(ss -tlnp "sport = :$port" 2>/dev/null | grep -oP 'pid=\K\d+' || true)
    if [ -n "$pid" ]; then
        kill -9 "$pid" 2>/dev/null || true
        echo "  Port $port (PID $pid) 已停止"
        stopped=$((stopped + 1))
    fi
done

if [ "$stopped" -eq 0 ]; then
    echo "没有运行中的服务"
else
    echo "共停止 $stopped 个服务"
fi