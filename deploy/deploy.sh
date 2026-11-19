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
