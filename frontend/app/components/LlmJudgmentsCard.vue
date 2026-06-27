<script setup lang="ts">
import { EvaluationType, type JudgmentSchema } from "@/api/generated"
import { formatCost, getLlmPercentage } from "@/utils/format"
import { computed } from "vue"

const props = defineProps<{
  judgments: JudgmentSchema[]
  completed: number
  total: number
  passed: number
  evaluationType: EvaluationType
}>()

const passedString = computed(() =>
  EvaluationType.LLM_ONLY === props.evaluationType ? "Passed" : "Matched",
)
</script>

<template>
  <v-card>
    <v-card-title class="d-flex align-center">
      <v-icon size="small" class="mr-2" color="secondary">mdi-robot</v-icon>
      LLM Judgments
      <span class="text-caption text-medium-emphasis ml-2"
        >({{ completed }}/{{ total }} completed)</span
      >
      <v-spacer />
      <v-chip variant="tonal" color="primary" size="default" class="font-weight-bold">
        {{ passedString }}: {{ getLlmPercentage(passed, total) }} | {{ passed }}/{{ total }}
      </v-chip>
    </v-card-title>
    <v-card-text>
      <v-expansion-panels v-if="judgments.length > 0 && props.completed > 0" variant="accordion">
        <v-expansion-panel v-for="judgment in judgments" :key="judgment.id">
          <v-expansion-panel-title>
            <div class="d-flex align-center" style="width: 100%">
              <span class="font-weight-medium">{{ judgment.judgment_model }}</span>
              <v-spacer />
              <v-icon v-if="judgment.passed" color="green" icon="mdi-check-circle" size="small" />
              <v-icon
                v-else-if="judgment.passed === false"
                color="red"
                icon="mdi-close-circle"
                size="small"
              />
              <v-icon v-else color="grey" icon="mdi-help-circle-outline" size="small" />
            </div>
          </v-expansion-panel-title>
          <v-expansion-panel-text>
            <div class="mb-3">
              <div class="text-subtitle-2 font-weight-bold mb-1">Reasoning</div>
              <div class="text-body-2" style="white-space: pre-wrap">
                {{ judgment.reasoning ?? "No reasoning provided or not judged yet" }}
              </div>
            </div>

            <v-divider class="my-3" />

            <div class="text-subtitle-2 font-weight-bold mb-2">Cost Details</div>
            <v-table density="compact">
              <tbody>
                <tr>
                  <td class="text-medium-emphasis">Input Tokens</td>
                  <td>{{ judgment.input_tokens ?? "N/A" }}</td>
                </tr>
                <tr>
                  <td class="text-medium-emphasis">Output Tokens</td>
                  <td>{{ judgment.output_tokens ?? "N/A" }}</td>
                </tr>
                <tr>
                  <td class="text-medium-emphasis">Input Cost</td>
                  <td>{{ formatCost(judgment.input_tokens_cost) }}</td>
                </tr>
                <tr>
                  <td class="text-medium-emphasis">Output Cost</td>
                  <td>{{ formatCost(judgment.output_tokens_cost) }}</td>
                </tr>
              </tbody>
            </v-table>
          </v-expansion-panel-text>
        </v-expansion-panel>
      </v-expansion-panels>
      <div v-else class="text-medium-emphasis text-body-2 pa-2">No LLM judgments available yet</div>
    </v-card-text>
  </v-card>
</template>
