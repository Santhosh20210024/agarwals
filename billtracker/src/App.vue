<template>
	<div>
		<!-- <button v-if="$auth.isLoggedIn" @click="$auth.logout()">Logout</button> -->
		<!-- <Sidebar /> -->
		<router-view />
	</div>
</template>


<script>
import Sidebar from './views/Home.vue';
export default {
	inject: ['$auth'],
	components: {
    Sidebar,
	}
};
</script>

<style>
:root {
    --primary: #4ade80;
    --primary-alt: #22c55e;
    --grey: #64748b;
    --dark: #1e293b;
    --dark-alt: #334155;
    --light: #f1f5f9;
    --sidebar-width: 300px;
}

* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
    font-family: 'Fira Sans', sans-serif;
}

body {
    background: var(--light);
}

button {
    cursor: pointer;
    appearance: none;
    border: none;
    outline: none;
    background: none;
}

.app {
    display: flex;
}

.app main {
    flex: 1 1 0;
    padding: 2rem;
}

@media (max-width: 1024px) {
    .app main {
        padding-left: 6rem;
    }
}
</style>