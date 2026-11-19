#!/bin/sh
set -eu
# migration은 deploy.sh의 별도 단계에서 한 번 실행한다.
exec "$@"
