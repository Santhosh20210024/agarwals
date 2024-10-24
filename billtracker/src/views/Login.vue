<!-- <template>
  <div class="min-h-screen bg-white flex">
	<div class="mx-auto w-full max-w-sm lg:w-96">
	  <form @submit.prevent="login" class="space-y-6">
		<label for="email"> Username: </label>
		<input type="text" v-model="email" />
		<br />
		<label for="password"> Password: </label>
		<input type="password" v-model="password" />

		<button
		  class="bg-blue-500 block text-white p-2 hover:bg-blue-700"
		  type="submit"
		>
		  Sign in
		</button>
	  </form>
	</div>
  </div>
</template>
<script>
export default {
  data() {
	return {
	  email: null,
	  password: null,
	};
  },
  inject: ["$auth"],
  async mounted() {
	if (this.$route?.query?.route) {
	  this.redirect_route = this.$route.query.route;
	  this.$router.replace({ query: null });
	}
  },
  methods: {
	async login() {
	  if (this.email && this.password) {
		let res = await this.$auth.login(this.email, this.password);
		if (res) {
		  this.$router.push({ name: "Home" });
		}
	  }
	},
  },
};
</script> -->
vue
<template>
  <div class="login-container">
    <div class="login-card">
       <img src="./assets/agarwals/billtracker/vite.svg" alt="Logo" class="logo" /> 
      <h2>Login to Agarwals-Claimgenie</h2>
      <form @submit.prevent="login">
        <div class="input-group">
          <label for="email">Email</label>
          <input
            type="email"
            id="email"
            v-model="email"
            placeholder="jane@example.com"
            required
          />
        </div>
        <div class="input-group">
          <label for="password">Password</label>
          <div class="password-group">
            <input
              type="password"
              id="password"
              v-model="password"
              required
            />
            <button type="button" @click="togglePasswordVisibility">
              {{ showPassword ? 'Hide' : 'Show' }}
            </button>
          </div>
        </div>
        <button type="submit" class="login-button">Login</button>
      </form>
      <a href="#" class="forgot-password">Forgot Password?</a>
    </div>
  </div>
</template>
 
<script>
export default {
  data() {
	return {
	  email: null,
	  password: null,
	};
  },
  inject: ["$auth"],
  async mounted() {
	if (this.$route?.query?.route) {
	  this.redirect_route = this.$route.query.route;
	  this.$router.replace({ query: null });
	}
  },
  methods: {
	async login() {
	  if (this.email && this.password) {
		let res = await this.$auth.login(this.email, this.password);
		if (res) {
		  this.$router.push({ name: "Home" });
		}
	  }
	},},}</script>
 
<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  background-color: #f5f5f5;
}
 
.login-card {
  background: white;
  padding: 30px;
  border-radius: 10px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  width: 300px;
  text-align: center;
}
 
.logo {
  width: 50px; /* Adjust according to your logo size */
  margin-bottom: 20px;
}
 
.input-group {
  margin-bottom: 15px;
  text-align: left;
}
 
.password-group {
  display: flex;
  align-items: center;
}
 
.password-group input {
  flex: 1;
}
 
.login-button {
  background-color: #007bff;
  color: white;
  border: none;
  padding: 10px;
  border-radius: 5px;
  cursor: pointer;
  width: 100%;
}
 
.login-button:hover {
  background-color: #0056b3;
}
 
.forgot-password {
  display: block;
  margin-top: 10px;
  color: #007bff;
}
</style>
 











