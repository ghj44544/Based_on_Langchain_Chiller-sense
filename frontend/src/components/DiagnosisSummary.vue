<template>
  <el-card class="panel-card" shadow="never">
    <template #header>
      <div class="card-header">
        <span>诊断摘要</span>
        <el-tag :type="severityType">{{ result.model_result.severity }}</el-tag>
      </div>
    </template>

    <div class="metric-grid">
      <div class="metric">
        <div class="metric-label">diagnosis_id</div>
        <div class="metric-value">#{{ result.diagnosis_id }}</div>
      </div>
      <div class="metric">
        <div class="metric-label">主导故障名称</div>
        <div class="metric-value">{{ result.model_result.dominant_fault_name }}</div>
      </div>
      <div class="metric">
        <div class="metric-label">主导标签</div>
        <div class="metric-value">{{ result.model_result.dominant_label }}</div>
      </div>
      <div class="metric">
        <div class="metric-label">主导比例</div>
        <div class="metric-value">{{ percent(result.model_result.dominant_ratio) }}</div>
      </div>
      <div class="metric">
        <div class="metric-label">平均置信度</div>
        <div class="metric-value">{{ nullablePercent(result.model_result.avg_confidence) }}</div>
      </div>
      <div class="metric">
        <div class="metric-label">样本数</div>
        <div class="metric-value">{{ result.model_result.total_rows.toLocaleString() }}</div>
      </div>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { computed } from 'vue';

import type { DiagnosisUploadResponse } from '@/types/api';

const props = defineProps<{
  result: DiagnosisUploadResponse;
}>();

const severityType = computed(() => {
  const severity = props.result.model_result.severity?.toLowerCase();
  if (severity === 'high') return 'danger';
  if (severity === 'medium') return 'warning';
  if (severity === 'low') return 'success';
  return 'info';
});

function percent(value: number) {
  return `${(value * 100).toFixed(2)}%`;
}

function nullablePercent(value?: number | null) {
  return typeof value === 'number' ? percent(value) : '暂无';
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
</style>
