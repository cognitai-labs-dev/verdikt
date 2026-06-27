import { globalIgnores } from "eslint/config"
import { defineConfigWithVueTs, vueTsConfigs } from "@vue/eslint-config-typescript"
import pluginVue from "eslint-plugin-vue"
import eslintConfigPrettier from "eslint-config-prettier"

export default defineConfigWithVueTs(
  {
    name: "app/files-to-lint",
    files: ["**/*.{vue,ts,mts,tsx}"],
  },

  globalIgnores([
    "**/dist/**",
    "**/.nuxt/**",
    "**/.output/**",
    "**/node_modules/**",
    "app/api/generated.ts",
  ]),

  ...pluginVue.configs["flat/essential"],
  vueTsConfigs.recommended,

  {
    rules: {
      "vue/valid-v-slot": ["error", { allowModifiers: true }],
    },
  },

  {
    // Nuxt pages/layouts are file-routed and single-word by design.
    files: ["app/pages/**/*.vue", "app/layouts/**/*.vue", "app/app.vue"],
    rules: { "vue/multi-word-component-names": "off" },
  },

  eslintConfigPrettier,
)
