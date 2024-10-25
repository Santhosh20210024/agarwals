<template>
	<div class="min-h-screen bg-gray-200 flex">
	  <div class="container mx-auto my-10 bg-white p-4 drop-shadow rounded-md">
		<div class="doc flex justify-center mb-4">
		  <h1 class="text-3xl font-bold">Bill Entry</h1>
		</div>
		<div class="flex flex-col md:flex-row gap-4">
		  <div class="flex-1 p-4">
			<FormControl
			  type="text"
			  ref="billInput"
			  size="lg"
			  variant="subtle"
			  placeholder="Enter Bill"
			  :disabled="false"
			  label="Bill"
			  v-model="billValue"
			  :class="{'border-red-500': billError }"
			/>
			<span v-if="billError" class="text-red-500">{{ billError }}</span>
		  </div>
		  <div class="flex-1 p-4">
			<FormControl
			  type="text"
			  ref="claimInput"
			  size="lg"
			  variant="subtle"
			  placeholder="Enter Claim ID"
			  :disabled="false"
			  label="MA Claim ID"
			  v-model="claimValue"
			/>
		  </div>
		</div>
		<div class="flex flex-col mt-4 md:flex-row gap-4">
		  <div class="flex-1 p-4">
			<FormControl
			  type="select"
			  ref="eventInput"
			  size="lg"
			  variant="subtle"
			  placeholder="Select Event"
			  :disabled="false"
			  :required="true"
			  label="Event"
			  v-model="eventvalue"
			>
			  <option value="" disabled>Select an Event</option>
			  <option v-for="event in events" :key="event.value" :value="event.value">
				{{ event.text }}
			  </option>
			</FormControl>
		  </div>
		  <div class="flex-1 p-4">
			<FormControl
			  type="date"
			  ref="dateInput"
			  size="lg"
			  variant="subtle"
			  placeholder="Select Date"
			  :disabled="false"
			  label="Date"
			  v-model="dateValue"
			/>
		  </div>
		</div>
		<div class="flex-1 p-4">
		  <FormControl
			type="text"
			ref="remarksInput"
			size="lg"
			variant="subtle"
			placeholder="Enter Remarks"
			:disabled="false"
			label="Remarks"
			v-model="remarksValue"
		  />
		</div>
		<div class="flex justify-center mt-6">
		  <Button
			class="bg-blue-600 text-white hover:bg-blue-700 rounded px-4 py-2 mr-4"
			variant="solid"
			ref="submitButton"
			theme="blue"
			size="sm"
			label="Submit"
			:loading="loading"
			:disabled="false"
			@click = "submit"
		  >
			Submit
		  </Button>
		  <Button
			class="bg-blue-600 text-white hover:bg-blue-700 rounded px-4 py-2"
			variant="solid"
			ref="cancelButton"
			theme="blue"
			size="sm"
			label="Cancel"
			:loading="false"
			:disabled="false"
		  >
			Cancel
		  </Button>
		</div>
	  </div>
	</div>
  </template>
   
  <script setup>
  import { ref } from 'vue';
  import { FormControl, Button } from 'frappe-ui'; // Import Button if needed
   
  const billValue = ref('');
  const eventValue = ref('');
  const claimValue = ref('');
  const remarksValue = ref('');
  const dateValue = ref(null);
  const billError = ref('');
  const eventError = ref('');
   
   
  const submit = function(){
	  if (!billValue.value) {
	  billError.value = 'Bill is required.';
	  return billError;
	}
	 if (!eventValue.value) {
	  eventError.value = 'Event is required.';
	  return eventError;
	}
   
  }
  </script>
   
  <style>
  .container {
	max-width: 600px;
	width: 100%;
  }
   
  .flex-1 {
	flex: 1;
  }
   
  .p-4 {
	margin: 5px 5px;
  }
  .border-red-500 {
	border-color: #f56565;
  }
   
  @media (max-width: 640px)
	.flex {
	  flex-direction: column;
  }
  </style>