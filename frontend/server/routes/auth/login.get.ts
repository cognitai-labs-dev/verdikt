import { discover, pkceChallenge, randomString } from "../../utils/oidc"

// Start the OIDC authorization-code + PKCE flow. State / nonce / code_verifier
// are kept in short-lived httpOnly cookies and checked on the callback.
export default defineEventHandler(async (event) => {
  const cfg = useRuntimeConfig()
  const { authorization_endpoint } = await discover(cfg.oidcIssuer)

  const state = randomString()
  const nonce = randomString()
  const verifier = randomString(32)
  const redirectUri = `${getRequestURL(event).origin}/auth/callback`

  const cookieOpts = {
    httpOnly: true,
    secure: !import.meta.dev,
    sameSite: "lax" as const,
    maxAge: 600,
    path: "/",
  }
  setCookie(event, "oidc_state", state, cookieOpts)
  setCookie(event, "oidc_nonce", nonce, cookieOpts)
  setCookie(event, "oidc_verifier", verifier, cookieOpts)

  const returnTo = getQuery(event).returnTo
  if (typeof returnTo === "string") setCookie(event, "oidc_return", returnTo, cookieOpts)

  const url = new URL(authorization_endpoint)
  url.searchParams.set("client_id", cfg.oidcClientId)
  url.searchParams.set("redirect_uri", redirectUri)
  url.searchParams.set("response_type", "code")
  url.searchParams.set("scope", cfg.oidcScope)
  url.searchParams.set("state", state)
  url.searchParams.set("nonce", nonce)
  url.searchParams.set("code_challenge", pkceChallenge(verifier))
  url.searchParams.set("code_challenge_method", "S256")

  return sendRedirect(event, url.toString())
})
