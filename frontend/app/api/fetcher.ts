// All API calls go to the same-origin BFF (Nitro) under /api, carrying only the
// httpOnly session cookie. The Nitro proxy (server/api/v1/[...path].ts) attaches
// the user's id_token as Bearer to the real Verdikt call — the token never
// reaches the browser, so there is no auth logic here.

const getBody = <T>(c: Response | Request): Promise<T> => {
  const contentType = c.headers.get("content-type")

  if (contentType && contentType.includes("application/json")) {
    return c.json()
  }

  return c.text() as Promise<T>
}

const getUrl = (contextUrl: string): string => {
  // The generated client builds absolute URLs from its baseUrl; we only keep the
  // path + query and route them through the same-origin BFF (/api/v1/...).
  const url = new URL(contextUrl)
  return `/api${url.pathname}${url.search}`
}

export const customFetch = async <T>(url: string, options: RequestInit): Promise<T> => {
  const requestUrl = getUrl(url)

  const headers: HeadersInit = { ...options.headers }
  const method = options.method
  if (method && ["POST", "PUT", "PATCH"].includes(method.toUpperCase())) {
    ;(headers as Record<string, string>)["Content-Type"] = "application/json"
  }

  const response = await fetch(requestUrl, {
    ...options,
    headers,
    credentials: "include",
  })
  const data = response.status === 204 ? undefined : await getBody<T>(response)

  return { status: response.status, data, headers: response.headers } as T
}
