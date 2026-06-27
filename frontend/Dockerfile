FROM node:22-slim AS builder
WORKDIR /app

# Nuxt reads config from NUXT_* env at SERVER startup (see nuxt.config.ts
# runtimeConfig), so the image is built once and reconfigured per deployment —
# no build args, no envsubst.
RUN corepack enable && corepack prepare pnpm@11.5.2 --activate

# Copy everything before install so the `nuxt prepare` postinstall has the
# project (config + app/) available.
COPY . .
RUN pnpm install --frozen-lockfile
RUN pnpm run build

FROM node:22-slim AS final
WORKDIR /app

RUN addgroup --system --gid 1001 appgroup && \
	adduser --system --uid 1001 --ingroup appgroup --home /app appuser

# Self-contained Nitro server bundle (UI + /api BFF routes).
COPY --from=builder --chown=appuser:appgroup /app/.output ./.output

USER appuser
ENV HOST=0.0.0.0 \
	PORT=3000 \
	NODE_ENV=production
EXPOSE 3000

CMD ["node", ".output/server/index.mjs"]
