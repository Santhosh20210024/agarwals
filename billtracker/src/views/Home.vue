<template>
	<!-- Main Body -->
 <div class="w-screen h-screen flex">
	<!-- Sidebar -->
 <div class="w-[300px] h-full bg-gray-200 sidebar layout" v-show="sidebarOpen">
	<div class="h-[200px] bg-gray-900 flex justify-center items-center avatar-tag text-gray-900">
		<div class="flex flex-col items-center px-4"> <!-- Adjusted for better alignment -->
			<Avatar
				:shape="'circle'"
				:ref_for="true"
				image="https://avatars.githubusercontent.com/u/499550?s=60&v=4"
				label="EY"
				size="6xl"
			/>
			<h3 class="font-bold text-lg md:text-xl lg:text-2xl mt-2 text-center">Santhoshsivan Vallatharasu</h3>
		</div>
	</div>
	<div class="px-[50px] h-[calc(100vh-200px)] bg-white-800 py-[20px]">
		<div class=" flex flex-col justify-start items-start" @click="toggleSidebar">
			<router-link to="/list" class="inline-flex relative items-center mt-4 hover:text-blue-500 transition-all">
				<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-home">
					<path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path>
					<polyline points="9 22 9 12 15 12 15 22"></polyline>
				</svg>
				<span class="ml-2">Home</span>
			  </router-link>
			  <router-link to="/create" class="flex items-center mt-4 hover:text-blue-500 transition-all">
				<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-external-link">
					<path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path>
					<polyline points="15 3 21 3 21 9"></polyline>
					<line x1="10" y1="14" x2="21" y2="3"></line>
				</svg>
				<span class="ml-2">Create</span>
			  </router-link>
			  <router-link to="/home" class="flex items-center mt-4 hover:text-blue-500 transition-all">
				<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-external-link">
					<path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path>
					<polyline points="15 3 21 3 21 9"></polyline>
					<line x1="10" y1="14" x2="21" y2="3"></line>
				</svg>
				<span class="ml-2">Invoice</span>
			  </router-link>
			  <router-link to="/home" class="flex items-start mt-4 hover:text-blue-500 transition-all">
				<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-pie-chart"><path d="M21.21 15.89A10 10 0 1 1 8 2.83"></path><path d="M22 12A10 10 0 0 0 12 2v10z"></path></svg>
				<span class="ml-2">Charts</span>
			  </router-link>
			  <router-link to="/home" class="flex items-start mt-4 hover:text-blue-500 transition-all">
				<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-settings">
					<circle cx="12" cy="12" r="3"></circle>
					<path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path>
				</svg>
				<span class="ml-2">Settings</span>
			  </router-link>
		</div>
		</div>
 </div>
 <!-- Sidebar Ends -->
 <div class="w-full h-full bg-gray-400">
	<div class="h-[50px] bg-gray-300 mb-1 flex items-center shadow-sm px-[20px] w-full py-[10px] z-10 border-b">
		<!-- Humburger -->
		<div class="menu-toggle-wrap cursor-pointer w-[30px]" @click="toggleSidebar">
			<svg class="feather feather-menu" fill="none" height="24" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" viewBox="0 0 24 24" width="24" xmlns="http://www.w3.org/2000/svg"><line x1="3" x2="21" y1="12" y2="12"/><line x1="3" x2="21" y1="6" y2="6"/><line x1="3" x2="21" y1="18" y2="18"/></svg>
		</div>
		<!-- SearchBar -->
		<div
		class="flex-grow flex justify-center px-5"
		variant="outline"
	  	>
		  <TextInput type="text" placeholder="Enter Bill No" size="md" variant="outline">
			<template #prefix>
			  <FeatherIcon
				class="w-4"
				name="search"
			  />
			</template>
		  </TextInput>
	  </div>
	</div>
	<div class="h-[calc(100vh-50px)] bg-white">
		<div class="border rounded-md p-[20px] h-full">
			<router-view></router-view>
		</div>
		</div>
	</div>
 </div>
</template>

<script setup>
import { ref } from 'vue';
import { createResource } from 'frappe-ui'
import Avatar from 'frappe-ui/src/components/Avatar.vue';

const sidebarOpen = ref(false); 
function toggleSidebar(){
	sidebarOpen.value = !sidebarOpen.value;
}

let username = createResource({
	url: 'agarwals.api.get_user_name',
})
username.fetch()
console.log(username)
</script>

<style lang="scss" scoped>
.avatar-tag{
	background-color: rgb(156, 211, 253);;
}

.layout{
	transition: 1s ease-in-out;
}

</style>