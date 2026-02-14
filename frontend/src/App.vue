<script setup lang="ts">
import { useRouter, useRoute } from "vue-router"
import { useTheme } from "vuetify"
import { useActiveApp } from "@/stores/useActiveApp"

const router = useRouter()
const route = useRoute()
const { activeApp, clearApp } = useActiveApp()

function goHome() {
  clearApp()
  router.push("/")
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
    <v-app-bar color="primary" elevation="2">
      <v-btn icon="mdi-home" variant="text" @click="goHome" />
      <v-app-bar-title class="font-weight-bold">
        <template v-if="activeApp">
          <span style="cursor: pointer" @click="router.push(`/app/${activeApp.id}/detail`)">
            {{ activeApp.name }}
          </span>
          <span v-if="route.name && route.name !== 'Apps detail'" class="font-weight-regular">
            / {{ route.name }}
          </span>
        </template>
        <template v-else-if="route.name">
          {{ route.name }}
        </template>
      </v-app-bar-title>

      <template #append>
        <v-btn
          :icon="
            theme.global.current.value.dark ? 'mdi-white-balance-sunny' : 'mdi-moon-waning-crescent'
          "
          @click="toggleTheme"
          variant="text"
        />
      </template>
    </v-app-bar>

    <v-main>
      <div>
        <RouterView />
      </div>
    </v-main>
  </v-app>
</template>
