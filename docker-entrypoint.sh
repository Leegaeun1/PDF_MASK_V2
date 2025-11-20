#!/bin/bash

# Redis 호스트 이름을 설정 파일에서 사용하고 있으므로, 그 이름(redis_master)을 사용합니다.
REDIS_HOST="redis_master" 

# Redis가 완전히 준비될 때까지 기다립니다.
echo "Waiting for Redis ($REDIS_HOST)..."
while ! redis-cli -h $REDIS_HOST ping; do
  sleep 1
done
echo "Redis started. Executing Gunicorn..."

# 💡 Java 환경 확인 (디버깅용)
echo "JAVA_HOME is set to: $JAVA_HOME"
if [ -x "$JAVA_HOME/bin/java" ]; then
    echo "Java executable found and ready."
else
    echo "CRITICAL: Java executable NOT found at $JAVA_HOME/bin/java"
fi

# Web 컨테이너의 원래 CMD(Gunicorn)를 실행합니다.
exec "$@"