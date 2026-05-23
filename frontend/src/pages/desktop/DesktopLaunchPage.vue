<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { resolveDesktopHealthContext } from '@/config/backendOrigin'
import type { DesktopRuntimeConfig } from '@/desktop/desktopRuntime'
import {
  type HealthPayload,
  canProceedWhileDegraded,
  fetchHealthPayload,
  resolveDesktopLaunchPhase,
} from '@/desktop/healthGate'

const router = useRouter()
const healthUrl = ref('')
const desktopConfig = ref<DesktopRuntimeConfig | null>(null)
const spawnError = ref<string | null>(null)

const isChecking = ref(true)
const health = ref<HealthPayload | null>(null)
const connectionFailed = ref(false)

const phase = computed(() => {
  if (spawnError.value) return 'error'
  return resolveDesktopLaunchPhase({
    isChecking: isChecking.value,
    health: health.value,
    connectionFailed: connectionFailed.value,
  })
})

const sidecarStartingHint = computed(
  () =>
    desktopConfig.value?.manage_sidecar &&
    !spawnError.value &&
    healthUrl.value &&
    phase.value === 'loading',
)

async function runCheck() {
  isChecking.value = true
  connectionFailed.value = false
  health.value = null
  const url = healthUrl.value
  if (!url) {
    isChecking.value = false
    connectionFailed.value = true
    return
  }

  const pauseMs = 400
  const maxAttempts = desktopConfig.value?.manage_sidecar ? 200 : 90
  let lastFailed = true
  let lastHealth: HealthPayload | null = null

  for (let i = 0; i < maxAttempts; i++) {
    const r = await fetchHealthPayload(url)
    lastFailed = r.connectionFailed
    lastHealth = r.health
    if (!r.connectionFailed && r.health) {
      health.value = r.health
      const ph = resolveDesktopLaunchPhase({
        isChecking: false,
        health: r.health,
        connectionFailed: false,
      })
      if (ph === 'loading') {
        connectionFailed.value = false
        if (i < maxAttempts - 1) {
          await new Promise((res) => setTimeout(res, pauseMs))
        }
        continue
      }
      connectionFailed.value = false
      isChecking.value = false
      if (ph === 'ready') {
        void router.replace({ name: 'login' })
      }
      return
    }
    if (i < maxAttempts - 1) {
      await new Promise((res) => setTimeout(res, pauseMs))
    }
  }
  connectionFailed.value = lastFailed
  health.value = lastHealth
  isChecking.value = false
}

function proceedDegraded() {
  if (health.value && canProceedWhileDegraded(health.value)) {
    void router.replace({ name: 'login' })
  }
}

onMounted(async () => {
  const ctx = await resolveDesktopHealthContext()
  desktopConfig.value = ctx.desktop
  if (ctx.spawnError) {
    spawnError.value = ctx.spawnError
    const o = ctx.desktop?.backend_origin?.replace(/\/$/, '') ?? ''
    healthUrl.value = o ? `${o}/health` : ''
    isChecking.value = false
    return
  }
  spawnError.value = null
  healthUrl.value = ctx.healthUrl
  void runCheck()
})
</script>

<template>
  <div class="dl-wrap">
    <div class="dl-card">
      <h1 class="dl-title">intelliOffice</h1>
      <p class="dl-sub">桌面启动（D2 健康门；D3 sidecar；D4 数据库生命周期）</p>

      <ul v-if="desktopConfig" class="dl-meta">
        <li>
          <span class="dl-k">backend_origin:</span> {{ desktopConfig.backend_origin || '（空 = Vite 代理 / 相对路径）' }}
        </li>
        <li><span class="dl-k">manage_sidecar:</span> {{ desktopConfig.manage_sidecar }}</li>
        <li><span class="dl-k">sidecar_port:</span> {{ desktopConfig.sidecar_port }}</li>
        <li v-if="desktopConfig.sidecar_pid != null">
          <span class="dl-k">sidecar_pid:</span> {{ desktopConfig.sidecar_pid }}
        </li>
      </ul>

      <template v-if="phase === 'loading'">
        <p class="dl-msg">正在连接后端并检查 /health …</p>
        <p v-if="health?.database_lifecycle_phase" class="dl-hint">
          数据库阶段：<strong>{{ health.database_lifecycle_phase }}</strong>
          <span v-if="health.migration_pending">（待迁移）</span>
          <span v-if="health.database_lifecycle_detail"> — {{ health.database_lifecycle_detail }}</span>
        </p>
        <p
          v-if="health && (health.alembic_current_revision != null || health.alembic_head_revision != null)"
          class="dl-hint dl-mono"
        >
          Alembic：{{ health.alembic_current_revision ?? '（无）' }} → {{ health.alembic_head_revision ?? '—' }}
        </p>
        <p v-if="sidecarStartingHint" class="dl-hint">
          已请求由桌面壳启动后端 sidecar（PyInstaller 产物）；若首次启动较慢，将自动重试片刻。
        </p>
        <p class="dl-url">{{ healthUrl || '—' }}</p>
      </template>

      <template v-else-if="phase === 'ready'">
        <p class="dl-msg">后端就绪，正在进入应用…</p>
      </template>

      <template v-else-if="phase === 'degraded' && health">
        <p class="dl-warn">后端处于 degraded 状态（未完全就绪）。</p>
        <p v-if="health.database_lifecycle_phase" class="dl-hint">
          数据库阶段：{{ health.database_lifecycle_phase }}
          <span v-if="health.migration_pending"> — 请在开发环境执行 <code>alembic upgrade head</code></span>
        </p>
        <ul class="dl-facts">
          <li>database_lifecycle_phase: {{ health.database_lifecycle_phase }}</li>
          <li>migration_pending: {{ health.migration_pending }}</li>
          <li>status: {{ health.status }}</li>
          <li>runtime_mode: {{ health.runtime_mode }}</li>
          <li>bootstrap_status: {{ health.bootstrap_status }}</li>
          <li>database_status: {{ health.database_status }}</li>
          <li>version: {{ health.version }}</li>
        </ul>
        <p v-if="health.errors?.length" class="dl-err">
          {{ health.errors.join('；') }}
        </p>
        <p v-if="canProceedWhileDegraded(health)" class="dl-hint">
          当前为 development 模式：允许在知晓风险的前提下继续进入应用。
        </p>
        <div class="dl-actions">
          <button type="button" class="dl-btn" @click="runCheck">重试检查</button>
          <button v-if="canProceedWhileDegraded(health)" type="button" class="dl-btn primary" @click="proceedDegraded">
            仍要继续
          </button>
        </div>
      </template>

      <template v-else>
        <p class="dl-err">无法就绪：后端不可用、sidecar 启动失败或 /health 不符合契约。</p>
        <p v-if="spawnError" class="dl-err dl-strong">{{ spawnError }}</p>
        <ul v-if="health" class="dl-facts">
          <li>database_lifecycle_phase: {{ health.database_lifecycle_phase }}</li>
          <li>migration_pending: {{ health.migration_pending }}</li>
          <li>status: {{ health.status }}</li>
          <li>runtime_mode: {{ health.runtime_mode }}</li>
          <li>bootstrap_status: {{ health.bootstrap_status }}</li>
          <li>database_status: {{ health.database_status }}</li>
          <li>version: {{ health.version }}</li>
        </ul>
        <p v-if="health?.errors?.length" class="dl-err">
          {{ health.errors.join('；') }}
        </p>
        <p class="dl-url">{{ healthUrl || '—' }}</p>
        <div class="dl-actions">
          <button type="button" class="dl-btn primary" @click="runCheck">重试</button>
        </div>
      </template>
    </div>
  </div>
</template>

<style scoped>
.dl-wrap {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #0f1419;
  color: #e6edf3;
  font-family: system-ui, sans-serif;
  padding: 1rem;
}
.dl-card {
  max-width: 36rem;
  width: 100%;
  background: #161b22;
  border: 1px solid #30363d;
  border-radius: 8px;
  padding: 1.5rem;
}
.dl-title {
  margin: 0 0 0.25rem;
  font-size: 1.35rem;
  font-weight: 600;
}
.dl-sub {
  margin: 0 0 1rem;
  color: #8b949e;
  font-size: 0.9rem;
}
.dl-meta {
  list-style: none;
  margin: 0 0 1rem;
  padding: 0;
  font-size: 0.78rem;
  color: #8b949e;
  word-break: break-all;
}
.dl-meta li {
  margin: 0.2rem 0;
}
.dl-k {
  color: #6e7681;
  margin-right: 0.35rem;
}
.dl-msg {
  margin: 0.5rem 0;
}
.dl-warn {
  margin: 0.5rem 0;
  color: #d29922;
}
.dl-err {
  margin: 0.5rem 0;
  color: #f85149;
  word-break: break-word;
}
.dl-strong {
  font-weight: 600;
}
.dl-hint {
  margin: 0.75rem 0 0;
  color: #8b949e;
  font-size: 0.9rem;
}
.dl-mono {
  font-family: ui-monospace, monospace;
  font-size: 0.78rem;
}
.dl-url {
  font-size: 0.75rem;
  color: #8b949e;
  word-break: break-all;
  margin: 0.75rem 0 0;
}
.dl-facts {
  margin: 0.5rem 0 0;
  padding-left: 1.2rem;
  color: #c9d1d9;
  font-size: 0.9rem;
}
.dl-actions {
  margin-top: 1rem;
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}
.dl-btn {
  padding: 0.45rem 0.9rem;
  border-radius: 6px;
  border: 1px solid #30363d;
  background: #21262d;
  color: #e6edf3;
  cursor: pointer;
}
.dl-btn:hover {
  background: #30363d;
}
.dl-btn.primary {
  background: #238636;
  border-color: #2ea043;
}
.dl-btn.primary:hover {
  background: #2ea043;
}
</style>
