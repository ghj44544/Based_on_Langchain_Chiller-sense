<template>
  <el-card class="panel-card" shadow="never">
    <template #header>
      <div class="card-header">
        <span>后端健康状态</span>
        <el-button size="small" :loading="loading" @click="$emit('refresh')">刷新</el-button>
      </div>
    </template>

    <el-skeleton v-if="loading" :rows="4" animated />

    <el-alert
      v-else-if="error"
      title="后端服务不可用"
      :description="error"
      type="error"
      show-icon
      :closable="false"
    />

    <template v-else-if="status">
      <el-alert
        v-if="status.matlab_engine_available === false"
        title="MATLAB Engine 不可用"
        description="请先打开 MATLAB 并执行 matlab.engine.shareEngine"
        type="warning"
        show-icon
        :closable="false"
        class="matlab-alert"
      />

      <div class="status-grid">
        <div class="status-item">
          <span>model_loaded</span>
          <el-tag :type="status.model_loaded ? 'success' : 'danger'">{{ boolText(status.model_loaded) }}</el-tag>
        </div>
        <div class="status-item">
          <span>model_type</span>
          <el-tag type="info" effect="plain">{{ status.model_type || 'unknown' }}</el-tag>
        </div>
        <div class="status-item">
          <span>matlab_engine_available</span>
          <el-tag :type="status.matlab_engine_available ? 'success' : 'warning'">
            {{ nullableBoolText(status.matlab_engine_available) }}
          </el-tag>
        </div>
        <div class="status-item">
          <span>matlab_shared_engines</span>
          <span class="value-text">{{ sharedEngines }}</span>
        </div>
        <div class="status-item">
          <span>llm_enabled</span>
          <el-tag :type="status.llm_enabled ? 'success' : 'info'">{{ boolText(status.llm_enabled) }}</el-tag>
        </div>
        <div class="status-item">
          <span>llm_configured</span>
          <el-tag :type="status.llm_configured ? 'success' : 'info'">{{ boolText(status.llm_configured) }}</el-tag>
        </div>
        <div class="status-item">
          <span>rag_enabled</span>
          <el-tag :type="status.rag_enabled ? 'success' : 'info'">{{ boolText(status.rag_enabled) }}</el-tag>
        </div>
      </div>
    </template>
  </el-card>
</template>

<script setup lang="ts">
import { computed } from 'vue';

import type { HealthStatus } from '@/types/api';

const props = defineProps<{
  status: HealthStatus | null;
  loading: boolean;
  error: string;
}>();

defineEmits<{
  refresh: [];
}>();

const sharedEngines = computed(() => {
  if (!props.status?.matlab_shared_engines?.length) {
    return '无';
  }
  return props.status.matlab_shared_engines.join(', ');
});

function boolText(value: boolean) {
  return value ? '是' : '否';
}

function nullableBoolText(value: boolean | null) {
  if (value === null) return '不适用';
  return boolText(value);
}
</script>

<style scoped>
.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: #172b4d;
  font-weight: 700;
}

.matlab-alert {
  margin-bottom: 14px;
}

.status-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(230px, 1fr));
  gap: 10px;
}

.status-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  min-height: 42px;
  padding: 10px 12px;
  border: 1px solid #e3edf7;
  border-radius: 8px;
  background: #fbfdff;
  color: #42526e;
  font-size: 13px;
}

.value-text {
  color: #172b4d;
  text-align: right;
  word-break: break-all;
}
</style>
