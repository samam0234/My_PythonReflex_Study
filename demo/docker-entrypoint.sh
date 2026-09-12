#!/bin/sh
set -e

# 컨테이너가 시작할 때마다 마이그레이션을 적용한다 (이미 적용된 건 건너뜀).
reflex db migrate

exec reflex run --env prod --single-port --backend-host 0.0.0.0
