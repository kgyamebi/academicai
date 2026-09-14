#!/bin/sh
set -eu

STORAGE_PATH="${STORAGE_LOCAL_PATH:-/data/storage}"
mkdir -p "$STORAGE_PATH"

if [ "$(id -u)" = "0" ]; then
  chown -R 10001:10001 "$STORAGE_PATH" || true
  exec setpriv --reuid=10001 --regid=10001 --init-groups -- "$@"
fi

exec "$@"
