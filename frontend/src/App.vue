<script setup lang="ts">
import { useRouter, useRoute } from "vue-router"
import { useTheme } from "vuetify"
import { useActiveApp } from "@/stores/useActiveApp"
import zitadelAuth from "@/services/zitadelAuth"

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
        <span
          v-if="zitadelAuth.oidcAuth.isAuthenticated"
          class="text-body-2 text-medium-emphasis mx-2"
        >
          {{ zitadelAuth.oidcAuth.userProfile.name ?? zitadelAuth.oidcAuth.userProfile.email }}
        </span>
        <v-btn
          icon="mdi-logout"
          variant="text"
          size="small"
          @click="zitadelAuth.oidcAuth.signOut()"
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
