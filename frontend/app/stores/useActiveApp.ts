import { ref } from "vue"
import { getApp, type AppSchema } from "@/api/generated"

const activeApplication = ref<AppSchema>()

export function useActiveApp() {
  function setApp(app: AppSchema) {
    activeApplication.value = app
  }

  async function loadApp(id: number) {
    if (activeApplication.value?.id === id) return
    const res = await getApp(id)
    if (res.status === 200) {
      activeApplication.value = res.data
    }
  }

  function clearApp() {
    activeApplication.value = undefined
  }

  return { activeApp: activeApplication, setApp, loadApp, clearApp }
}
