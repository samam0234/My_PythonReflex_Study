FROM python:3.12-slim

WORKDIR /app

ENV PYTHONUTF8=1 \
    PYTHONIOENCODING=utf-8 \
    PYTHONUNBUFFERED=1

# Reflex는 Node.js 대신 자체적으로 Bun 런타임을 내려받아 프론트엔드를
# 빌드한다. unzip/curl/ca-certificates 정도만 있으면 된다.
RUN apt-get update && apt-get install -y --no-install-recommends \
    unzip curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 이미지를 빌드하는 시점에 프론트엔드를 미리 컴파일해둔다.
# (컨테이너가 뜰 때마다 매번 다시 컴파일하지 않도록 — 시작 시간을 줄인다)
RUN reflex export --frontend-only --no-zip --env prod

EXPOSE 3000

COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

ENTRYPOINT ["docker-entrypoint.sh"]
