FROM node:22-slim AS builder
WORKDIR /app

# Vite bakes env vars into the bundle at build time — pass them as build args
ARG VITE_API_URL
ARG VITE_ZITADEL_ISSUER
ARG VITE_ZITADEL_CLIENT_ID
ARG VITE_ZITADEL_PROJECT_RESOURCE_ID

ENV VITE_API_URL=$VITE_API_URL
ENV VITE_ZITADEL_ISSUER=$VITE_ZITADEL_ISSUER
ENV VITE_ZITADEL_CLIENT_ID=$VITE_ZITADEL_CLIENT_ID
ENV VITE_ZITADEL_PROJECT_RESOURCE_ID=$VITE_ZITADEL_PROJECT_RESOURCE_ID

# Enable pnpm via corepack
RUN corepack enable && corepack prepare pnpm@latest --activate

# Copy package
COPY package.json pnpm-lock.yaml ./

# Install depedencies
RUN pnpm install --frozen-lockfile

# Copy code
COPY . .

# Build static files
RUN pnpm run build

FROM node:22-slim AS final

# Install serve
RUN npm install -g serve
WORKDIR /app/server
# Ensure safe permissions
RUN addgroup --system --gid 1001 appgroup && \
	adduser --system --uid 1001 --ingroup appgroup --home /app/server appuser

# Copy static files
COPY --from=builder /app/dist ./dist
RUN chown -R appuser:appgroup ./dist
USER appuser
EXPOSE 3000

# Run server
CMD ["serve", "-s", "dist", "-l", "3000"]

