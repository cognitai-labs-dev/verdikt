import { config } from "@/config"
import auth from "@/services/auth"

const getBody = <T>(c: Response | Request): Promise<T> => {
  const contentType = c.headers.get("content-type")

  if (contentType && contentType.includes("application/json")) {
    return c.json()
  }

  return c.text() as Promise<T>
}

const getUrl = (contextUrl: string): string => {
  const url = new URL(contextUrl)
  const pathname = url.pathname
  const search = url.search
  const baseUrl = config.apiUrl

  const requestUrl = new URL(`${baseUrl}${pathname}${search}`)

  return requestUrl.toString()
}

const getHeaders = async (headers?: HeadersInit, method?: string): Promise<HeadersInit> => {
  // Send the id_token (a JWT) rather than the access token. Some providers
  // (e.g. Google) issue opaque, non-verifiable access tokens; the id_token is
  // always a JWT the backend can verify against the issuer's JWKS.
  const user = await auth.oidcAuth.mgr.getUser()
  const token = user?.id_token
  const baseHeaders: HeadersInit = {
    ...headers,
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  }

  // Only set Content-Type for requests with body
  if (method && ["POST", "PUT", "PATCH"].includes(method.toUpperCase())) {
    return {
      ...baseHeaders,
      "Content-Type": "application/json",
    }
  }

  return baseHeaders
}

export const customFetch = async <T>(url: string, options: RequestInit): Promise<T> => {
  const requestUrl = getUrl(url)
  const requestHeaders = await getHeaders(options.headers, options.method)

  const requestInit: RequestInit = {
    ...options,
    headers: requestHeaders,
  }

  const response = await fetch(requestUrl, requestInit)
  const data = response.status === 204 ? undefined : await getBody<T>(response)

  return { status: response.status, data, headers: response.headers } as T
}
