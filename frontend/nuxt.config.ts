// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  // SPA mode: the browser renders (Vuetify stays client-only), but Nitro still
  // runs as a Node server so the BFF routes under server/ work. Tokens never
  // reach the browser — see server/api/v1/[...path].ts.
  ssr: false,

  compatibilityDate: "2025-01-01",

  // Dev server on 5173 to avoid the local Zitadel login UI (docker, :3000).
  // Production runs the Nitro node server on :3000 (PORT env).
  devServer: { port: 5173 },

  modules: ["vuetify-nuxt-module", "nuxt-auth-utils"],

  css: ["@mdi/font/css/materialdesignicons.css"],

  runtimeConfig: {
    // Server-only (mapped from NUXT_* env at server startup):
    //   oidcIssuer       <- NUXT_OIDC_ISSUER
    //   oidcClientId     <- NUXT_OIDC_CLIENT_ID
    //   oidcClientSecret <- NUXT_OIDC_CLIENT_SECRET
    //   verdiktApiUrl    <- NUXT_VERDIKT_API_URL
    // Session password    <- NUXT_SESSION_PASSWORD (read by nuxt-auth-utils)
    oidcIssuer: "",
    oidcClientId: "",
    oidcClientSecret: "",
    oidcScope: "openid email profile",
    verdiktApiUrl: "http://localhost:8000",
    // Nothing secret needs to reach the client anymore — login is server-side.
    public: {},
  },

  vuetify: {
    vuetifyOptions: {
      theme: {
        defaultTheme: "light",
        themes: {
          light: {
            colors: {
              primary: "#2563EB",
              secondary: "#64748B",
              surface: "#FFFFFF",
              background: "#F8FAFC",
            },
          },
          dark: {
            colors: {
              primary: "#3B82F6",
              secondary: "#94A3B8",
              surface: "#1C1C1E",
              background: "#111113",
            },
          },
        },
      },
      defaults: {
        VCard: { elevation: 2, rounded: "lg" },
        VBtn: { rounded: "lg" },
        VDataTable: { hover: true },
        VChip: { rounded: "lg" },
      },
    },
  },
})
