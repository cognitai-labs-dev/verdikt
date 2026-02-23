import zitadelAuth from "@/services/zitadelAuth"

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
  const baseUrl = import.meta.env.VITE_API_URL || "http://localhost:8000"

  const requestUrl = new URL(`${baseUrl}${pathname}${search}`)

  return requestUrl.toString()
}

const getHeaders = (headers?: HeadersInit, method?: string): HeadersInit => {
  const token = zitadelAuth.oidcAuth.accessToken
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
  const requestHeaders = getHeaders(options.headers, options.method)

  const requestInit: RequestInit = {
    ...options,
    headers: requestHeaders,
  }

  const response = await fetch(requestUrl, requestInit)
  const data = response.status === 204 ? undefined : await getBody<T>(response)

  return { status: response.status, data, headers: response.headers } as T
}
