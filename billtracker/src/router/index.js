import { createRouter, createWebHistory } from "vue-router";
import Home from "../views/Home.vue";
import CreateBillEntry from '../components/CreateBillEntry.vue'
import ListView from "frappe-ui/src/components/ListView/ListView.vue";
import authRoutes from './auth';

const routes = [
  {
	path: "/",
	name: "Home",
	component: Home,
  redirect: "/list",
  children:[
    {
      path: "/create",
      name: "CreateBillEntry",
      component: CreateBillEntry,
    },
    {
      path: "/list",
      name: "List",
      component: ListView,
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