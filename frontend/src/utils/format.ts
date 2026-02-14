export function getLlmPercentage(passed: number, total: number): string {
  if (total === 0) return "N/A"
  return `${Math.round((passed / total) * 100)}%`
}

export function formatDate(dateStr: string | null | undefined): string {
  if (!dateStr) return "N/A"
  const date = new Date(dateStr)
  return date.toLocaleString("en-GB", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  })
}

export function formatCost(cost: number | null | undefined): string {
  if (cost === 0.0) return `$0.0`
  if (cost === null || cost === undefined) return "N/A"
  return `$${cost.toFixed(5)}`
}
