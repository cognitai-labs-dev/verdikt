import "unfonts.css"
import "@mdi/font/css/materialdesignicons.css"
import router from "./router"
import { createApp } from "vue"

import "vuetify/styles"
import { createVuetify } from "vuetify"
import * as components from "vuetify/components"
import * as directives from "vuetify/directives"

import App from "./App.vue"

const vuetify = createVuetify({
  components,
  directives,
  theme: {
    defaultTheme: localStorage.getItem("theme") || "light",
    themes: {
      light: {
        colors: {
          primary: "#1565C0",
          secondary: "#546E7A",
          surface: "#FFFFFF",
          background: "#F5F7FA",
        },
      },
      dark: {
        colors: {
          primary: "#42A5F5",
          secondary: "#90A4AE",
          surface: "#1E1E1E",
          background: "#121212",
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

createApp(App).use(router).use(vuetify).mount("#app")
