import "unfonts.css"
import "@mdi/font/css/materialdesignicons.css"
import router from "./router"
import { createApp } from "vue"

import "vuetify/styles"
import { createVuetify } from "vuetify"
import * as components from "vuetify/components"
import * as directives from "vuetify/directives"

import App from "./App.vue"
import zitadelAuth from "./services/zitadelAuth"

const vuetify = createVuetify({
  components,
  directives,
  theme: {
    defaultTheme: localStorage.getItem("theme") || "light",
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
    VCard: {
      elevation: 2,
      rounded: "lg",
    },
    VBtn: {
      rounded: "lg",
    },
    VDataTable: {
      hover: true,
    },
    VChip: {
      rounded: "lg",
    },
  },
})

zitadelAuth.oidcAuth.startup().then((ok) => {
  if (ok) {
    const app = createApp(App)
    app.config.globalProperties.$zitadel = zitadelAuth
    app.use(router).use(vuetify).mount("#app")
  } else {
    console.error("Zitadel auth startup failed")
  }
})
