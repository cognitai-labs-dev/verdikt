import { computed, ref } from "vue"
import { getMe, type MeResponse } from "@/api/generated"

// Shared identity of the logged-in principal, fetched from /v1/me. Used to
// decide whether to surface admin-only UI. The API (require_admin) is the real
// security boundary — this gate is UX only.
const me = ref<MeResponse>()
const loaded = ref(false)

export function useMe() {
  async function loadMe() {
    if (loaded.value) return
    const res = await getMe()
    if (res.status === 200) {
      me.value = res.data
    }
    loaded.value = true
  }

  const isAdmin = computed(() => me.value?.is_admin ?? false)

  return { me, isAdmin, loadMe }
}
