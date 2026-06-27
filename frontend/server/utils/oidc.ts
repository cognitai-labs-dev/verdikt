import { createHash, randomBytes } from "node:crypto"

// Provider-agnostic OIDC helpers for the BFF. Discovery resolves endpoints from
// any compliant issuer (GitLab, Google, Zitadel, ...), so the provider is pure
// config — no per-provider code.

export interface OidcDiscovery {
  authorization_endpoint: string
  token_endpoint: string
  end_session_endpoint?: string
}

export interface OidcTokens {
  idToken: string
  refreshToken?: string
  expiresAt: number // epoch ms
}

const discoveryCache = new Map<string, OidcDiscovery>()

export async function discover(issuer: string): Promise<OidcDiscovery> {
  const cached = discoveryCache.get(issuer)
  if (cached) return cached
  const url = `${issuer.replace(/\/$/, "")}/.well-known/openid-configuration`
  const doc = await $fetch<OidcDiscovery>(url)
  discoveryCache.set(issuer, doc)
  return doc
}

export function base64url(input: Buffer): string {
  return input.toString("base64").replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "")
}

export function randomString(bytes = 32): string {
  return base64url(randomBytes(bytes))
}

export function pkceChallenge(verifier: string): string {
  return base64url(createHash("sha256").update(verifier).digest())
}

// Decode a JWT payload WITHOUT verifying the signature. Safe here: the token
// comes straight from the IdP token endpoint over TLS, and Verdikt verifies the
// signature against the issuer's JWKS on every API call. We only need claims.
export function decodeJwtClaims(token: string): Record<string, unknown> {
  const payload = token.split(".")[1]
  if (!payload) return {}
  const json = Buffer.from(payload.replace(/-/g, "+").replace(/_/g, "/"), "base64").toString("utf8")
  return JSON.parse(json)
}

interface TokenResponse {
  id_token: string
  access_token?: string
  refresh_token?: string
  expires_in?: number
}

function toTokens(res: TokenResponse, previousRefresh?: string): OidcTokens {
  const ttl = res.expires_in ?? 3600
  return {
    idToken: res.id_token,
    refreshToken: res.refresh_token ?? previousRefresh,
    // refresh 30s early to avoid races
    expiresAt: Date.now() + (ttl - 30) * 1000,
  }
}

export async function exchangeCode(opts: {
  issuer: string
  clientId: string
  clientSecret: string
  code: string
  redirectUri: string
  codeVerifier: string
}): Promise<{ tokens: OidcTokens; claims: Record<string, unknown> }> {
  const { token_endpoint } = await discover(opts.issuer)
  const res = await $fetch<TokenResponse>(token_endpoint, {
    method: "POST",
    headers: { "content-type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({
      grant_type: "authorization_code",
      code: opts.code,
      redirect_uri: opts.redirectUri,
      client_id: opts.clientId,
      client_secret: opts.clientSecret,
      code_verifier: opts.codeVerifier,
    }),
  })
  return { tokens: toTokens(res), claims: decodeJwtClaims(res.id_token) }
}

export async function refreshTokens(opts: {
  issuer: string
  clientId: string
  clientSecret: string
  refreshToken: string
}): Promise<OidcTokens> {
  const { token_endpoint } = await discover(opts.issuer)
  const res = await $fetch<TokenResponse>(token_endpoint, {
    method: "POST",
    headers: { "content-type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({
      grant_type: "refresh_token",
      refresh_token: opts.refreshToken,
      client_id: opts.clientId,
      client_secret: opts.clientSecret,
    }),
  })
  return toTokens(res, opts.refreshToken)
}
