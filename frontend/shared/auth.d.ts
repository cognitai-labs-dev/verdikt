// Augments nuxt-auth-utils session types. `user` is exposed to the client;
// `secure` (tokens) stays server-only.
declare module "#auth-utils" {
  interface User {
    name?: string
    email?: string
    sub?: string
  }

  interface SecureSessionData {
    idToken: string
    refreshToken?: string
    expiresAt: number
  }
}

export {}
