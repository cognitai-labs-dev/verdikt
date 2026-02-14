<script setup lang="ts">
import { formatCost } from "@/utils/format"

defineProps<{
  question: string
  humanAnswer: string
  appAnswer: string
  appCost?: number | null
  totalCost: number
}>()
</script>

<template>
  <v-card class="mb-4">
    <v-card-title class="text-subtitle-1 font-weight-bold">Question</v-card-title>
    <v-card-text class="text-body-1" style="white-space: pre-wrap">{{ question }}</v-card-text>
  </v-card>

  <v-card class="mb-4 golden-standard">
    <v-card-title class="text-subtitle-1 font-weight-bold d-flex align-center">
      Human answer
      <v-chip size="x-small" color="amber-darken-2" variant="tonal" class="ml-2"
        >Golden standard</v-chip
      >
    </v-card-title>
    <v-card-text class="text-body-1" style="white-space: pre-wrap">{{ humanAnswer }}</v-card-text>
  </v-card>

  <v-card class="mb-4">
    <v-card-title class="text-subtitle-1 font-weight-bold">App answer</v-card-title>
    <v-card-text class="text-body-1" style="white-space: pre-wrap">{{ appAnswer }}</v-card-text>
  </v-card>

  <v-card class="mb-4">
    <v-card-text class="d-flex align-center">
      <v-icon size="small" class="mr-2" color="secondary">mdi-currency-usd</v-icon>
      <span class="font-weight-medium">App Cost:</span>
      <span class="ml-2 mr-4">{{ formatCost(appCost) }}</span>
      <span class="font-weight-medium">Total cost:</span>
      <span class="ml-2">{{ formatCost(totalCost) }}</span>
    </v-card-text>
  </v-card>
</template>

<style scoped>
.golden-standard {
  border: 2px solid #d4a000;
  background: linear-gradient(135deg, rgba(255, 215, 0, 0.08) 0%, rgba(255, 193, 7, 0.12) 100%);
}
</style>
