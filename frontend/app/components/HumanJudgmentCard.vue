<script setup lang="ts">
import { postJudgment, type JudgmentSchema } from "@/api/generated"
import { computed, ref, watch } from "vue"

const saving = ref(false)
const humanPassed = ref<boolean | null>(null)
const humanReasoning = ref("")
const props = defineProps<{
  sampleId: number
  humanJudgment: JudgmentSchema | null
}>()
const emit = defineEmits<{
  saved: [judgment: JudgmentSchema]
}>()

// Initialize form fields when humanJudgment prop changes
watch(
  () => props.humanJudgment,
  (judgment) => {
    if (judgment) {
      humanPassed.value = judgment.passed ?? null
      humanReasoning.value = judgment.reasoning ?? ""
    }
  },
  { immediate: true },
)

const isLocked = computed(() => {
  return props.humanJudgment?.status === "COMPLETED"
})

const canSave = computed(() => {
  return humanPassed.value !== null && humanReasoning.value.trim() !== ""
})

async function saveJudgment() {
  if (!canSave.value || !props.humanJudgment) return

  saving.value = true
  const res = await postJudgment(props.sampleId, {
    passed: humanPassed.value!,
    reasoning: humanReasoning.value,
  })
  if (res.status == 201) {
    emit("saved", {
      ...props.humanJudgment,
      status: "COMPLETED",
      passed: humanPassed.value,
      reasoning: humanReasoning.value,
    })
  }
  saving.value = false
}

defineExpose({ humanPassed, humanReasoning, saveJudgment, isLocked })
</script>

<template>
  <v-card>
    <v-card-title class="d-flex align-center">
      <v-icon size="small" class="mr-2" color="secondary">mdi-account-check</v-icon>
      Human Judgment
      <v-chip
        class="ml-2"
        :color="humanJudgment?.status === 'COMPLETED' ? 'success' : 'warning'"
        size="small"
        variant="tonal"
      >
        {{ humanJudgment?.status ?? "PENDING" }}
      </v-chip>
    </v-card-title>
    <v-card-text>
      <div class="mb-4">
        <div class="text-subtitle-2 mb-2">Pass/Fail</div>
        <div class="d-flex ga-2">
          <v-btn
            :color="'success'"
            :variant="humanPassed === true ? 'flat' : 'outlined'"
            :disabled="isLocked && humanPassed !== true"
            @click="!isLocked && (humanPassed = true)"
          >
            <v-icon start>mdi-check</v-icon>
            Pass
          </v-btn>
          <v-btn
            :color="'error'"
            :variant="humanPassed === false ? 'flat' : 'outlined'"
            :disabled="isLocked && humanPassed !== false"
            @click="!isLocked && (humanPassed = false)"
          >
            <v-icon start>mdi-close</v-icon>
            Fail
          </v-btn>
        </div>
      </div>

      <v-textarea
        v-model="humanReasoning"
        variant="outlined"
        label="Reasoning"
        rows="3"
        class="mb-2"
        :readonly="isLocked"
      />

      <v-btn
        v-if="!isLocked"
        color="primary"
        :variant="canSave ? 'flat' : 'tonal'"
        class="mt-2"
        :loading="saving"
        :disabled="!canSave"
        @click="saveJudgment"
      >
        Save Judgment
      </v-btn>
    </v-card-text>
  </v-card>
</template>
