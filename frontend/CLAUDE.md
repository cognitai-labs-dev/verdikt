# CLAUDE.md

## Project Overview

Vue 3 + TypeScript SPA for LLM evaluation management. Tracks human and automated judgments on evaluation samples.

## Tech Stack

- **Framework**: Vue 3 with `<script setup lang="ts">` and Composition API
- **UI**: Vuetify 3 (Material Design)
- **Router**: Vue Router 4 (HTML5 history mode)
- **Build**: Vite 7, TypeScript ~5.9
- **Package Manager**: pnpm
- **API Client**: Auto-generated via Orval from OpenAPI spec

## Commands

- `pnpm dev` — Start dev server
- `pnpm build` — Type-check + production build
- `pnpm test:unit` — Run Vitest tests
- `pnpm lint` — Lint with eslint_d (auto-fix, cached)
- `pnpm format` — Format with Prettier
- `pnpm api:generate` — Regenerate API client from OpenAPI spec

## Pre-commit Hook

Runs `format`, `lint`, and `type-check` in sequence (via Husky).

## Code Style

- **Prettier**: No semicolons, double quotes, 100 char width
- **Components**: PascalCase `.vue` files, `<script setup lang="ts">`
- **Views**: Suffixed with `View.vue` (e.g., `EvaluationsView.vue`)
- **Functions**: camelCase
- **Types**: `*Schema` for models, `*Request`/`*Response` for API types

## Project Structure

```
src/
  api/
    fetcher.ts        # Custom fetch wrapper (uses VITE_API_URL or localhost:8000)
    generated.ts      # Orval-generated API client — do not edit manually
  components/         # Reusable Vue components
  views/              # Route-level page components
  utils/format.ts     # Date, cost, percentage formatting
  router.ts           # Route definitions
  main.ts             # App bootstrap with Vuetify
```

## Patterns

- Data fetching: direct async/await in `onMounted()` with local `ref()` state
- No centralized store — component-local state only
- Loading states via `v-progress-linear` with `v-if` guards
- Props via `defineProps<T>()`, emits via `defineEmits<T>()`
- API functions imported from `@/api/generated`
- `@` path alias resolves to `./src/`

## Don't

- Don't manually edit `src/api/generated.ts` — run `pnpm api:generate` instead
- Don't add semicolons (Prettier config: `semi: false`)
