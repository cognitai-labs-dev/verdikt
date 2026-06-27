<script setup lang="ts">
import { useTheme } from "vuetify"
import { useActiveApp } from "@/stores/useActiveApp"

const router = useRouter()
const route = useRoute()
const { activeApp, clearApp } = useActiveApp()
// Session lives in an httpOnly cookie; the browser only sees the profile.
const { user } = useUserSession()

function goHome() {
  clearApp()
  router.push("/")
}

function logout() {
  // Server route clears the sealed session, then redirects.
  navigateTo("/auth/logout", { external: true })
}

const theme = useTheme()

const saved = localStorage.getItem("theme")
theme.global.name.value =
  saved ?? (window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light")

function toggleTheme() {
  const next = theme.global.current.value.dark ? "light" : "dark"
  theme.global.name.value = next
  localStorage.setItem("theme", next)
}
</script>

<template>
  <v-app>
    <v-app-bar color="surface" elevation="0" border="b">
      <!-- Logo / home -->
      <div class="d-flex align-center pl-2" style="cursor: pointer" @click="goHome">
        <v-icon icon="mdi-scale-balance" color="primary" size="22" class="mr-1" />
        <span class="text-body-1 font-weight-bold" style="letter-spacing: 0.04em">Verdikt</span>
      </div>

      <!-- Breadcrumb -->
      <v-app-bar-title class="ml-4">
        <template v-if="activeApp">
          <span
            class="text-body-2 text-medium-emphasis"
            style="cursor: pointer"
            @click="router.push(`/app/${activeApp.id}/detail`)"
          >
            {{ activeApp.name }}
          </span>
          <span v-if="route.name && route.name !== 'Apps detail'" class="text-body-2 text-disabled">
            &nbsp;/&nbsp;{{ route.name }}
          </span>
        </template>
        <template v-else-if="route.name">
          <span class="text-body-2 text-medium-emphasis">{{ route.name }}</span>
        </template>
      </v-app-bar-title>

      <template #append>
        <v-btn
          :icon="
            theme.global.current.value.dark ? 'mdi-white-balance-sunny' : 'mdi-moon-waning-crescent'
          "
          @click="toggleTheme"
          variant="text"
          size="small"
        />
        <span v-if="user" class="text-body-2 text-medium-emphasis mx-2">
          {{ user.name ?? user.email }}
        </span>
        <v-btn icon="mdi-logout" variant="text" size="small" @click="logout" />
      </template>
    </v-app-bar>

    <v-main>
      <div>
        <slot />
      </div>
    </v-main>
  </v-app>
</template>
