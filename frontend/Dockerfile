FROM node:22-slim AS builder
WORKDIR /app

# No VITE_* build args: config is injected at RUNTIME (see docker-entrypoint.sh
# + public/config.js), so this image is built once and reconfigured per
# deployment via container env vars.

# Enable pnpm via corepack
RUN corepack enable && corepack prepare pnpm@11.5.2 --activate

# Copy package
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./

# Install depedencies
RUN pnpm install --frozen-lockfile

# Copy code
COPY . .

# Build static files
RUN pnpm run build

FROM node:22-slim AS final

# serve = static file server; gettext-base = envsubst for runtime config
RUN npm install -g serve && \
	apt-get update && apt-get install -y --no-install-recommends gettext-base && \
	rm -rf /var/lib/apt/lists/*

WORKDIR /app/server

# Ensure safe permissions
RUN addgroup --system --gid 1001 appgroup && \
	adduser --system --uid 1001 --ingroup appgroup --home /app/server appuser

# Copy static files + entrypoint
COPY --from=builder /app/dist ./dist
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh && \
	chown -R appuser:appgroup ./dist
USER appuser
EXPOSE 3000

# Entrypoint substitutes runtime config into dist/config.js, then serves.
ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["serve", "-s", "dist", "-l", "3000"]
