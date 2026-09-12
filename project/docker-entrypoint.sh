#!/bin/sh
set -e

reflex db migrate

exec reflex run --env prod --single-port --backend-host 0.0.0.0
