<script setup lang="ts">
import { computed, onMounted, ref } from "vue"
import {
  getMe,
  getApps,
  getMachineClients,
  postMachineClient,
  revokeMachineClient,
  unrevokeMachineClient,
  bindMachineClientApp,
  unbindMachineClientApp,
  type MachineClientResponse,
  type CreatedMachineClientResponse,
  type AppSchema,
} from "@/api/generated"
import { formatDate } from "@/utils/format"

definePageMeta({ name: "Admin" })

const loading = ref(true)
const authorized = ref(false)
const clients = ref<MachineClientResponse[]>([])
const apps = ref<AppSchema[]>([])

// Create dialog
const createDialog = ref(false)
const newName = ref("")
const newIsAdmin = ref(false)
const newAppSlugs = ref<string[]>([])
const creating = ref(false)
const createError = ref<string | null>(null)
const createdSecret = ref<CreatedMachineClientResponse | null>(null)
const idCopied = ref(false)
const secretCopied = ref(false)

const appSlugItems = computed(() =>
  apps.value.map((a) => ({ title: `${a.name} (${a.slug})`, value: a.slug })),
)

function appsForSelect(client: MachineClientResponse) {
  const bound = new Set((client.apps ?? []).map((a) => a.id))
  return apps.value
    .filter((a) => !bound.has(a.id))
    .map((a) => ({ title: `${a.name} (${a.slug})`, value: a.id }))
}

async function refreshClients() {
  const res = await getMachineClients()
  if (res.status === 200) {
    clients.value = res.data
  }
}

function replaceClient(updated: MachineClientResponse) {
  clients.value = clients.value.map((c) => (c.client_id === updated.client_id ? updated : c))
}

onMounted(async () => {
  const meRes = await getMe()
  authorized.value = meRes.status === 200 && meRes.data.is_admin
  if (authorized.value) {
    await Promise.all([refreshClients(), loadApps()])
  }
  loading.value = false
})

async function loadApps() {
  const res = await getApps()
  if (res.status === 200) {
    apps.value = res.data
  }
}

function openCreateDialog() {
  newName.value = ""
  newIsAdmin.value = false
  newAppSlugs.value = []
  createError.value = null
  createdSecret.value = null
  idCopied.value = false
  secretCopied.value = false
  createDialog.value = true
}

async function handleCreate() {
  if (!newName.value.trim()) return
  creating.value = true
  createError.value = null
  const res = await postMachineClient({
    name: newName.value.trim(),
    is_admin: newIsAdmin.value,
    app_slugs: newIsAdmin.value ? [] : newAppSlugs.value,
  })
  creating.value = false
  if (res.status === 201) {
    createdSecret.value = res.data
    await refreshClients()
  } else {
    createError.value =
      res.status === 400 && "detail" in res.data
        ? res.data.detail
        : "Failed to create client. Please try again."
  }
}

async function copyId() {
  if (!createdSecret.value) return
  await navigator.clipboard.writeText(createdSecret.value.client_id)
  idCopied.value = true
}

async function copySecret() {
  if (!createdSecret.value) return
  await navigator.clipboard.writeText(createdSecret.value.client_secret)
  secretCopied.value = true
}

async function toggleRevoke(client: MachineClientResponse) {
  const res = client.revoked
    ? await unrevokeMachineClient(client.client_id)
    : await revokeMachineClient(client.client_id)
  if (res.status === 200) {
    replaceClient(res.data)
  }
}

async function addApp(client: MachineClientResponse, appId: number) {
  const res = await bindMachineClientApp(client.client_id, { app_id: appId })
  if (res.status === 201) {
    replaceClient(res.data)
  }
}

async function removeApp(client: MachineClientResponse, appId: number) {
  const res = await unbindMachineClientApp(client.client_id, appId)
  if (res.status === 200) {
    replaceClient(res.data)
  }
}
</script>

<template>
  <v-container fluid class="pa-6">
    <div class="d-flex align-center mb-6">
      <h1 class="text-h5 font-weight-bold">Machine Accounts</h1>
      <v-spacer />
      <v-btn v-if="authorized" color="primary" variant="flat" @click="openCreateDialog">
        <v-icon start>mdi-plus</v-icon>
        New client
      </v-btn>
    </div>

    <v-progress-linear v-if="loading" indeterminate />

    <v-alert v-else-if="!authorized" type="error" variant="tonal">
      You are not authorized to view this page.
    </v-alert>

    <v-table v-else>
      <thead>
        <tr>
          <th class="text-left">Name</th>
          <th class="text-left">Client ID</th>
          <th class="text-left">Status</th>
          <th class="text-left">Created</th>
          <th class="text-left">Apps</th>
          <th class="text-right">Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="client in clients" :key="client.client_id">
          <td>{{ client.name }}</td>
          <td>
            <code class="text-caption">{{ client.client_id }}</code>
          </td>
          <td>
            <v-chip v-if="client.is_admin" size="x-small" color="primary" class="mr-1">
              admin
            </v-chip>
            <v-chip v-if="client.revoked" size="x-small" color="error">revoked</v-chip>
            <v-chip v-else size="x-small" color="success">active</v-chip>
          </td>
          <td class="text-caption">{{ formatDate(client.created_at) }}</td>
          <td>
            <template v-if="client.is_admin">
              <span class="text-caption text-medium-emphasis">all apps</span>
            </template>
            <template v-else>
              <div class="d-flex flex-wrap align-center ga-1">
                <v-chip
                  v-for="app in client.apps ?? []"
                  :key="app.id"
                  size="small"
                  closable
                  @click:close="removeApp(client, app.id)"
                >
                  {{ app.slug }}
                </v-chip>

                <v-menu v-if="appsForSelect(client).length">
                  <template #activator="{ props }">
                    <v-chip v-bind="props" size="small" variant="outlined" prepend-icon="mdi-plus">
                      add app
                    </v-chip>
                  </template>
                  <v-list density="compact">
                    <v-list-item
                      v-for="item in appsForSelect(client)"
                      :key="item.value"
                      :title="item.title"
                      @click="addApp(client, item.value)"
                    />
                  </v-list>
                </v-menu>

                <span
                  v-else-if="!(client.apps ?? []).length"
                  class="text-caption text-medium-emphasis"
                >
                  no apps
                </span>
              </div>
            </template>
          </td>
          <td class="text-right">
            <v-btn
              size="small"
              variant="tonal"
              :color="client.revoked ? 'success' : 'error'"
              @click="toggleRevoke(client)"
            >
              {{ client.revoked ? "Unrevoke" : "Revoke" }}
            </v-btn>
          </td>
        </tr>
      </tbody>
    </v-table>

    <v-dialog v-model="createDialog" max-width="480">
      <v-card>
        <v-card-title>{{
          createdSecret ? "Client created" : "Create machine client"
        }}</v-card-title>

        <v-card-text v-if="!createdSecret">
          <v-text-field
            v-model="newName"
            label="Name"
            autofocus
            :error-messages="createError ? [createError] : []"
          />
          <v-checkbox
            v-model="newIsAdmin"
            label="Admin (access to every app)"
            hide-details
            density="compact"
          />
          <v-select
            v-if="!newIsAdmin"
            v-model="newAppSlugs"
            :items="appSlugItems"
            label="Apps"
            multiple
            chips
            class="mt-2"
          />
        </v-card-text>

        <v-card-text v-else>
          <v-alert type="warning" variant="tonal" class="mb-3">
            Store these now — the secret is shown once and cannot be recovered.
          </v-alert>
          <div class="text-caption text-medium-emphasis mb-1">Client ID</div>
          <div class="credential-box d-flex align-center mb-4">
            <code class="flex-grow-1 text-truncate">{{ createdSecret.client_id }}</code>
            <v-btn
              :icon="idCopied ? 'mdi-check' : 'mdi-content-copy'"
              :color="idCopied ? 'success' : undefined"
              size="small"
              variant="text"
              density="comfortable"
              @click="copyId"
            />
          </div>

          <div class="text-caption text-medium-emphasis mb-1">Client secret</div>
          <div class="credential-box d-flex align-center">
            <code class="flex-grow-1 text-truncate">{{ createdSecret.client_secret }}</code>
            <v-btn
              :icon="secretCopied ? 'mdi-check' : 'mdi-content-copy'"
              :color="secretCopied ? 'success' : undefined"
              size="small"
              variant="text"
              density="comfortable"
              @click="copySecret"
            />
          </div>
        </v-card-text>

        <v-card-actions>
          <v-spacer />
          <template v-if="!createdSecret">
            <v-btn variant="text" @click="createDialog = false">Cancel</v-btn>
            <v-btn
              color="primary"
              variant="flat"
              :loading="creating"
              :disabled="!newName.trim()"
              @click="handleCreate"
            >
              Create
            </v-btn>
          </template>
          <v-btn v-else color="primary" variant="flat" @click="createDialog = false">Done</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<style scoped>
.credential-box {
  gap: 8px;
  padding: 6px 6px 6px 12px;
  border-radius: 8px;
  background: rgba(var(--v-theme-on-surface), 0.04);
  border: 1px solid rgba(var(--v-theme-on-surface), 0.12);
}
.credential-box code {
  font-family: monospace;
  font-size: 0.875rem;
  overflow-x: auto;
}
</style>
