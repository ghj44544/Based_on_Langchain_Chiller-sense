<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h2 class="page-title">诊断报告</h2>
        <p class="page-subtitle">输入诊断记录 ID，调用后端生成并导出 md / html / docx 多格式报告。</p>
      </div>
    </div>

    <el-card class="panel-card" shadow="never">
      <el-form :inline="true" @submit.prevent>
        <el-form-item label="diagnosis_id">
          <el-input-number v-model="diagnosisId" :min="1" :precision="0" controls-position="right" />
        </el-form-item>
        <el-form-item label="导出格式">
          <el-segmented v-model="reportFormat" :options="formatOptions" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" @click="submit">生成 {{ formatLabel }} 报告</el-button>
          <el-button :loading="latestLoading" @click="downloadLatest">下载最新 {{ formatLabel }} 报告</el-button>
        </el-form-item>
      </el-form>

      <el-alert
        v-if="errorMessage"
        :title="errorMessage"
        type="error"
        show-icon
        :closable="false"
      />
    </el-card>

    <el-card v-if="report" class="panel-card" shadow="never">
      <template #header>
        <div class="card-header">
          <span>报告生成结果</span>
          <el-tag type="success">已生成</el-tag>
        </div>
      </template>

      <el-descriptions :column="1" border>
        <el-descriptions-item label="report_path">
          <span class="mono">{{ report.report_path }}</span>
        </el-descriptions-item>
        <el-descriptions-item v-if="report.report_filename" label="report_filename">
          <span class="mono">{{ report.report_filename }}</span>
        </el-descriptions-item>
        <el-descriptions-item v-if="report.report_format" label="report_format">
          <el-tag effect="plain">{{ report.report_format }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item v-if="report.download_url" label="download_url">
          <span class="mono">{{ report.download_url }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="保存位置">报告已保存在后端 reports 目录。</el-descriptions-item>
      </el-descriptions>

      <div class="report-actions">
        <el-button
          v-if="report.download_url"
          type="primary"
          @click="downloadReport(report.download_url, report.report_filename)"
        >
          下载 {{ report.report_format ? formatName(report.report_format) : '报告' }} 文件
        </el-button>
        <el-button @click="downloadLatest">下载该 ID 最新 {{ formatLabel }} 报告</el-button>
      </div>

      <div v-if="report.report_content" class="preview-block">
        <h3 class="section-title">报告预览</h3>
        <MarkdownPreview :content="report.report_content" />
      </div>
      <el-alert
        v-else
        class="path-alert"
        title="后端当前通过下载接口导出文件，前端不会强行读取服务器文件。"
        type="info"
        show-icon
        :closable="false"
      />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useRoute } from 'vue-router';

import { buildDownloadUrl, generateReport, getLatestReport, getLatestReportDownloadUrl } from '@/api/report';
import { ApiServiceError } from '@/api/request';
import MarkdownPreview from '@/components/MarkdownPreview.vue';
import { useDiagnosisStore } from '@/stores/diagnosis';
import type { ReportFormat, ReportResponse } from '@/types/api';

const route = useRoute();
const diagnosisStore = useDiagnosisStore();
const diagnosisId = ref(1);
const loading = ref(false);
const latestLoading = ref(false);
const errorMessage = ref('');
const report = ref<ReportResponse | null>(null);
const reportFormat = ref<ReportFormat>('md');

const formatOptions: Array<{ label: string; value: ReportFormat }> = [
  { label: 'Markdown', value: 'md' },
  { label: 'HTML', value: 'html' },
  { label: 'Word', value: 'docx' },
];

const formatLabel = computed(() => formatName(reportFormat.value));

onMounted(() => {
  const queryId = Number(route.query.diagnosis_id);
  if (Number.isFinite(queryId) && queryId > 0) {
    diagnosisId.value = queryId;
    return;
  }

  if (diagnosisStore.latestDiagnosisId) {
    diagnosisId.value = diagnosisStore.latestDiagnosisId;
  }
});

async function submit() {
  loading.value = true;
  errorMessage.value = '';
  report.value = null;

  try {
    report.value = await generateReport(diagnosisId.value, reportFormat.value);
  } catch (error) {
    errorMessage.value = error instanceof ApiServiceError ? error.message : '报告生成失败';
  } finally {
    loading.value = false;
  }
}

async function downloadLatest() {
  latestLoading.value = true;
  errorMessage.value = '';

  try {
    const latestReport = await getLatestReport(diagnosisId.value, reportFormat.value);
    report.value = latestReport;
    downloadReport(
      latestReport.download_url || getLatestReportDownloadUrl(diagnosisId.value, reportFormat.value),
      latestReport.report_filename,
    );
  } catch (error) {
    errorMessage.value = error instanceof ApiServiceError ? error.message : '最新报告下载失败';
  } finally {
    latestLoading.value = false;
  }
}

function downloadReport(downloadUrl: string, filename?: string) {
  const link = document.createElement('a');
  link.href = buildDownloadUrl(downloadUrl);
  if (filename) {
    link.download = filename;
  }
  document.body.appendChild(link);
  link.click();
  link.remove();
}

function formatName(format: ReportFormat) {
  const option = formatOptions.find((item) => item.value === format);
  return option?.label || format.toUpperCase();
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

.preview-block {
  margin-top: 18px;
}

.report-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 16px;
}

.path-alert {
  margin-top: 16px;
}
</style>
