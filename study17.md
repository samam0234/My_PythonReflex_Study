# study17 — Docker·외부 배포 자동화

목표: 검증된 Reflex 앱을 비루트 이미지·영속 DB·TLS·자동 배포·롤백으로 연결한다.

실제 구현: [project/Dockerfile](project/Dockerfile), [deploy/README.md](deploy/README.md). 설치·검증 명령은 [README](README.md)를 따른다.

## 📖 이론

실제 구현은 [Dockerfile](project/Dockerfile), [Compose](deploy/compose.yml), [배포 절차](deploy/README.md), [deploy.sh](deploy/deploy.sh), [CI](.github/workflows/ci.yml)다. 대상은 Linux VM 한 대·Reflex 인스턴스 하나다. 단일 인스턴스 교체에는 짧은 중단이 있다.

노션의 migration 후 실행 흐름을 배포의 별도 migration 단계로 분리했다. 기존 DB를 보존하고 온라인 백업 후 앱을 중지해 migration 중 쓰기를 막는다. 여러 앱을 동시에 띄워 같은 SQLite를 공유하지 않는다.

## 🛠️ 실기(코드·줄별 설명)

```dockerfile
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
```

- 기반 Python·UTF-8·즉시 로그 출력을 정한다.
- `requirements.lock`은 Python 3.12 / Linux의 전이 의존성과 해시를 고정한다.
- 빌드 도구 설치 후 UID 10001 사용자와 DB 디렉터리 권한을 만든다.
- 소스를 복사한 뒤 비루트 사용자로 export·run한다.
- 공개 API URL은 빌드 인자이며 비밀 키가 아니다. 실제 TLS 도메인을 사용한다.
- entrypoint는 CMD를 exec한다. migration은 자동으로 중복 실행하지 않는다.
- prod는 3000 단일 포트다. `--single-port`에 서로 다른 frontend/backend 포트를 함께 지정하지 않는다.

실제 Compose:

```yaml
services:
  app:
    image: ${APP_IMAGE:?APP_IMAGE is required}
    restart: unless-stopped
    env_file: .env.runtime
    environment:
      APP_DB_URL: sqlite:////data/reflex.db
      REFLEX_DB_URL: sqlite:////data/reflex.db
      APP_ENV: production
      APP_API_URL: https://${APP_DOMAIN:?APP_DOMAIN is required}
      REFLEX_API_URL: https://${APP_DOMAIN}
      APP_FRONTEND_ORIGIN: https://${APP_DOMAIN}
      REFLEX_CORS_ALLOWED_ORIGINS: https://${APP_DOMAIN}
    volumes:
      - board_data:/data
    expose:
      - "3000"
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:3000/health/ready', timeout=3)"]
      interval: 15s
      timeout: 5s
      retries: 4
      start_period: 30s
    mem_limit: 1g
  proxy:
    image: caddy:2.10.2
    restart: unless-stopped
    environment:
      APP_DOMAIN: ${APP_DOMAIN}
    depends_on:
      app:
        condition: service_healthy
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile:ro
      - caddy_data:/data
      - caddy_config:/config
volumes:
  board_data:
  caddy_data:
  caddy_config:
```

앱 포트는 내부 네트워크에만 노출한다. 영속 볼륨 `/data`와 서버 전용 `.env.runtime`을 사용한다. readiness는 실제 테이블 질의를 확인한다. proxy는 readiness 성공을 기다린 뒤 외부 80·443을 받는다. `REFLEX_CORS_ALLOWED_ORIGINS`는 **쉼표 구분 문자열**이며 JSON 배열 문자열을 넣지 않는다.

실제 배포 스크립트:

```bash
#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
image=${1:?commit SHA image is required}
if [[ ! "$image" =~ ^ghcr.io/[a-z0-9._/-]+:[a-f0-9]{40}$ ]]; then
  echo '유효한 GHCR 커밋 SHA 이미지를 지정하세요.' >&2
  exit 2
fi
export APP_IMAGE="$image"
docker compose config --quiet
docker compose pull app
if [[ -n "$(docker compose ps --status running -q app)" ]]; then
  stamp=$(date -u +%Y%m%dT%H%M%S)
  docker compose exec -T app python -m project.manage backup "/data/backups/pre-${stamp}.db"
fi
# 단일 인스턴스의 계획된 중단. migration 실패 시 멈춘 상태로 복원을 판단한다.
docker compose stop app
docker compose run --rm --no-deps app reflex db migrate
docker compose up -d --wait --wait-timeout 180
# 성공한 이미지만 저장하고 APP_DOMAIN 등 다른 설정은 보존한다.
tmp_env=$(mktemp .env.XXXXXX)
awk -v image="$image" 'BEGIN {found=0} /^APP_IMAGE=/ {print "APP_IMAGE=" image;found=1;next} {print} END {if(!found) print "APP_IMAGE=" image}' .env > "$tmp_env"
chmod 600 "$tmp_env"
mv -f -- "$tmp_env" .env
echo '배포 및 DB readiness 확인 완료. 외부 브라우저 smoke test를 이어서 수행하세요.'
```

1. 보유 도메인의 DNS·VM Docker·GHCR 읽기 자격을 준비한다.
2. `deploy/` 내용을 `/srv/reflex/`에 복사한다. `.env.example`, `.env.runtime.example`을 서버 전용 파일로 복사하고 권한을 제한한다.
3. 같은 도메인의 `PUBLIC_API_URL`로 SHA 태그 이미지를 빌드한다.
4. 스크립트는 image 검증→다운로드→기존 DB 백업→앱 중지→migration→readiness 대기 순서로 실행한다.
5. 성공한 이미지 설정만 `.env`에 기록한다. migration 실패면 새 앱을 시작하지 않는다.
6. 외부에서 로그인·CRUD·새로고침·타인 권한 거부·WebSocket을 확인한다.
7. 스키마 호환성을 확인한 뒤 [rollback.sh](deploy/rollback.sh)에 이전 이미지를 지정한다. 파괴적 migration은 별도 DB 복원이 필요하다.

```powershell
python tools/check_deploy.py
python tools/verify_app.py --app project --mode prod
```

첫 줄은 자격증명 없이 Compose 해석·CI 의존성·배포 셸 문법을 검사한다. 둘째 줄은 로컬 prod 빌드와 실제 브라우저를 검증한다. Docker daemon이 꺼져 있는 현재 환경에서는 이미지 실행과 외부 VM 배포를 수행하지 않았다.

## 오류 노트

- `.env.runtime`·DB·가상환경·생성 `.web/`는 이미지 context에서 제외한다.
- runtime 변수만 바꾸어 이미 빌드한 API URL이 교체된다고 가정하지 않는다.
- 볼륨 UID와 컨테이너 UID를 맞춘다.
- 페이지는 열리고 이벤트만 실패하면 TLS·API 주소·허용 origin·WebSocket을 확인한다.
- Actions production 자격과 `DEPLOY_ENABLED`가 없으면 배포 job은 건너뛴다. 파일 작성은 외부 배포 성공 기록이 아니다.

## ☐ 체크리스트

- ☐ [노션 Docker 기록] migration과 prod 실행의 순서를 배포 단계로 재현한다.
- ☐ 비루트·해시 lock·비밀 제외·영속 볼륨·readiness를 확인한다.
- ☐ CI 테스트·세 앱 prod E2E 성공 이후에만 SHA 이미지를 게시한다.
- ☐ [노션 배포 목표] 실제 외부 TLS·WebSocket·DB 유지 결과를 별도로 기록한다.
- ☐ migration 실패 중단·백업 복원·호환되는 이전 이미지 롤백을 시험한다.

## 다음 단계 연결

[study18](study18.md)에서 서버 키와 제한된 MCP 도구를 연결한다.
