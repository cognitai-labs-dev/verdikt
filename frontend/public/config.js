// Runtime configuration — loaded before the app bundle so a single prebuilt
// image can be configured per deployment via container env vars.
//
// The ${...} tokens are substituted by the container entrypoint (envsubst) at
// startup. In local dev this file is served verbatim with the tokens intact;
// src/config.ts detects the unsubstituted "${" tokens and falls back to Vite's
// import.meta.env (frontend/.env). So you never edit this file by hand.
window.__APP_CONFIG__ = {
  API_URL: "${API_URL}",
  OIDC_ISSUER: "${OIDC_ISSUER}",
  OIDC_CLIENT_ID: "${OIDC_CLIENT_ID}",
}
