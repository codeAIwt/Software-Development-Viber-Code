import { createRouter, createWebHistory } from "vue-router";
import { getToken } from "../utils/auth";

const routes = [
  { path: "/", redirect: "/home" },
  {
    path: "/login",
    name: "login",
    component: () => import("../views/Login.vue"),
    meta: { public: true },
  },
  {
    path: "/register",
    name: "register",
    component: () => import("../views/Register.vue"),
    meta: { public: true },
  },
  {
    path: "/home",
    name: "home",
    component: () => import("../views/Home.vue"),
    meta: { requiresAuth: true },
  },
  {
    path: "/personal",
    name: "personal",
    component: () => import("../views/Personal.vue"),
    meta: { requiresAuth: true },
  },
  {
    path: "/study-room",
    name: "study-room",
    component: () => import("../views/StudyRoom.vue"),
    meta: { requiresAuth: true },
  },
  {
    path: "/study-room/:id",
    name: "study-room-detail",
    component: () => import("../views/StudyRoomDetail.vue"),
    meta: { requiresAuth: true },
  },
  {
    path: "/tags",
    name: "tags",
    component: () => import("../views/Tags.vue"),
    meta: { requiresAuth: true },
  },
  {
    path: "/rank",
    name: "rank",
    component: () => import("../views/Rank.vue"),
    meta: { requiresAuth: true },
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

router.beforeEach((to) => {
  if (to.meta.requiresAuth && !getToken()) {
    return { path: "/login", query: { redirect: to.fullPath } };
  }
  return true;
});

export default router;