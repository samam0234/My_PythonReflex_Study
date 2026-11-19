#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
image=${1:?previous compatible image is required}
if [[ ! "$image" =~ ^ghcr.io/[a-z0-9._/-]+:[a-f0-9]{40}$ ]]; then
  exit 2
fi
# DB 스키마가 이전 코드와 호환된다고 확인한 뒤에만 실행한다. downgrade하지 않는다.
export APP_IMAGE="$image"
docker compose pull app
docker compose up -d --wait --wait-timeout 180
tmp_env=$(mktemp .env.XXXXXX)
awk -v image="$image" 'BEGIN {found=0} /^APP_IMAGE=/ {print "APP_IMAGE=" image;found=1;next} {print} END {if(!found) print "APP_IMAGE=" image}' .env > "$tmp_env"
chmod 600 "$tmp_env"
mv -f -- "$tmp_env" .env
