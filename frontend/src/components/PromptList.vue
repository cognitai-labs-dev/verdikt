<script setup lang="ts">
import { ref, computed } from "vue"
import { useTheme } from "vuetify"
import { createPatch } from "diff"
import { html } from "diff2html"
import { ColorSchemeType } from "diff2html/lib/types"
import "diff2html/bundles/css/diff2html.min.css"
import { postAppPrompt, patchApp, type PromptVersionSummary } from "@/api/generated"
import { formatDate, getLlmPercentage } from "@/utils/format"

const theme = useTheme()

const props = defineProps<{
  appId: number
  prompts: PromptVersionSummary[]
  activePromptId?: number | null
}>()
const emit = defineEmits<{ activated: [prompt: PromptVersionSummary] }>()

const selectedPrompt = ref<PromptVersionSummary | null>(null)
const dialogOpen = ref(false)
const activating = ref(false)

const compareMode = ref(false)
const compareSelection = ref<PromptVersionSummary[]>([])
const diffDialogOpen = ref(false)

function toggleCompareSelection(prompt: PromptVersionSummary) {
  const idx = compareSelection.value.findIndex((p) => p.id === prompt.id)
  if (idx >= 0) {
    compareSelection.value.splice(idx, 1)
  } else if (compareSelection.value.length < 2) {
    compareSelection.value.push(prompt)
  }
}

function isSelectedForCompare(prompt: PromptVersionSummary) {
  return compareSelection.value.some((p) => p.id === prompt.id)
}

const sortedSelection = computed(() => [...compareSelection.value].sort((a, b) => a.id - b.id))

const diffHtml = computed(() => {
  const sorted = sortedSelection.value
  if (sorted.length !== 2) return ""
  const patch = createPatch(
    "prompt",
    sorted[0]!.content,
    sorted[1]!.content,
    sorted[0]!.hash.slice(0, 12),
    sorted[1]!.hash.slice(0, 12),
  )
  const colorScheme = theme.global.current.value.dark ? ColorSchemeType.DARK : ColorSchemeType.LIGHT
  return html(patch, { drawFileList: false, outputFormat: "line-by-line", colorScheme })
})

function openDiff() {
  diffDialogOpen.value = true
}

function exitCompareMode() {
  compareMode.value = false
  compareSelection.value = []
}

function openPrompt(prompt: PromptVersionSummary) {
  selectedPrompt.value = prompt
  dialogOpen.value = true
}

async function revertToPrompt() {
  if (!selectedPrompt.value) return
  activating.value = true
  try {
    const createRes = await postAppPrompt(props.appId, {
      content: selectedPrompt.value.content,
    })
    if (createRes.status === 201) {
      const newPrompt = createRes.data
      await patchApp(props.appId, { prompt_id: newPrompt.id })
      emit("activated", newPrompt)
      dialogOpen.value = false
    }
  } finally {
    activating.value = false
  }
}

function truncate(text: string, maxLen = 120): string {
  if (text.length <= maxLen) return text
  return text.slice(0, maxLen) + "..."
}
</script>

<template>
  <v-card rounded="lg">
    <v-card-title class="d-flex align-center">
      <v-icon start>mdi-text-box-outline</v-icon>
      Prompts
      <v-spacer />
      <v-btn
        v-if="prompts.length >= 2 && !compareMode"
        variant="text"
        size="small"
        prepend-icon="mdi-compare"
        @click="compareMode = true"
      >
        Compare
      </v-btn>
      <template v-if="compareMode">
        <v-btn
          variant="flat"
          size="small"
          color="primary"
          prepend-icon="mdi-compare"
          :disabled="compareSelection.length !== 2"
          @click="openDiff"
          class="mr-2"
        >
          Show Diff ({{ compareSelection.length }}/2)
        </v-btn>
        <v-btn variant="text" size="small" @click="exitCompareMode">Cancel</v-btn>
      </template>
    </v-card-title>

    <v-card-text v-if="prompts.length === 0" class="text-medium-emphasis font-italic">
      No prompts found.
    </v-card-text>

    <v-list v-if="prompts.length > 0" lines="two">
      <template v-for="(prompt, i) in prompts" :key="prompt.id">
        <v-divider v-if="i > 0" />
        <v-list-item
          @click="compareMode ? toggleCompareSelection(prompt) : openPrompt(prompt)"
          class="py-3"
          :style="
            prompt.id === activePromptId
              ? 'border-left: 3px solid #4CAF50'
              : 'border-left: 3px solid transparent'
          "
        >
          <template v-if="compareMode" #prepend>
            <v-checkbox-btn
              :model-value="isSelectedForCompare(prompt)"
              @click.stop="toggleCompareSelection(prompt)"
              :disabled="!isSelectedForCompare(prompt) && compareSelection.length >= 2"
            />
          </template>
          <v-list-item-title class="text-body-2 font-weight-medium mb-1">
            {{ prompt.hash.slice(0, 12) }}
          </v-list-item-title>
          <v-list-item-subtitle class="text-caption">
            {{ truncate(prompt.content) }}
          </v-list-item-subtitle>
          <template #append>
            <div class="d-flex align-center ga-6">
              <div class="text-center">
                <div class="text-body-1 font-weight-bold">
                  {{ prompt.evaluations_count }}
                </div>
                <div class="text-caption text-medium-emphasis" style="line-height: 1.2">
                  Evaluations
                </div>
              </div>
              <div class="text-center">
                <div class="text-body-1 font-weight-bold text-blue">
                  {{ getLlmPercentage(prompt.llm_passed_count, prompt.llm_total_count) }}
                </div>
                <div class="text-caption text-medium-emphasis" style="line-height: 1.2">
                  LLM
                  <span class="text-caption text-disabled">
                    {{ prompt.llm_passed_count }}/{{ prompt.llm_total_count }}
                  </span>
                </div>
              </div>
              <div class="text-center">
                <div class="text-body-1 font-weight-bold text-orange">
                  {{
                    getLlmPercentage(
                      prompt.human_and_llm_matched_count,
                      prompt.human_and_llm_total_count,
                    )
                  }}
                </div>
                <div class="text-caption text-medium-emphasis" style="line-height: 1.2">
                  Human
                  <span class="text-caption text-disabled">
                    {{ prompt.human_and_llm_matched_count }}/{{ prompt.human_and_llm_total_count }}
                  </span>
                </div>
              </div>
              <span class="text-caption text-medium-emphasis">{{
                formatDate(prompt.created_at)
              }}</span>
            </div>
          </template>
        </v-list-item>
      </template>
    </v-list>
  </v-card>

  <v-dialog v-model="dialogOpen" max-width="700">
    <v-card v-if="selectedPrompt" rounded="lg">
      <v-card-title class="d-flex align-center">
        <v-icon start>mdi-text-box-outline</v-icon>
        Prompt Details
      </v-card-title>
      <v-card-text>
        <div class="text-caption text-medium-emphasis mb-1">Hash</div>
        <div class="text-body-2 mb-3 font-weight-medium">{{ selectedPrompt.hash }}</div>

        <div class="text-caption text-medium-emphasis mb-1">Created</div>
        <div class="text-body-2 mb-3">{{ formatDate(selectedPrompt.created_at) }}</div>

        <div class="d-flex ga-6 mb-4">
          <div class="text-center">
            <div class="text-body-1 font-weight-bold">
              {{ selectedPrompt.evaluations_count }}
            </div>
            <div class="text-caption text-medium-emphasis" style="line-height: 1.2">
              Evaluations
            </div>
          </div>
          <div class="text-center">
            <div class="text-body-1 font-weight-bold text-blue">
              {{
                getLlmPercentage(selectedPrompt.llm_passed_count, selectedPrompt.llm_total_count)
              }}
            </div>
            <div class="text-caption text-medium-emphasis" style="line-height: 1.2">
              LLM
              <span class="text-caption text-disabled">
                {{ selectedPrompt.llm_passed_count }}/{{ selectedPrompt.llm_total_count }}
              </span>
            </div>
          </div>
          <div class="text-center">
            <div class="text-body-1 font-weight-bold text-orange">
              {{
                getLlmPercentage(
                  selectedPrompt.human_and_llm_matched_count,
                  selectedPrompt.human_and_llm_total_count,
                )
              }}
            </div>
            <div class="text-caption text-medium-emphasis" style="line-height: 1.2">
              Human
              <span class="text-caption text-disabled">
                {{ selectedPrompt.human_and_llm_matched_count }}/{{
                  selectedPrompt.human_and_llm_total_count
                }}
              </span>
            </div>
          </div>
        </div>

        <div class="text-caption text-medium-emphasis mb-1">Content</div>
        <v-sheet
          rounded="lg"
          color="grey-darken-3"
          class="pa-4 text-body-2"
          style="white-space: pre-wrap; max-height: 400px; overflow-y: auto"
          >{{ selectedPrompt.content }}</v-sheet
        >
      </v-card-text>
      <v-card-actions>
        <v-spacer />
        <v-btn variant="text" @click="dialogOpen = false">Close</v-btn>
        <v-btn
          v-if="selectedPrompt?.id !== activePromptId"
          color="primary"
          variant="flat"
          :loading="activating"
          @click="revertToPrompt"
        >
          Revert to This Version
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>

  <v-dialog v-model="diffDialogOpen" max-width="900">
    <v-card v-if="compareSelection.length === 2" rounded="lg">
      <v-card-title class="d-flex align-center">
        <v-icon start>mdi-compare</v-icon>
        Prompt Diff
      </v-card-title>
      <v-card-subtitle class="px-4 pb-2">
        {{ sortedSelection[0]?.hash.slice(0, 12) }}
        &rarr;
        {{ sortedSelection[1]?.hash.slice(0, 12) }}
      </v-card-subtitle>
      <v-card-text>
        <!-- eslint-disable-next-line vue/no-v-html -->
        <div class="diff-wrapper" v-html="diffHtml" />
      </v-card-text>
      <v-card-actions>
        <v-spacer />
        <v-btn variant="text" @click="diffDialogOpen = false">Close</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<style>
.diff-wrapper .d2h-file-header {
  display: none;
}

.diff-wrapper .d2h-file-wrapper {
  border-radius: 8px;
  overflow: hidden;
}
</style>
