import { exchangeCode } from "../../utils/oidc"

// OIDC redirect target. Validates state, exchanges the code for tokens, stores
// the id_token/refresh_token in the sealed (server-only) session, redirects back.
export default defineEventHandler(async (event) => {
  const cfg = useRuntimeConfig()
  const q = getQuery(event)

  const state = getCookie(event, "oidc_state")
  const nonce = getCookie(event, "oidc_nonce")
  const verifier = getCookie(event, "oidc_verifier")
  for (const name of ["oidc_state", "oidc_nonce", "oidc_verifier"]) deleteCookie(event, name)

  if (!q.code || !q.state || q.state !== state || !verifier) {
    throw createError({ statusCode: 400, statusMessage: "Invalid OIDC callback" })
  }

  const redirectUri = `${getRequestURL(event).origin}/auth/callback`
  const { tokens, claims } = await exchangeCode({
    issuer: cfg.oidcIssuer,
    clientId: cfg.oidcClientId,
    clientSecret: cfg.oidcClientSecret,
    code: String(q.code),
    redirectUri,
    codeVerifier: verifier,
  })

  if (nonce && claims.nonce && claims.nonce !== nonce) {
    throw createError({ statusCode: 400, statusMessage: "OIDC nonce mismatch" })
  }

  await setUserSession(event, {
    user: {
      name: claims.name as string | undefined,
      email: claims.email as string | undefined,
      sub: claims.sub as string | undefined,
    },
    secure: {
      idToken: tokens.idToken,
      refreshToken: tokens.refreshToken,
      expiresAt: tokens.expiresAt,
    },
  })

  const returnTo = getCookie(event, "oidc_return") || "/"
  deleteCookie(event, "oidc_return")
  return sendRedirect(event, returnTo)
})
