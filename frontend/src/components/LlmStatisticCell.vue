<script setup lang="ts">
import { getLlmPercentage } from "@/utils/format"

defineProps<{
  passed: number
  total: number
}>()
</script>

<template>{{ getLlmPercentage(passed, total) }} | {{ passed }}/{{ total }}</template>
