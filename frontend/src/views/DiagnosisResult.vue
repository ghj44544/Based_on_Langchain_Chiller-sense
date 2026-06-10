<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h2 class="page-title">诊断结果</h2>
        <p class="page-subtitle">展示最近一次上传诊断的模型输出、数据摘要和维护建议。</p>
      </div>
      <div v-if="result" class="toolbar">
        <el-button type="primary" @click="goReport">生成 Markdown 报告</el-button>
        <el-button @click="goChat">进入诊断问答</el-button>
      </div>
    </div>

    <el-alert
      v-if="!result"
      title="暂无诊断结果"
      description="请先上传 Excel 或 CSV 文件完成一次诊断。"
      type="info"
      show-icon
      :closable="false"
    >
      <template #default>
        <el-button type="primary" class="empty-action" @click="$router.push('/diagnosis/upload')">去上传诊断</el-button>
      </template>
    </el-alert>

    <template v-else>
      <DiagnosisSummary :result="result" />

      <PredictionChart :distribution="result.model_result.prediction_distribution" :labels="diagnosisStore.labels" />

      <el-row :gutter="16">
        <el-col :xs="24" :lg="12">
          <el-card class="panel-card" shadow="never">
            <template #header>
              <div class="card-header">
                <span>dataset_summary</span>
                <el-tag type="info" effect="plain">数据集摘要</el-tag>
              </div>
            </template>

            <el-descriptions :column="1" border>
              <el-descriptions-item label="total_rows">{{ displayValue(result.dataset_summary.total_rows) }}</el-descriptions-item>
              <el-descriptions-item label="total_columns">
                {{ displayValue(result.dataset_summary.total_columns) }}
              </el-descriptions-item>
              <el-descriptions-item label="validation_mode">
                {{ displayValue(result.dataset_summary.validation_mode) }}
              </el-descriptions-item>
              <el-descriptions-item label="has_label">{{ boolValue(result.dataset_summary.has_label) }}</el-descriptions-item>
              <el-descriptions-item label="label_distribution">
                <div v-if="labelDistributionRows.length" class="tag-list">
                  <el-tag v-for="item in labelDistributionRows" :key="item.label" effect="plain">
                    {{ item.name }}: {{ item.value }}
                  </el-tag>
                </div>
                <span v-else>暂无</span>
              </el-descriptions-item>
            </el-descriptions>
          </el-card>
        </el-col>

        <el-col :xs="24" :lg="12">
          <el-card class="panel-card" shadow="never">
            <template #header>
              <div class="card-header">
                <span>诊断解释</span>
              </div>
            </template>

            <MarkdownPreview :content="result.explanation || '后端未返回解释内容。'" />
          </el-card>
        </el-col>
      </el-row>

      <el-card class="panel-card" shadow="never">
        <template #header>
          <div class="card-header">
            <span>维修建议</span>
            <el-tag type="info" effect="plain">{{ result.maintenance_suggestions.length }} 条</el-tag>
          </div>
        </template>

        <el-empty v-if="!result.maintenance_suggestions.length" description="暂无维修建议" />
        <el-timeline v-else>
          <el-timeline-item v-for="(suggestion, index) in result.maintenance_suggestions" :key="index" :timestamp="`建议 ${index + 1}`">
            {{ suggestion }}
          </el-timeline-item>
        </el-timeline>
      </el-card>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';

import { getLabels } from '@/api/meta';
import DiagnosisSummary from '@/components/DiagnosisSummary.vue';
import MarkdownPreview from '@/components/MarkdownPreview.vue';
import PredictionChart from '@/components/PredictionChart.vue';
import { useDiagnosisStore } from '@/stores/diagnosis';

const router = useRouter();
const diagnosisStore = useDiagnosisStore();

const result = computed(() => diagnosisStore.latestResult);
const labelDistributionRows = computed(() => {
  const distribution = result.value?.dataset_summary.label_distribution || {};
  return Object.entries(distribution).map(([label, value]) => ({
    label,
    name: diagnosisStore.resolveLabel(label),
    value,
  }));
});

onMounted(async () => {
  if (!Object.keys(diagnosisStore.labels).length) {
    try {
      diagnosisStore.setLabels(await getLabels());
    } catch {
      // The result page remains useful with numeric labels if metadata is unavailable.
    }
  }
});

function goReport() {
  void router.push({ path: '/reports', query: { diagnosis_id: result.value?.diagnosis_id } });
}

function goChat() {
  void router.push({ path: '/chat', query: { diagnosis_id: result.value?.diagnosis_id } });
}

function displayValue(value: unknown) {
  if (value === undefined || value === null || value === '') return '暂无';
  return String(value);
}

function boolValue(value: unknown) {
  if (typeof value === 'boolean') return value ? '是' : '否';
  return displayValue(value);
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

.empty-action {
  margin-top: 12px;
}

.tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
</style>
