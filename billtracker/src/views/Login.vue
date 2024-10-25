<template>
  <div class="min-h-screen bg-gray-100 flex sm:p-6 md:p-8 lg:p-10 xl:p-12">
    <div class="mx-auto w-full max-w-sm lg:w-112 my-auto bg-white p-4 drop-shadow rounded-md" :class="{ shake: shakeEffect }">
      <div class="text-center mb-2 pb-3 text-lg font-medium">
        <img src="../img/logo.svg" width="100px" alt="Logo" class="mx-auto py-6" />
        Login to Bill Tracker
      </div>
     
      <form @submit.prevent="login" class="space-y-6 mx-auto py-2">
        <div class="form-group">
          <FormControl
            id="email"
            type="text"
            v-model="email"
            :required="true"
            size="md"
            placeholder="jane@example.com"
            variant="subtle"
            :class="{ warningClass: wrongInput }"
          >
          <template #prefix>
          <FeatherIcon
                class="w-4"
                name="mail"
              />
          </template>
          </FormControl>
        </div>

        <div class="form-group">
          <FormControl
            id="password"
            type="password"
            v-model="password"
            :required="true"
            size="md"
            placeholder="Password"
            :class="{ warningClass: wrongInput }"
          >
          <template #prefix>
          <FeatherIcon
              class="w-4"
              name="lock"
              />
          </template>
          </FormControl>
        </div>

        <p class="text-2xs font-light text-right mx-5">
          <a href="#">Forgot password?</a>
        </p>

        <div class="flex justify-center pb-4">
          <Button
            variant="solid"
            theme="blue"
            size="sm"
            :label="label"
            :loading="loading"
            loadingText="Verifying"
            :disabled="loading"
            class="w-80"
            type="submit"
          />
        </div>
      </form>
    </div>
  </div>
</template>

<script>
import { FormControl,FeatherIcon, Button } from 'frappe-ui';

export default {
  components: {
    FormControl,
    FeatherIcon,
    Button,
  },

  data() {
    return {
      email: '',            
      password: '',        
      redirectRoute: null,  
      wrongInput: false,    
      loading: false,      
      label: "Login",      
      shakeEffect: false,
    };
  },

  inject: ["$auth"],  

  async mounted() {
   
    const routeQuery = this.$route?.query?.route;
    if (routeQuery) {
      this.redirectRoute = routeQuery;
      this.$router.replace({ query: null });  
    }
  },

  methods: {
    async login() {
      try {
          this.loading = true;  
        if (this.email && this.password) {  
          const response = await this.$auth.login(this.email, this.password);
          if (response) {
            this.$router.push({ name: "Home" });  
          }
        }
      } catch (error) {
        this.handleLoginError();  
      } finally {
        this.loading = false;  
      }
    },

    handleLoginError() {
      this.wrongInput = true;          
      this.label = "Invalid Login. Try Again";
      this.shakeEffect = true;          
      setTimeout(() => {
        this.shakeEffect = false;      
      }, 1500);
    },
  },
};
</script>


<style scoped>
.form-group {
  margin: 0 auto;
  padding: 0 0.75rem;
}

.warningClass {
  border: 1px solid red;
  border-radius: 8px;
}

.shake {
  animation: shake 0.82s cubic-bezier(0.36, 0.07, 0.19, 0.97) both;
  transform: translate3d(0, 0, 0);
}

@keyframes shake {
  10%, 90% { transform: translate3d(-1px, 0, 0); }
  20%, 80% { transform: translate3d(2px, 0, 0); }
  30%, 50%, 70% { transform: translate3d(-4px, 0, 0); }
  40%, 60% { transform: translate3d(4px, 0, 0); }
}
</style>