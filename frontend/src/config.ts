// Single source of runtime config. Prefers values injected at container
// startup (window.__APP_CONFIG__ from public/config.js, substituted by
// envsubst), falling back to Vite build-time env (import.meta.env) for local
// dev. This is what lets one prebuilt image be reconfigured per deployment
// without a rebuild.

interface RuntimeConfig {
  API_URL?: string
  OIDC_ISSUER?: string
  OIDC_CLIENT_ID?: string
}

const runtime: RuntimeConfig =
  (window as unknown as { __APP_CONFIG__?: RuntimeConfig }).__APP_CONFIG__ ?? {}

// A value is "real" only if present and not a leftover ${TOKEN} placeholder
// (which is what dev sees, since envsubst never ran).
const pick = (runtimeValue: string | undefined, envValue: string | undefined): string => {
  if (runtimeValue && !runtimeValue.startsWith("${")) {
    return runtimeValue
  }
  return envValue ?? ""
}

export const config = {
  apiUrl: pick(runtime.API_URL, import.meta.env.VITE_API_URL) || "http://localhost:8000",
  oidcIssuer: pick(runtime.OIDC_ISSUER, import.meta.env.VITE_OIDC_ISSUER),
  oidcClientId: pick(runtime.OIDC_CLIENT_ID, import.meta.env.VITE_OIDC_CLIENT_ID),
}
