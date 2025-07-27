import { createApp } from 'vue'
import App from './App.vue'
import { createRouter, createWebHistory } from 'vue-router'

// Import views
import Home from './views/Home.vue'
import Watchlist from './views/Watchlist.vue'

const routes = [
  { path: '/', component: Home },
  { path: '/watchlist', component: Watchlist }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

const app = createApp(App)
app.use(router)
app.mount('#app')
