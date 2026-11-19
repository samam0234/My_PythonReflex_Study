FROM python:3.12-slim
WORKDIR /app
ENV PYTHONUTF8=1 PYTHONIOENCODING=utf-8 PYTHONUNBUFFERED=1 GRANIAN_WORKERS=1
RUN apt-get update && apt-get install -y --no-install-recommends unzip curl ca-certificates && rm -rf /var/lib/apt/lists/*
COPY requirements.lock .
RUN pip install --no-cache-dir --require-hashes -r requirements.lock
RUN useradd --create-home --uid 10001 app && mkdir -p /data && chown app:app /app /data
COPY --chown=app:app . .
RUN chmod +x /app/docker-entrypoint.sh
USER app
ARG PUBLIC_API_URL=https://board.example.com
ENV APP_API_URL=${PUBLIC_API_URL} REFLEX_API_URL=${PUBLIC_API_URL} APP_FRONTEND_ORIGIN=${PUBLIC_API_URL} APP_ENV=production
RUN reflex export --frontend-only --no-zip --env prod
EXPOSE 3000
ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["reflex", "run", "--env", "prod", "--single-port", "--frontend-port", "3000", "--backend-host", "0.0.0.0"]
