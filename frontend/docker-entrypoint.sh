#!/bin/sh
set -e

# Substitute runtime config into the static config.js at container startup.
# This is what lets one prebuilt image be configured per deployment via env
# vars (API_URL, OIDC_ISSUER, OIDC_CLIENT_ID) instead of baking them at build
# time. Only our known tokens are substituted so nothing else in the file is
# touched.
CONFIG_FILE=./dist/config.js

envsubst '${API_URL} ${OIDC_ISSUER} ${OIDC_CLIENT_ID}' \
  < "$CONFIG_FILE" > "$CONFIG_FILE.tmp"
mv "$CONFIG_FILE.tmp" "$CONFIG_FILE"

echo "Runtime config:"
cat "$CONFIG_FILE"

exec "$@"
