// Gate every page on a server session. Unauthenticated users are sent to the
// server login route (external — it lives under server/, not in the SPA router).
export default defineNuxtRouteMiddleware(async (to) => {
  if (to.path.startsWith("/auth")) return

  const { loggedIn, fetch: fetchSession } = useUserSession()
  if (!loggedIn.value) await fetchSession()
  if (!loggedIn.value) {
    return navigateTo(`/auth/login?returnTo=${encodeURIComponent(to.fullPath)}`, {
      external: true,
    })
  }
})
