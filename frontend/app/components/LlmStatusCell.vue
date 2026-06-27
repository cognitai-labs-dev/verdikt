<script setup lang="ts">
import { getLlmPercentage } from "@/utils/format"
import { computed } from "vue"

const props = defineProps<{
  countCompleted: number
  count: number
}>()

const completed = computed(() => props.count === props.countCompleted)
</script>

<template>
  <v-icon v-if="completed" color="green" icon="mdi-check-circle" />
  <div v-else>{{ getLlmPercentage(countCompleted, count) }} | {{ countCompleted }}/{{ count }}</div>
</template>
