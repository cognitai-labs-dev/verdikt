import { refreshTokens } from "../../utils/oidc"

// BFF core: the browser calls same-origin /api/v1/* with only the session
// cookie. This forwards to Verdikt with the user's id_token as Bearer, so the
// token never reaches the browser. Refreshes the token when it has expired.
export default defineEventHandler(async (event) => {
  const cfg = useRuntimeConfig()
  const session = await getUserSession(event)
  const secure = session.secure

  if (!secure?.idToken) {
    throw createError({ statusCode: 401, statusMessage: "Unauthenticated" })
  }

  let idToken = secure.idToken
  if (secure.expiresAt && Date.now() >= secure.expiresAt && secure.refreshToken) {
    const refreshed = await refreshTokens({
      issuer: cfg.oidcIssuer,
      clientId: cfg.oidcClientId,
      clientSecret: cfg.oidcClientSecret,
      refreshToken: secure.refreshToken,
    })
    idToken = refreshed.idToken
    await setUserSession(event, { ...session, secure: { ...secure, ...refreshed } })
  }

  const path = (event.context.params?.path as string | undefined) ?? ""
  const search = getRequestURL(event).search
  const target = `${cfg.verdiktApiUrl.replace(/\/$/, "")}/v1/${path}${search}`

  const method = event.method
  const headers: Record<string, string> = { Authorization: `Bearer ${idToken}` }
  const contentType = getRequestHeader(event, "content-type")
  if (contentType) headers["content-type"] = contentType

  const body = method === "GET" || method === "HEAD" ? undefined : await readRawBody(event)

  const res = await fetch(target, { method, headers, body })

  setResponseStatus(event, res.status)
  const resContentType = res.headers.get("content-type")
  if (resContentType) setResponseHeader(event, "content-type", resContentType)
  return Buffer.from(await res.arrayBuffer())
})
