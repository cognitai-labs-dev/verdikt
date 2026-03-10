<script setup lang="ts">
import {
  EvaluationType,
  getEvaluationSamples,
  getSampleDetail,
  type JudgmentSchema,
  type SampleJudgmentSummarySchema,
  type SampleJudgments,
} from "@/api/generated"
import HumanJudgmentCard from "@/components/HumanJudgmentCard.vue"
import LlmJudgmentsCard from "@/components/LlmJudgmentsCard.vue"
import SampleContentCards from "@/components/SampleContentCards.vue"
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from "vue"
import { useRoute, useRouter } from "vue-router"

const router = useRouter()
const route = useRoute()

const props = defineProps({
  id: {
    type: String,
    required: true,
  },
})

const samples = ref<SampleJudgmentSummarySchema[]>([])
const currentIndex = ref(0)
const currentDetail = ref<SampleJudgments | null>(null)
const loadingList = ref(true)
const loadingDetail = ref(false)
const slideDirection = ref<"left" | "right">("left")
const judgmentCardRef = ref<InstanceType<typeof HumanJudgmentCard> | null>(null)

const currentSample = computed(() => samples.value[currentIndex.value] ?? null)
const totalCount = computed(() => samples.value.length)
const completedCount = computed(() => samples.value.filter((s) => s.status === "COMPLETED").length)
const progressPercent = computed(() => {
  if (totalCount.value === 0) return 0
  return (completedCount.value / totalCount.value) * 100
})

onMounted(async () => {
  loadingList.value = true
  const res = await getEvaluationSamples(parseInt(props.id), { judgment_type: "HUMAN" })
  if (res.status === 200) {
    samples.value = res.data
    const querySampleId = route.query.startSampleId
    if (querySampleId) {
      const targetIndex = samples.value.findIndex((s) => s.sample_id === Number(querySampleId))
      currentIndex.value = targetIndex >= 0 ? targetIndex : 0
    } else {
      const firstPending = samples.value.findIndex((s) => s.status !== "COMPLETED")
      currentIndex.value = firstPending >= 0 ? firstPending : 0
    }
    await loadCurrentDetail()
  }
  loadingList.value = false
  document.addEventListener("keydown", handleKeydown)
})

onUnmounted(() => {
  document.removeEventListener("keydown", handleKeydown)
})

watch(currentIndex, async () => {
  await loadCurrentDetail()
})

async function loadCurrentDetail() {
  const sample = currentSample.value
  if (!sample) return
  loadingDetail.value = true
  const res = await getSampleDetail(sample.sample_id)
  if (res.status === 200) {
    currentDetail.value = res.data
  }
  loadingDetail.value = false
}

function navigate(direction: "prev" | "next") {
  if (direction === "next" && currentIndex.value < totalCount.value - 1) {
    slideDirection.value = "left"
    currentIndex.value++
  } else if (direction === "prev" && currentIndex.value > 0) {
    slideDirection.value = "right"
    currentIndex.value--
  }
}

function onHumanJudgmentSaved(judgment: JudgmentSchema) {
  if (currentDetail.value) {
    currentDetail.value.human_judgment = judgment
  }
  // Update the samples list status
  if (currentSample.value) {
    samples.value[currentIndex.value] = {
      ...currentSample.value,
      status: "COMPLETED",
      passed: judgment.passed,
    }
  }
  // Auto-advance to next pending after a short delay
  setTimeout(() => {
    const nextPending = samples.value.findIndex(
      (s, i) => i > currentIndex.value && s.status !== "COMPLETED",
    )
    if (nextPending >= 0) {
      slideDirection.value = "left"
      currentIndex.value = nextPending
    } else {
      const anyPending = samples.value.findIndex((s) => s.status !== "COMPLETED")
      if (anyPending >= 0) {
        slideDirection.value = "left"
        currentIndex.value = anyPending
      }
    }
  }, 300)
}

function goBack() {
  router.back()
}

function handleKeydown(e: KeyboardEvent) {
  const target = e.target as HTMLElement
  const isInInput = target.tagName === "TEXTAREA" || target.tagName === "INPUT"

  if (e.key === "ArrowLeft" && !isInInput) {
    e.preventDefault()
    navigate("prev")
    return
  }

  if (e.key === "ArrowRight" && !isInInput) {
    e.preventDefault()
    navigate("next")
    return
  }

  if (e.ctrlKey && e.key === "Enter") {
    e.preventDefault()
    judgmentCardRef.value?.saveJudgment()
    return
  }

  if (isInInput) return

  const card = judgmentCardRef.value
  if (card && !card.isLocked) {
    if (e.key === "p" || e.key === "P") {
      e.preventDefault()
      card.humanPassed = true
      nextTick(() => {
        const textarea = document.querySelector(".v-card textarea") as HTMLElement
        textarea?.focus()
      })
      return
    }

    if (e.key === "f" || e.key === "F") {
      e.preventDefault()
      card.humanPassed = false
      nextTick(() => {
        const textarea = document.querySelector(".v-card textarea") as HTMLElement
        textarea?.focus()
      })
      return
    }
  }
}
</script>

<template>
  <v-container fluid class="pa-6">
    <div class="d-flex align-center mb-2">
      <v-btn variant="text" prepend-icon="mdi-arrow-left" @click="goBack"> Back to samples </v-btn>
      <v-spacer />
      <div v-if="!loadingList && totalCount > 0" class="d-flex align-center ga-3">
        <v-chip variant="tonal" color="primary" size="small">
          {{ completedCount }} / {{ totalCount }} judged
        </v-chip>
        <span class="text-body-2 text-medium-emphasis">
          Sample {{ currentIndex + 1 }} of {{ totalCount }}
        </span>
      </div>
    </div>

    <v-progress-linear
      v-if="!loadingList && totalCount > 0"
      :model-value="progressPercent"
      color="success"
      height="4"
      class="mb-4"
      rounded
    />

    <div class="d-flex align-center mb-5">
      <h1 class="text-h5 font-weight-bold">Judging</h1>
      <v-chip class="ml-3" color="primary" variant="tonal" size="small"> Human & LLM </v-chip>
    </div>

    <!-- Loading state -->
    <div v-if="loadingList" class="d-flex justify-center align-center" style="min-height: 400px">
      <v-progress-circular indeterminate size="64" color="primary" />
    </div>

    <!-- Sample slideshow -->
    <template v-else-if="currentDetail && !loadingList">
      <transition :name="slideDirection === 'left' ? 'slide-left' : 'slide-right'" mode="out-in">
        <div :key="currentIndex">
          <v-progress-linear v-if="loadingDetail" indeterminate color="primary" class="mb-4" />

          <template v-if="!loadingDetail">
            <v-row>
              <!-- Left Column: Question/Answer -->
              <v-col cols="12" md="6">
                <SampleContentCards
                  :question="currentDetail.question"
                  :human-answer="currentDetail.human_answer"
                  :app-answer="currentDetail.app_answer"
                  :app-cost="currentDetail.app_cost"
                  :total-cost="currentDetail.total_cost"
                />
              </v-col>

              <!-- Right Column: Judgments (same as SampleDetailView) -->
              <v-col cols="12" md="6">
                <HumanJudgmentCard
                  v-if="currentDetail.evaluation_type === EvaluationType.HUMAN_AND_LLM"
                  ref="judgmentCardRef"
                  :sample-id="currentDetail.id"
                  :human-judgment="currentDetail.human_judgment"
                  class="mb-4"
                  @saved="onHumanJudgmentSaved"
                />

                <LlmJudgmentsCard
                  :judgments="currentDetail.llm_judgments"
                  :completed="currentDetail.llm_judgments_count_completed"
                  :total="currentDetail.llm_judgments_count"
                  :passed="currentDetail.llm_judgments_count_passed"
                  :evaluation-type="currentDetail.evaluation_type"
                />

                <!-- Keyboard shortcuts -->
                <v-card class="mt-4" variant="outlined">
                  <v-card-text class="py-3">
                    <div
                      class="text-caption text-medium-emphasis font-weight-bold text-uppercase mb-2"
                    >
                      Keyboard Shortcuts
                    </div>
                    <div class="d-flex flex-wrap ga-3">
                      <div class="shortcut-item">
                        <kbd>P</kbd>
                        <span class="text-body-2 text-medium-emphasis">Pass</span>
                      </div>
                      <div class="shortcut-item">
                        <kbd>F</kbd>
                        <span class="text-body-2 text-medium-emphasis">Fail</span>
                      </div>
                      <div class="shortcut-item">
                        <kbd>Ctrl</kbd> + <kbd>Enter</kbd>
                        <span class="text-body-2 text-medium-emphasis">Submit</span>
                      </div>
                      <div class="shortcut-item">
                        <kbd>&larr;</kbd> <kbd>&rarr;</kbd>
                        <span class="text-body-2 text-medium-emphasis">Navigate</span>
                      </div>
                    </div>
                  </v-card-text>
                </v-card>
              </v-col>
            </v-row>

            <!-- Navigation buttons -->
            <div class="d-flex justify-center align-center ga-4 mt-4">
              <v-btn
                variant="outlined"
                :disabled="currentIndex === 0"
                @click="navigate('prev')"
                prepend-icon="mdi-arrow-left"
              >
                Previous
              </v-btn>
              <v-btn
                variant="outlined"
                :disabled="currentIndex === totalCount - 1"
                @click="navigate('next')"
                append-icon="mdi-arrow-right"
              >
                Next
              </v-btn>
            </div>
          </template>
        </div>
      </transition>
    </template>
  </v-container>
</template>

<style scoped>
kbd {
  display: inline-block;
  min-width: 24px;
  padding: 2px 8px;
  font-size: 0.75rem;
  font-family: inherit;
  font-weight: 600;
  text-align: center;
  color: rgba(var(--v-theme-on-surface), 0.7);
  background: linear-gradient(
    180deg,
    rgba(var(--v-theme-on-surface), 0.04),
    rgba(var(--v-theme-on-surface), 0.08)
  );
  border-radius: 6px;
  border: 1px solid rgba(var(--v-theme-on-surface), 0.15);
  box-shadow: 0 1px 0 rgba(var(--v-theme-on-surface), 0.1);
  line-height: 1.8;
}

.shortcut-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.slide-left-enter-active,
.slide-left-leave-active,
.slide-right-enter-active,
.slide-right-leave-active {
  transition: all 0.2s ease;
}

.slide-left-enter-from {
  opacity: 0;
  transform: translateX(30px);
}

.slide-left-leave-to {
  opacity: 0;
  transform: translateX(-30px);
}

.slide-right-enter-from {
  opacity: 0;
  transform: translateX(-30px);
}

.slide-right-leave-to {
  opacity: 0;
  transform: translateX(30px);
}
</style>
