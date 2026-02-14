import { defineConfig } from "orval"

export default defineConfig({
  api: {
    input: "http://127.0.0.1:8000/openapi.json",
    output: {
      target: "./src/api/generated.ts",
      client: "fetch",
      mode: "single",
      // gets overwritten at runtime in fetcher.ts
      baseUrl: "http://127.0.0.1:8000",
      override: {
        mutator: {
          path: "./src/api/fetcher.ts",
          name: "customFetch",
        },
      },
    },
  },
})
