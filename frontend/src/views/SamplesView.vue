<script setup lang="ts">
import { EvaluationType, getSamplesSummaries, type SampleSummary } from "@/api/generated"
import LlmStatisticCell from "@/components/LlmStatisticCell.vue"
import LlmStatusCell from "@/components/LlmStatusCell.vue"
import CostCell from "@/components/CostCell.vue"
import { onMounted, ref } from "vue"
import { useRouter } from "vue-router"

const router = useRouter()
const items = ref<SampleSummary[]>([])
const evaluationType = ref<EvaluationType>()

const evaluationTypeLabel: Record<EvaluationType, string> = {
  [EvaluationType.LLM_ONLY]: "LLM Only",
  [EvaluationType.HUMAN_AND_LLM]: "Human & LLM",
}

const headers = ref([
  { title: "Question", key: "question" },
  { title: "Human answer", key: "human_answer" },
  { title: "AI answer", key: "app_answer" },
])

onMounted(async () => {
  const res = await getSamplesSummaries(parseInt(props.id))
  if (res.status === 200) {
    items.value = res.data
    if (items.value.length > 0) evaluationType.value = items.value[0]?.evaluation_type

    if (evaluationType.value === EvaluationType.LLM_ONLY) {
      headers.value.push({ title: "AI judging", key: "llm_judgments_status" })
      headers.value.push({ title: "Passed", key: "llm_judgments_statistic" })
    } else if (evaluationType.value === EvaluationType.HUMAN_AND_LLM) {
      headers.value.push({ title: "Human judging", key: "human_judgment_passed" })
      headers.value.push({ title: "AI judging", key: "llm_judgments_status" })
      headers.value.push({ title: "Matched", key: "llm_judgments_statistic" })
    }
  }
  headers.value.push({ title: "Cost", key: "total_cost" })
})

const props = defineProps({
  id: {
    type: String,
    required: true,
  },
})

function goBack() {
  router.back()
}

function onRowClick(_event: Event, { item }: { item: SampleSummary }) {
  if (evaluationType.value == EvaluationType.LLM_ONLY) {
    router.push({ path: `/sample/${item.id}/detail` })
  } else {
    router.push({ path: `/evaluation/${props.id}/judging`, query: { startSampleId: item.id } })
  }
}
</script>

<template>
  <v-container fluid class="pa-6">
    <v-btn variant="text" prepend-icon="mdi-arrow-left" @click="goBack" class="mb-2">
      Back to Evaluations
    </v-btn>

    <div v-if="evaluationType" class="d-flex align-center mb-5">
      <h1 class="text-h5 font-weight-bold">Evaluation Samples</h1>
      <v-chip class="ml-3" color="primary" variant="tonal" size="small">
        {{ evaluationTypeLabel[evaluationType] }}
      </v-chip>
    </div>

    <v-card>
      <v-data-table :items="items" :headers="headers" @click:row="onRowClick">
        <template #item.question="{ item }">
          <v-tooltip location="top">
            <template #activator="{ props }">
              <span class="truncate" v-bind="props">{{ item.question }}</span>
            </template>
            <span class="tooltip-text">{{ item.question }}</span>
          </v-tooltip>
        </template>

        <template #item.human_answer="{ item }">
          <v-tooltip location="top">
            <template #activator="{ props }">
              <span class="truncate" v-bind="props">{{ item.human_answer }}</span>
            </template>
            <span class="tooltip-text">{{ item.human_answer }}</span>
          </v-tooltip>
        </template>

        <template #item.app_answer="{ item }">
          <v-tooltip location="top">
            <template #activator="{ props }">
              <span class="truncate" v-bind="props">{{ item.app_answer }}</span>
            </template>
            <span class="tooltip-text">{{ item.app_answer }}</span>
          </v-tooltip>
        </template>

        <template #header.llm_judgments_statistic="{ column }">
          <span>{{ column.title }}</span>
          <v-icon
            size="small"
            class="ml-1"
            v-tooltip:bottom="
              evaluationType === EvaluationType.LLM_ONLY
                ? 'LLM judges that marked this answer as correct'
                : 'LLM judges whose verdict matched the human judgment'
            "
            >mdi-help-circle-outline</v-icon
          >
        </template>
        <template #item.llm_judgments_statistic="{ item }">
          <LlmStatisticCell
            :passed="item.llm_judgments_count_passed"
            :total="item.llm_judgments_count"
          />
        </template>

        <template #header.human_judgment_passed="{ column }">
          <span>{{ column.title }}</span>
          <v-icon size="small" class="ml-1" v-tooltip:bottom="'Human judging result'"
            >mdi-help-circle-outline</v-icon
          >
        </template>
        <template #item.human_judgment_passed="{ item }">
          <v-icon
            v-if="item.human_judgment_passed !== null"
            color="green"
            icon="mdi-check-circle"
          />
          <v-icon v-else color="grey" icon="mdi-help-circle-outline" />
        </template>

        <template #header.llm_judgments_status="{ column }">
          <span>{{ column.title }}</span>
          <v-icon
            size="small"
            class="ml-1"
            v-tooltip:bottom="'Progress of LLM judging — checkmark when all judges have completed'"
            >mdi-help-circle-outline</v-icon
          >
        </template>

        <template #item.llm_judgments_status="{ item }">
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

<style scoped>
:deep(.v-data-table__tr) {
  cursor: pointer;
}

.truncate {
  display: inline-block;
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.tooltip-text {
  display: block;
  max-width: 400px;
  white-space: pre-wrap;
  word-break: break-word;
}
</style>
