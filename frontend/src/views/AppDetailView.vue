<script setup lang="ts">
import { ref, computed, onMounted } from "vue"
import { useRouter } from "vue-router"
import { useActiveApp } from "@/stores/useActiveApp"
import { getAppPrompts, postAppPrompt, patchApp, type PromptVersionSummary } from "@/api/generated"
import PromptList from "@/components/PromptList.vue"

const props = defineProps<{ id: string }>()
const router = useRouter()
const { activeApp: app, loadApp } = useActiveApp()

const appId = Number(props.id)
const prompts = ref<PromptVersionSummary[]>([])

const activePrompt = computed(() =>
  prompts.value.find((p) => p.id === app.value?.current_prompt_version_id),
)

onMounted(async () => {
  await loadApp(appId)
  const res = await getAppPrompts(appId)
  if (res.status === 200) {
    prompts.value = res.data
  }
})

const createDialogOpen = ref(false)
const newPromptContent = ref("")
const creating = ref(false)

function openCreateDialog() {
  newPromptContent.value = activePrompt.value?.content ?? ""
  createDialogOpen.value = true
}

async function createAndActivatePrompt() {
  creating.value = true
  try {
    const res = await postAppPrompt(appId, { content: newPromptContent.value })
    if (res.status === 201) {
      const newPrompt = res.data
      prompts.value.unshift(newPrompt)
      await patchApp(appId, { prompt_id: newPrompt.id })
      if (app.value) {
        app.value.current_prompt_version_id = newPrompt.id
      }
      createDialogOpen.value = false
    }
  } finally {
    creating.value = false
  }
}

function onPromptActivated(prompt: PromptVersionSummary) {
  prompts.value.unshift(prompt)
  if (app.value) {
    app.value.current_prompt_version_id = prompt.id
  }
}

const goToEvaluations = () => {
  router.push(`/app/${appId}/evaluations`)
}
</script>

<template>
  <v-container fluid class="pa-6">
    <template v-if="app">
      <v-btn color="primary" variant="flat" rounded="lg" @click="goToEvaluations" class="mb-4">
        <v-icon start>mdi-clipboard-list-outline</v-icon>
        View Evaluations
      </v-btn>

      <v-row class="mb-6">
        <v-col cols="12" md="6">
          <v-card rounded="lg">
            <v-card-title class="d-flex align-center">
              <v-icon start>mdi-text-box-outline</v-icon>
              Meta Prompt
            </v-card-title>
            <v-card-text>
              <div class="text-body-2 text-medium-emphasis font-italic">
                No meta prompt configured
              </div>
            </v-card-text>
          </v-card>
        </v-col>

        <v-col cols="12" md="6">
          <v-card rounded="lg">
            <v-card-title class="d-flex align-center">
              <v-icon start>mdi-text-box-check-outline</v-icon>
              Active Prompt
              <v-spacer />
              <v-btn size="small" variant="tonal" rounded="lg" @click="openCreateDialog">
                <v-icon start>mdi-pencil</v-icon>
                Edit
              </v-btn>
            </v-card-title>
            <v-card-text>
              <template v-if="activePrompt">
                <div class="text-caption text-medium-emphasis mb-1">
                  {{ activePrompt.hash.slice(0, 12) }}
                </div>
                <div
                  class="text-body-2"
                  style="white-space: pre-wrap; height: 300px; overflow-y: auto"
                >
                  {{ activePrompt.content }}
                </div>
              </template>
              <div v-else class="text-body-2 text-medium-emphasis font-italic">
                No active prompt set
              </div>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>

      <PromptList
        :app-id="appId"
        :prompts="prompts"
        :active-prompt-id="app.current_prompt_version_id"
        @activated="onPromptActivated"
      />
    </template>

    <v-alert v-if="!app" type="error" variant="tonal"> App not found. </v-alert>

    <v-dialog v-model="createDialogOpen" max-width="700">
      <v-card rounded="lg">
        <v-card-title class="d-flex align-center">
          <v-icon start>mdi-plus</v-icon>
          Create New Prompt
        </v-card-title>
        <v-card-text>
          <v-textarea
            v-model="newPromptContent"
            label="Prompt content"
            rows="12"
            auto-grow
            variant="outlined"
          />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="createDialogOpen = false">Cancel</v-btn>
          <v-btn
            color="primary"
            variant="flat"
            :loading="creating"
            :disabled="!newPromptContent.trim()"
            @click="createAndActivatePrompt"
          >
            Create &amp; Set Active
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>
