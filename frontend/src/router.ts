import { createRouter, createWebHistory } from "vue-router"
import EvaluationsView from "./views/EvaluationsView.vue"
import SamplesView from "./views/SamplesView.vue"
import SampleDetailView from "./views/SampleDetailView.vue"
import AppsView from "./views/AppsView.vue"
import AppDetailView from "./views/AppDetailView.vue"
import JudgingView from "./views/JudgingView.vue"

const routes = [
  { path: "/", component: AppsView, name: "Apps" },
  { path: "/app/:id/detail", component: AppDetailView, name: "Apps detail", props: true },
  { path: "/app/:id/evaluations", component: EvaluationsView, name: "Evaluations", props: true },
  {
    path: "/evaluation/:id/samples",
    component: SamplesView,
    name: "Evaluation Samples",
    props: true,
  },
  {
    path: "/evaluation/:id/judging",
    component: JudgingView,
    name: "Judging",
    props: true,
  },
  { path: "/sample/:id/detail", component: SampleDetailView, name: "Sample Detail", props: true },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
