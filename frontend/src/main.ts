import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'

import App from './App.vue'
import router from './router'
import './style.css'
import { bootDesktopHttpBase } from '@/config/backendOrigin'

async function bootstrap() {
  await bootDesktopHttpBase()
  const app = createApp(App)
  app.use(createPinia())
  app.use(router)
  app.use(ElementPlus)
  app.mount('#app')
}

void bootstrap()
