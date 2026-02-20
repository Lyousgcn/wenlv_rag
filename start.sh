#!/usr/bin/env bash
set -e

CMD=$1

if [ -z "$CMD" ]; then
  CMD="start"
fi

case "$CMD" in
  start)
    echo "启动所有服务..."
    docker-compose up -d
    ;;
  stop)
    echo "停止所有服务..."
    docker-compose down
    ;;
  restart)
    echo "重启所有服务..."
    docker-compose down
    docker-compose up -d
    ;;
  logs)
    echo "查看应用日志 (按 Ctrl+C 退出)..."
    docker-compose logs -f app
    ;;
  *)
    echo "用法: ./start.sh [start|stop|restart|logs]"
    exit 1
    ;;
esac

