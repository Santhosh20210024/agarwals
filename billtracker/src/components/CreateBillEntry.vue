<template>
    <div class="min-h-screen bg-gray-200 flex">
      <div class="container mx-auto my-10 bg-white p-4 drop-shadow rounded-md">
        <div class="doc flex justify-center mb-4">
          <h1 class="text-3xl font-bold">Bill Entry</h1>
        </div>
        <div class="flex flex-col md:flex-row gap-4">
          <div class="flex-1 p-3">
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
          <div class="flex-1 p-3">
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
          <div class="flex-1 p-3">
            <FormControl
              type="select"
              ref="eventInput"
              size="lg"
              variant="subtle"
              placeholder="Select Event"
              :disabled="false"
              :options = "events"
              label="Event"
              v-model="eventValue"
              :class="{'border-red-500': eventError }"
            />
            <span v-if="eventError" class="text-red-500">{{ eventError }}</span>
          </div>
          <div class="flex-1 p-3">
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
        <div class="flex-1 p-3">
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
            :loading="false"
            :disabled="false"
            @click="submitForm"
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
            @click="cancelForm"
          >
            Cancel
          </Button>
        </div>
      </div>
    </div>
  </template>
   
  <script setup>
  import { ref } from 'vue';
  import { FormControl, Button,createListResource } from 'frappe-ui';
  import { useRouter } from 'vue-router';
   
  const router = useRouter();
  const billValue = ref('');
  const eventValue = ref('');
  const claimValue = ref('');
  const remarksValue = ref('');
  const dateValue = ref(null);
  const billError = ref('');
  const eventError = ref('');
   
  const submitForm = () => {
    billError.value = '';
    eventError.value = '';
    let isValid = true;
   
    if (!billValue.value) {
      billError.value = 'Bill is required.';
      isValid = false;
    }
   
    if (!eventValue.value) {
      eventError.value = 'Event is required.';
      isValid = true;
    }
   
    if (!isValid) {
      return;
    }
    const formData = {
      bill: billValue.value,
      ma_claim_id: claimValue.value,
      events: eventValue.value,
      date: dateValue.value,
      remarks: remarksValue.value,
    };
  //   try {
  //     const response = await fetch('http://127.0.0.1:8002/api/create_bills', {
  //       method: 'POST',
  //       headers: {
  //         'Content-Type': 'application/json',
  //       },
  //       body: JSON.stringify(formData),
  //     });
   
  //     if (!response.ok) {
  //       throw new Error('Network response was not ok');
  //     }
   
  //     const data = await response.json();
  //     console.log('Success:', data);
   
  //   } catch (error) {
  //     console.error('Error:', error);
  //   }
    console.log('Bill:', billValue.value);
    console.log('Event:', eventValue.value);
  };
   
   
  const cancelForm = () => {
    billValue.value = '';
    claimValue.value = '';
    eventValue.value = '';
    dateValue.value = null;
    remarksValue.value = '';
   
    router.push({ name: 'Home' });
  };
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
   
  @media (max-width: 640px) {
    .flex {
      flex-direction: column;
    }
  }
  </style>
   
  has context menu