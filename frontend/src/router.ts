import { createRouter, createWebHistory } from "vue-router"
import EvaluationsView from "./views/EvaluationsView.vue"
import SamplesView from "./views/SamplesView.vue"
import SampleDetailView from "./views/SampleDetailView.vue"
import AppsView from "./views/AppsView.vue"
import AppDetailView from "./views/AppDetailView.vue"
import JudgingView from "./views/JudgingView.vue"
import zitadelAuth from "./services/zitadelAuth"

const routes = [
  {
    path: "/",
    component: AppsView,
    name: "Apps",
    meta: { authName: zitadelAuth.oidcAuth.authName },
  },
  {
    path: "/app/:id/detail",
    component: AppDetailView,
    name: "Apps detail",
    props: true,
    meta: { authName: zitadelAuth.oidcAuth.authName },
  },
  {
    path: "/app/:id/evaluations",
    component: EvaluationsView,
    name: "Evaluations",
    props: true,
    meta: { authName: zitadelAuth.oidcAuth.authName },
  },
  {
    path: "/evaluation/:id/samples",
    component: SamplesView,
    name: "Evaluation Samples",
    props: true,
    meta: { authName: zitadelAuth.oidcAuth.authName },
  },
  {
    path: "/evaluation/:id/judging",
    component: JudgingView,
    name: "Judging",
    props: true,
    meta: { authName: zitadelAuth.oidcAuth.authName },
  },
  {
    path: "/sample/:id/detail",
    component: SampleDetailView,
    name: "Sample Detail",
    props: true,
    meta: { authName: zitadelAuth.oidcAuth.authName },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

zitadelAuth.oidcAuth.useRouter(router)

export default router
