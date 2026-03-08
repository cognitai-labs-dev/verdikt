<script setup lang="ts">
import { ref, computed } from "vue"
import { postAppDatasets, type AppDatasetSchema } from "@/api/generated"
import { formatDate } from "@/utils/format"

const props = defineProps<{
  appId: number
  datasets: AppDatasetSchema[]
}>()

const emit = defineEmits<{ created: [datasets: AppDatasetSchema[]] }>()

const headers = [
  { title: "Question", key: "question", sortable: false },
  { title: "Human Answer", key: "human_answer", sortable: false },
  { title: "Created", key: "created_at", sortable: true, width: "160px" },
]

// shared dialog state
const dialogOpen = ref(false)
const dialogMode = ref<"view" | "create">("create")
const question = ref("")
const humanAnswer = ref("")

// create-specific state
const creating = ref(false)
const createError = ref<string | null>(null)

const dialogTitle = computed(() => (dialogMode.value === "create" ? "Add Question" : "Question"))
const isReadOnly = computed(() => dialogMode.value === "view")

function openCreateDialog() {
  dialogMode.value = "create"
  question.value = ""
  humanAnswer.value = ""
  createError.value = null
  dialogOpen.value = true
}

function openViewDialog(item: AppDatasetSchema) {
  dialogMode.value = "view"
  question.value = item.question
  humanAnswer.value = item.human_answer
  dialogOpen.value = true
}

async function handleCreate() {
  if (!question.value.trim() || !humanAnswer.value.trim()) return
  creating.value = true
  createError.value = null
  try {
    const res = await postAppDatasets(props.appId, {
      datasets: [{ question: question.value.trim(), human_answer: humanAnswer.value.trim() }],
    })
    if (res.status === 201) {
      emit("created", res.data)
      dialogOpen.value = false
    } else {
      createError.value = "Failed to add question. Please try again."
    }
  } finally {
    creating.value = false
  }
}

function truncate(text: string, maxLen = 100): string {
  if (text.length <= maxLen) return text
  return text.slice(0, maxLen) + "..."
}
</script>

<template>
  <v-card rounded="lg">
    <v-card-title class="d-flex align-center">
      <v-icon start>mdi-help-circle-outline</v-icon>
      Questions
      <v-spacer />
      <v-btn size="small" variant="tonal" prepend-icon="mdi-plus" @click="openCreateDialog">
        Add Question
      </v-btn>
    </v-card-title>

    <v-card-text v-if="datasets.length === 0" class="text-medium-emphasis font-italic">
      No questions found.
    </v-card-text>

    <v-data-table
      v-if="datasets.length > 0"
      :headers="headers"
      :items="datasets"
      :items-per-page="10"
      density="comfortable"
      @click:row="(_: MouseEvent, { item }: { item: AppDatasetSchema }) => openViewDialog(item)"
      style="cursor: pointer"
    >
      <template #item.question="{ item }">
        <span class="text-body-2">{{ truncate(item.question) }}</span>
      </template>
      <template #item.human_answer="{ item }">
        <span class="text-body-2 text-medium-emphasis">{{ truncate(item.human_answer) }}</span>
      </template>
      <template #item.created_at="{ item }">
        <span class="text-caption text-medium-emphasis">{{ formatDate(item.created_at) }}</span>
      </template>
    </v-data-table>
  </v-card>

  <v-dialog v-model="dialogOpen" max-width="600">
    <v-card rounded="lg">
      <v-card-title class="d-flex align-center">
        <v-icon start>{{ isReadOnly ? "mdi-help-circle-outline" : "mdi-plus" }}</v-icon>
        {{ dialogTitle }}
      </v-card-title>
      <v-card-text>
        <template v-if="isReadOnly">
          <div class="text-caption text-medium-emphasis mb-1">Question</div>
          <v-sheet
            rounded="lg"
            color="grey-darken-3"
            class="pa-4 text-body-2 mb-4"
            style="white-space: pre-wrap; max-height: 300px; overflow-y: auto"
            >{{ question }}</v-sheet
          >

          <div class="text-caption text-medium-emphasis mb-1">Human Answer</div>
          <v-sheet
            rounded="lg"
            color="grey-darken-3"
            class="pa-4 text-body-2"
            style="white-space: pre-wrap; max-height: 300px; overflow-y: auto"
            >{{ humanAnswer }}</v-sheet
          >
        </template>

        <template v-else>
          <v-textarea
            v-model="question"
            label="Question"
            rows="3"
            auto-grow
            variant="outlined"
            class="mb-3"
          />
          <v-textarea
            v-model="humanAnswer"
            label="Human Answer"
            rows="3"
            auto-grow
            variant="outlined"
          />
          <v-alert v-if="createError" type="error" variant="tonal" class="mt-3">
            {{ createError }}
          </v-alert>
        </template>
      </v-card-text>
      <v-card-actions>
        <v-spacer />
        <v-btn variant="text" @click="dialogOpen = false">Close</v-btn>
        <v-btn
          v-if="!isReadOnly"
          color="primary"
          variant="flat"
          :loading="creating"
          :disabled="!question.trim() || !humanAnswer.trim()"
          @click="handleCreate"
        >
          Add
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>
