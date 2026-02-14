<script setup lang="ts">
import {
  EvaluationType,
  getSampleDetail,
  type JudgmentSchema,
  type SampleJudgements,
} from "@/api/generated"
import HumanJudgmentCard from "@/components/HumanJudgmentCard.vue"
import LlmJudgmentsCard from "@/components/LlmJudgmentsCard.vue"
import { formatCost } from "@/utils/format"
import { onMounted, ref } from "vue"
import { useRouter } from "vue-router"

const router = useRouter()

const props = defineProps({
  id: {
    type: String,
    required: true,
  },
})

const sample = ref<SampleJudgements | null>(null)
const loading = ref(true)

onMounted(async () => {
  loading.value = true
  const res = await getSampleDetail(parseInt(props.id))
  if (res.status === 200) {
    sample.value = res.data
  }
  loading.value = false
})

function goBack() {
  router.back()
}

function onHumanJudgmentSaved(judgment: JudgmentSchema) {
  if (sample.value) {
    sample.value.human_judgment = judgment
  }
}
</script>

<template>
  <v-container fluid class="pa-6">
    <v-btn variant="text" prepend-icon="mdi-arrow-left" @click="goBack" class="mb-2">
      Back to samples
    </v-btn>

    <h1 class="text-h5 font-weight-bold mb-5">Sample Detail</h1>

    <v-progress-linear v-if="loading" indeterminate color="primary" class="mb-4" />

    <template v-if="sample && !loading">
      <v-row>
        <!-- Left Column: Question/Answer -->
        <v-col cols="12" md="6">
          <v-card class="mb-4">
            <v-card-title class="text-subtitle-1 font-weight-bold">Question</v-card-title>
            <v-card-text class="text-body-1" style="white-space: pre-wrap">{{
              sample.question
            }}</v-card-text>
          </v-card>

          <v-card class="mb-4 golden-standard">
            <v-card-title class="text-subtitle-1 font-weight-bold d-flex align-center">
              Human answer
              <v-chip size="x-small" color="amber-darken-2" variant="tonal" class="ml-2"
                >Golden standard</v-chip
              >
            </v-card-title>
            <v-card-text class="text-body-1" style="white-space: pre-wrap">{{
              sample.human_answer
            }}</v-card-text>
          </v-card>

          <v-card class="mb-4">
            <v-card-title class="text-subtitle-1 font-weight-bold">App answer</v-card-title>
            <v-card-text class="text-body-1" style="white-space: pre-wrap">{{
              sample.app_answer
            }}</v-card-text>
          </v-card>

          <v-card class="mb-4">
            <v-card-text class="d-flex align-center">
              <v-icon size="small" class="mr-2" color="secondary">mdi-currency-usd</v-icon>
              <span class="font-weight-medium">App Cost:</span>
              <span class="ml-2 mr-4">{{ formatCost(sample.app_cost) }}</span>
              <span class="font-weight-medium">Total cost:</span>
              <span class="ml-2">{{ formatCost(sample.total_cost) }}</span>
            </v-card-text>
          </v-card>
        </v-col>

        <!-- Right Column: Judgments -->
        <v-col cols="12" md="6">
          <HumanJudgmentCard
            v-if="sample.evaluation_type === EvaluationType.HUMAN_AND_LLM"
            :sample-id="sample.id"
            :human-judgment="sample.human_judgment"
            class="mb-4"
            @saved="onHumanJudgmentSaved"
          />

          <LlmJudgmentsCard
            :judgments="sample.llm_judgements"
            :completed="sample.llm_judgments_count_completed"
            :total="sample.llm_judgments_count"
            :passed="sample.llm_judgments_count_passed"
            :evaluation-type="sample.evaluation_type"
          />
        </v-col>
      </v-row>
    </template>
  </v-container>
</template>

<style scoped>
.golden-standard {
  border: 2px solid #d4a000;
  background: linear-gradient(135deg, rgba(255, 215, 0, 0.08) 0%, rgba(255, 193, 7, 0.12) 100%);
}
</style>
