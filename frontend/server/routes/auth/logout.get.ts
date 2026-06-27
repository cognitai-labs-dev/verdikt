import { discover } from "../../utils/oidc"

// Clear the sealed session, then best-effort end the IdP session.
export default defineEventHandler(async (event) => {
  const cfg = useRuntimeConfig()
  await clearUserSession(event)

  try {
    const { end_session_endpoint } = await discover(cfg.oidcIssuer)
    if (end_session_endpoint) {
      const url = new URL(end_session_endpoint)
      url.searchParams.set("post_logout_redirect_uri", `${getRequestURL(event).origin}/`)
      url.searchParams.set("client_id", cfg.oidcClientId)
      return sendRedirect(event, url.toString())
    }
  } catch {
    // discovery unavailable — fall through to local redirect
  }
  return sendRedirect(event, "/")
})
