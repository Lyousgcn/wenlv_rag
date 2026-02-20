import { createRouter, createWebHistory } from "vue-router";
import { useAuthStore } from "../stores/auth";

const Login = () => import("../views/Login.vue");
const Register = () => import("../views/Register.vue");
const ChatLayout = () => import("../views/ChatLayout.vue");
const KnowledgeParse = () => import("../views/KnowledgeParse.vue");
const KnowledgePreview = () => import("../views/KnowledgePreview.vue");
const KnowledgeManage = () => import("../views/KnowledgeManage.vue");

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/login", name: "login", component: Login },
    { path: "/register", name: "register", component: Register },
    { path: "/", name: "chat", component: ChatLayout },
    {
      path: "/knowledge/parse",
      name: "knowledge-parse",
      component: KnowledgeParse
    },
    {
      path: "/knowledge/preview/:docId",
      name: "knowledge-preview",
      component: KnowledgePreview,
      props: true
    },
    {
      path: "/knowledge/manage",
      name: "knowledge-manage",
      component: KnowledgeManage
    }
  ]
});

router.beforeEach((to, from, next) => {
  const auth = useAuthStore();
  if (!auth.token && to.name !== "login" && to.name !== "register") {
    next({ name: "login" });
  } else if (auth.token && (to.name === "login" || to.name === "register")) {
    next({ name: "chat" });
  } else {
    next();
  }
});

export default router;
