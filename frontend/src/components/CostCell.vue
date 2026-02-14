<script setup lang="ts">
import { formatCost } from "@/utils/format"

defineProps<{
  cost?: number | null
}>()
</script>

<template>
  {{ formatCost(cost) }}
</template>
