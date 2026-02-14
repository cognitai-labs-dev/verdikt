<script setup lang="ts">
import {
  EvaluationType,
  getSampleDetail,
  type JudgmentSchema,
  type SampleJudgements,
} from "@/api/generated"
import HumanJudgmentCard from "@/components/HumanJudgmentCard.vue"
import LlmJudgmentsCard from "@/components/LlmJudgmentsCard.vue"
import SampleContentCards from "@/components/SampleContentCards.vue"
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
          <SampleContentCards
            :question="sample.question"
            :human-answer="sample.human_answer"
            :app-answer="sample.app_answer"
            :app-cost="sample.app_cost"
            :total-cost="sample.total_cost"
          />
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
