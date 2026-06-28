<script setup lang="ts">
import { onMounted, ref } from "vue"
import {
  getAppMachineClients,
  postAppMachineClient,
  deleteAppMachineClient,
  type AppMachineClientResponse,
  type CreatedAppMachineClientResponse,
} from "@/api/generated"
import { formatDate } from "@/utils/format"

const props = defineProps<{ appId: number }>()

const clients = ref<AppMachineClientResponse[]>([])
const loading = ref(true)

const createDialog = ref(false)
const newName = ref("")
const creating = ref(false)
const createError = ref<string | null>(null)
const created = ref<CreatedAppMachineClientResponse | null>(null)
const idCopied = ref(false)
const secretCopied = ref(false)

async function refresh() {
  const res = await getAppMachineClients(props.appId)
  if (res.status === 200) {
    clients.value = res.data
  }
}

onMounted(async () => {
  await refresh()
  loading.value = false
})

function openCreate() {
  newName.value = ""
  createError.value = null
  created.value = null
  idCopied.value = false
  secretCopied.value = false
  createDialog.value = true
}

async function handleCreate() {
  if (!newName.value.trim()) return
  creating.value = true
  createError.value = null
  const res = await postAppMachineClient(props.appId, { name: newName.value.trim() })
  creating.value = false
  if (res.status === 201) {
    created.value = res.data
    await refresh()
  } else {
    createError.value = "Failed to create client. Please try again."
  }
}

async function copyId() {
  if (!created.value) return
  await navigator.clipboard.writeText(created.value.client_id)
  idCopied.value = true
}

async function copySecret() {
  if (!created.value) return
  await navigator.clipboard.writeText(created.value.client_secret)
  secretCopied.value = true
}

async function removeClient(client: AppMachineClientResponse) {
  const res = await deleteAppMachineClient(props.appId, client.client_id)
  if (res.status === 204) {
    clients.value = clients.value.filter((c) => c.client_id !== client.client_id)
  }
}
</script>

<template>
  <v-card rounded="lg">
    <v-card-title class="d-flex align-center">
      <v-icon start>mdi-key-chain</v-icon>
      Machine Clients
      <v-spacer />
      <v-btn size="small" variant="tonal" rounded="lg" @click="openCreate">
        <v-icon start>mdi-plus</v-icon>
        New client
      </v-btn>
    </v-card-title>

    <v-card-text>
      <v-progress-linear v-if="loading" indeterminate />

      <div v-else-if="!clients.length" class="text-body-2 text-medium-emphasis font-italic">
        No machine clients for this app yet.
      </div>

      <v-table v-else density="compact">
        <thead>
          <tr>
            <th class="text-left">Name</th>
            <th class="text-left">Client ID</th>
            <th class="text-left">Status</th>
            <th class="text-left">Created</th>
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
              <v-chip v-if="client.revoked" size="x-small" color="error">revoked</v-chip>
              <v-chip v-else size="x-small" color="success">active</v-chip>
            </td>
            <td class="text-caption">{{ formatDate(client.created_at) }}</td>
            <td class="text-right">
              <v-btn size="small" variant="tonal" color="error" @click="removeClient(client)">
                Remove
              </v-btn>
            </td>
          </tr>
        </tbody>
      </v-table>
    </v-card-text>

    <v-dialog v-model="createDialog" max-width="480">
      <v-card>
        <v-card-title>{{ created ? "Client created" : "Create machine client" }}</v-card-title>

        <v-card-text v-if="!created">
          <v-text-field
            v-model="newName"
            label="Name"
            autofocus
            :error-messages="createError ? [createError] : []"
          />
        </v-card-text>

        <v-card-text v-else>
          <v-alert type="warning" variant="tonal" class="mb-3">
            Store these now — the secret is shown once and cannot be recovered.
          </v-alert>
          <div class="text-caption text-medium-emphasis mb-1">Client ID</div>
          <div class="credential-box d-flex align-center mb-4">
            <code class="flex-grow-1 text-truncate">{{ created.client_id }}</code>
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
            <code class="flex-grow-1 text-truncate">{{ created.client_secret }}</code>
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
          <template v-if="!created">
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
  </v-card>
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
