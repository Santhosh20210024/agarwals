import { createApp, reactive } from "vue";
import App from "./App.vue";
import router from './router';
import resourceManager from "../../../doppio/libs/resourceManager";
import call from "../../../doppio/libs/controllers/call";
import socket from "../../../doppio/libs/controllers/socket";
import Auth from "../../../doppio/libs/controllers/auth";
import './assets/css/app.css'

import {
	FrappeUI,
	Button,
	Input,
	TextInput,
	FormControl,
	ErrorMessage,
	Dialog,
	Alert,
	Badge,
	setConfig,
	frappeRequest,
	FeatherIcon,
	ListView
  } from 'frappe-ui'


const app = createApp(App);
const auth = reactive(new Auth());

let globalComponents = {
	Button,
	TextInput,
	Input,
	FormControl,
	ErrorMessage,
	Dialog,
	Alert,
	Badge,
	FeatherIcon,
	ListView
  }

for (let key in globalComponents) {
	app.component(key, globalComponents[key])
}

setConfig('resourceFetcher', frappeRequest)

// Plugins
app.use(router);
app.use(FrappeUI);
app.use(resourceManager);

app.provide("$auth", auth);
app.provide("$call", call);
app.provide("$socket", socket);

// Configure route gaurds
router.beforeEach(async (to, from, next) => {
	if (to.matched.some((record) => !record.meta.isLoginPage)) {
		if (!auth.isLoggedIn) {
			next({ name: 'Login', query: { route: to.path } });
		} else {
			next();
		}
	} else {
		if (auth.isLoggedIn) {
			next({ name: 'Home' });
		} else {
			next();
		}
	}
});

app.mount("#app");