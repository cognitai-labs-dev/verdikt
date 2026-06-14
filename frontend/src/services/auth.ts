import { User } from "oidc-client"
import { createOidcAuth, SignInType, type OidcAuth } from "vue-oidc-client/vue3"

// Generic OIDC — works with any compliant provider (Google, Zitadel,
// Keycloak, Okta, Azure AD, ...). Configured per deployment via env.
// Redirect URI to register in the IdP: {origin}/auth/signinwin/oidc
const appUrl = `${window.location.origin}/`

const oidcAuth: OidcAuth = createOidcAuth("oidc", SignInType.Window, appUrl, {
  authority: import.meta.env.VITE_OIDC_ISSUER,
  client_id: import.meta.env.VITE_OIDC_CLIENT_ID,
  response_type: "code",
  scope: "openid email profile",
})

// handle events
oidcAuth.events.addAccessTokenExpiring(function () {
  console.log("access token expiring")
})

oidcAuth.events.addAccessTokenExpired(function () {
  console.log("access token expired")
})

oidcAuth.events.addSilentRenewError(function (err: Error) {
  console.error("silent renew error", err)
})

oidcAuth.events.addUserLoaded(function (user: User) {
  console.log("user loaded", user)
})

oidcAuth.events.addUserUnloaded(function () {
  console.log("user unloaded")
})

oidcAuth.events.addUserSignedOut(function () {
  console.log("user signed out")
})

oidcAuth.events.addUserSessionChanged(function () {
  console.log("user session changed")
})

export default { oidcAuth }
