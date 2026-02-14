<script setup lang="ts">
import { onMounted, ref, computed } from "vue"
import { getEvaluationsSummaries, type EvaluationSummary, EvaluationType } from "@/api/generated"
import { useRouter } from "vue-router"
import { useActiveApp } from "@/stores/useActiveApp"
import LlmStatisticCell from "@/components/LlmStatisticCell.vue"
import LlmStatusCell from "@/components/LlmStatusCell.vue"
import CostCell from "@/components/CostCell.vue"
import { formatDate } from "@/utils/format"

const router = useRouter()
const { loadApp } = useActiveApp()
const EVAL_TYPE_COOKIE = "selectedEvalType"

const props = defineProps({
  id: {
    type: String,
    required: true,
  },
})

function getEvalTypeCookie(): EvaluationType {
  const match = document.cookie.match(new RegExp(`(?:^|; )${EVAL_TYPE_COOKIE}=([^;]*)`))
  const value = match?.[1] ? decodeURIComponent(match[1]) : null
  if (value === EvaluationType.HUMAN_AND_LLM) return EvaluationType.HUMAN_AND_LLM
  return EvaluationType.LLM_ONLY
}

function setEvalTypeCookie(type: EvaluationType) {
  document.cookie = `${EVAL_TYPE_COOKIE}=${encodeURIComponent(type)}; path=/; max-age=31536000`
}

const items = ref<EvaluationSummary[]>([])
const selectedEvalType = ref<EvaluationType>(getEvalTypeCookie())

const headers = computed(() => {
  const base = [
    { title: "Version", key: "version" },
    { title: "Created", key: "created_at" },
  ]

  if (selectedEvalType.value === EvaluationType.LLM_ONLY) {
    base.push({ title: "AI judging", key: "llm_judgements_status" })
    base.push({ title: "Passed", key: "llm_judgements_statistic" })
  } else {
    base.push({ title: "Human judging", key: "human_judgements_status" })
    base.push({ title: "AI judging", key: "llm_judgements_status" })
    base.push({ title: "Matched", key: "llm_judgements_statistic" })
  }

  base.push({ title: "Cost", key: "total_cost" })

  return base
})

const fetchEvaluations = async () => {
  const res = await getEvaluationsSummaries({
    app_id: Number(props.id),
    eval_type: selectedEvalType.value,
  })
  if (res.status === 200) {
    items.value = res.data
  }
}

onMounted(async () => {
  loadApp(Number(props.id))
  await fetchEvaluations()
})

const switchEvalType = async (type: EvaluationType) => {
  selectedEvalType.value = type
  setEvalTypeCookie(type)
  await fetchEvaluations()
}

const routeToEval = (_event: Event, { item }: { item: EvaluationSummary }) => {
  router.push({ path: `/evaluation/${item.id}/samples` })
}
</script>

<template>
  <v-container fluid class="pa-6">
    <v-btn-toggle
      v-model="selectedEvalType"
      mandatory
      class="mb-5"
      color="primary"
      variant="outlined"
      divided
    >
      <v-btn :value="EvaluationType.LLM_ONLY" @click="switchEvalType(EvaluationType.LLM_ONLY)">
        LLM Only
      </v-btn>
      <v-btn
        :value="EvaluationType.HUMAN_AND_LLM"
        @click="switchEvalType(EvaluationType.HUMAN_AND_LLM)"
      >
        Human and LLM
      </v-btn>
    </v-btn-toggle>

    <v-card>
      <v-data-table :items="items" :headers="headers" @click:row="routeToEval">
        <template #item.created_at="{ item }">
          {{ formatDate(item.created_at) }}
        </template>

        <template #header.llm_judgements_statistic="{ column }">
          <span>{{ column.title }}</span>
          <v-icon
            size="small"
            class="ml-1"
            v-tooltip:bottom="
              selectedEvalType === EvaluationType.LLM_ONLY
                ? 'LLM judges that marked this answer as correct'
                : 'LLM judges whose verdict matched the human judgment'
            "
            >mdi-help-circle-outline</v-icon
          >
        </template>
        <template #item.llm_judgements_statistic="{ item }">
          <LlmStatisticCell
            :passed="item.llm_judgments_count_passed"
            :total="item.llm_judgments_count"
          />
        </template>

        <template #header.human_judgements_status="{ column }">
          <span>{{ column.title }}</span>
          <v-icon
            size="small"
            class="ml-1"
            v-tooltip:bottom="
              'Progress of human judging — checkmark when all judgments are completed'
            "
            >mdi-help-circle-outline</v-icon
          >
        </template>

        <template #item.human_judgements_status="{ item }">
          <LlmStatusCell
            :count-completed="item.human_judgement_count_completed"
            :count="item.human_judgement_count"
          />
        </template>

        <template #header.llm_judgements_status="{ column }">
          <span>{{ column.title }}</span>
          <v-icon
            size="small"
            class="ml-1"
            v-tooltip:bottom="'Progress of LLM judging — checkmark when all judges have completed'"
            >mdi-help-circle-outline</v-icon
          >
        </template>
        <template #item.llm_judgements_status="{ item }">
          <LlmStatusCell
            :count-completed="item.llm_judgments_count_completed"
            :count="item.llm_judgments_count"
          />
        </template>

        <template #item.total_cost="{ item }">
          <CostCell :cost="item.total_cost" />
        </template>
      </v-data-table>
    </v-card>
  </v-container>
</template>
