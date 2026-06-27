import { defineConfig } from "orval"

export default defineConfig({
  api: {
    input: "http://127.0.0.1:8000/openapi.json",
    output: {
      target: "./app/api/generated.ts",
      client: "fetch",
      mode: "single",
      // Only the path+query is used; customFetch routes calls through the
      // same-origin BFF (/api/...). See app/api/fetcher.ts.
      baseUrl: "http://127.0.0.1:8000",
      override: {
        mutator: {
          path: "./app/api/fetcher.ts",
          name: "customFetch",
        },
      },
    },
  },
})
