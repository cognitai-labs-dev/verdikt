<script setup lang="ts">
import { onMounted, ref } from "vue"
import { getApps, deleteApp, type AppSchema } from "@/api/generated"
import { useRouter } from "vue-router"
import { formatDate } from "@/utils/format"
import { useActiveApp } from "@/stores/useActiveApp"
import zitadelAuth from "@/services/zitadelAuth"

const router = useRouter()
const { setApp } = useActiveApp()
const apps = ref<AppSchema[]>([])
const loading = ref(true)
const deleteDialog = ref(false)
const appToDelete = ref<AppSchema | null>(null)

const token = zitadelAuth.oidcAuth.accessToken

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
    {{ token }}
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
    </v-row>

    <v-alert v-if="!loading && apps.length === 0" type="info" variant="tonal">
      No apps found.
    </v-alert>

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
  </v-container>
</template>
