<script setup lang="ts">
import { onMounted, ref } from "vue"
import { getApps, deleteApp, postApp, type AppSchema } from "@/api/generated"
import { useRouter } from "vue-router"
import { formatDate } from "@/utils/format"
import { useActiveApp } from "@/stores/useActiveApp"

const router = useRouter()
const { setApp } = useActiveApp()
const apps = ref<AppSchema[]>([])
const loading = ref(true)
const deleteDialog = ref(false)
const appToDelete = ref<AppSchema | null>(null)
const createDialog = ref(false)
const newAppName = ref("")
const newAppSlug = ref("")
const creating = ref(false)
const createError = ref<string | null>(null)

function toSlug(name: string): string {
  return name
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "")
}

const confirmDelete = (app: AppSchema) => {
  appToDelete.value = app
  deleteDialog.value = true
}

const handleDelete = async () => {
  if (!appToDelete.value) return
  const res = await deleteApp(appToDelete.value.id)
  if (res.status === 204) {
    apps.value = apps.value.filter((a) => a.id !== appToDelete.value!.id)
  }
  deleteDialog.value = false
  appToDelete.value = null
}

onMounted(async () => {
  const res = await getApps()
  if (res.status === 200) {
    apps.value = res.data
  }
  loading.value = false
})

const openCreateDialog = () => {
  newAppName.value = ""
  newAppSlug.value = ""
  createError.value = null
  createDialog.value = true
}

const handleCreate = async () => {
  if (!newAppName.value.trim() || !newAppSlug.value.trim()) return
  creating.value = true
  createError.value = null
  const res = await postApp({ name: newAppName.value.trim(), slug: newAppSlug.value.trim() })
  creating.value = false
  if (res.status === 201) {
    const appsRes = await getApps()
    if (appsRes.status === 200) {
      apps.value = appsRes.data
    }
    createDialog.value = false
  } else {
    createError.value = "Failed to create app. Please try again."
  }
}

const navigateToDetail = (app: AppSchema) => {
  setApp(app)
  router.push(`/app/${app.id}/detail`)
}

const navigateToEvaluations = (app: AppSchema) => {
  setApp(app)
  router.push(`/app/${app.id}/evaluations`)
}
</script>

<template>
  <v-container fluid class="pa-6">
    <div class="mb-6">
      <h1 class="text-h5 font-weight-bold">Your Apps</h1>
    </div>

    <v-progress-linear v-if="loading" indeterminate />

    <v-row v-if="!loading">
      <v-col v-for="app in apps" :key="app.id" cols="12" sm="6" md="4" lg="3">
        <v-card rounded="lg" class="pa-4">
          <div class="d-flex align-center ga-3 mb-3">
            <v-avatar color="primary" variant="tonal" rounded="lg" size="40">
              <v-icon>mdi-application-outline</v-icon>
            </v-avatar>
            <div>
              <div class="text-body-1 font-weight-medium">{{ app.name }}</div>
              <div class="text-caption text-medium-emphasis">
                Created {{ formatDate(app.created_at) }}
              </div>
            </div>
          </div>
          <div class="d-flex ga-2">
            <v-btn size="small" variant="tonal" color="primary" @click="navigateToDetail(app)">
              <v-icon start>mdi-information-outline</v-icon>
              Detail
            </v-btn>
            <v-btn size="small" variant="tonal" color="primary" @click="navigateToEvaluations(app)">
              <v-icon start>mdi-clipboard-list-outline</v-icon>
              Evaluations
            </v-btn>
            <v-spacer />
            <v-btn size="small" variant="tonal" color="error" @click="confirmDelete(app)">
              <v-icon>mdi-delete-outline</v-icon>
            </v-btn>
          </div>
        </v-card>
      </v-col>

      <!-- New app tile -->
      <v-col cols="12" sm="6" md="4" lg="3">
        <v-card
          rounded="lg"
          class="pa-4 d-flex align-center justify-center new-app-tile"
          style="min-height: 110px; cursor: pointer"
          variant="outlined"
          @click="openCreateDialog"
        >
          <v-icon icon="mdi-plus" size="36" color="medium-emphasis" />
        </v-card>
      </v-col>
    </v-row>

    <v-dialog v-model="deleteDialog" max-width="400">
      <v-card>
        <v-card-title>Delete App</v-card-title>
        <v-card-text>
          Are you sure you want to delete <strong>{{ appToDelete?.name }}</strong
          >?
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="deleteDialog = false">Cancel</v-btn>
          <v-btn color="error" variant="flat" @click="handleDelete">Delete</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog v-model="createDialog" max-width="400">
      <v-card>
        <v-card-title>Create App</v-card-title>
        <v-card-text>
          <v-text-field
            v-model="newAppName"
            label="App name"
            autofocus
            :error-messages="createError ? [createError] : []"
            @update:model-value="newAppSlug = toSlug(newAppName)"
            @keyup.enter="handleCreate"
          />
          <v-text-field
            v-model="newAppSlug"
            label="Slug"
            :hint="'URL-friendly identifier, e.g. my-app'"
            persistent-hint
            class="mt-2"
            @keyup.enter="handleCreate"
          />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="createDialog = false">Cancel</v-btn>
          <v-btn
            color="primary"
            variant="flat"
            :loading="creating"
            :disabled="!newAppName.trim() || !newAppSlug.trim()"
            @click="handleCreate"
          >
            Create
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<style scoped>
.new-app-tile {
  transition:
    border-color 0.15s,
    background 0.15s;
}
.new-app-tile:hover {
  border-color: rgb(var(--v-theme-primary)) !important;
  background: rgba(var(--v-theme-primary), 0.04) !important;
}
.new-app-tile:hover .v-icon {
  color: rgb(var(--v-theme-primary)) !important;
}
</style>
