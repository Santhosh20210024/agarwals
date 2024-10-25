import { createRouter, createWebHistory } from "vue-router";
import Home from "../views/Home.vue";
import List from "../views/List.vue"
import authRoutes from './auth';

const routes = [
  {
	path: "/",
	name: "Home",
	component: Home,
  children:[
    {
      path: "/list",
      name: "List",
      component: List,
    }
  ]
  },
  ...authRoutes,
];

const router = createRouter({
  base: "/billtracker/",
  history: createWebHistory(),
  routes,
});

export default router;
