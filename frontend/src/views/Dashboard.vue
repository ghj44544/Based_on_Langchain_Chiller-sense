<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h2 class="page-title">系统工作台</h2>
        <p class="page-subtitle">上传数据、查看模型与 MATLAB 状态，并进入报告和问答流程。</p>
      </div>
    </div>

    <HealthStatus :status="health" :loading="healthLoading" :error="healthError" @refresh="loadHealth" />

    <div class="dashboard-grid">
      <UploadPanel @success="handleUploadSuccess" />

      <el-card class="panel-card" shadow="never">
        <template #header>
          <div class="card-header">
            <span>快速入口</span>
            <el-tag type="info" effect="plain">MVP</el-tag>
          </div>
        </template>

        <div class="quick-grid">
          <router-link v-for="entry in entries" :key="entry.path" :to="entry.path" class="quick-entry">
            <el-icon><component :is="entry.icon" /></el-icon>
            <div>
              <div class="quick-title">{{ entry.title }}</div>
              <div class="quick-desc">{{ entry.desc }}</div>
            </div>
          </router-link>
        </div>
      </el-card>
    </div>

    <el-row :gutter="16">
      <el-col :xs="24" :lg="12">
        <el-card class="panel-card" shadow="never">
          <template #header>
            <div class="card-header">
              <span>标签映射</span>
              <el-button size="small" :loading="metaLoading" @click="loadMeta">刷新</el-button>
            </div>
          </template>

          <el-alert v-if="metaError" :title="metaError" type="warning" show-icon :closable="false" />
          <el-table v-else :data="labelRows" size="small" max-height="260">
            <el-table-column prop="label" label="标签" width="90" />
            <el-table-column prop="name" label="故障名称" />
          </el-table>
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="12">
        <el-card class="panel-card feature-card" shadow="never">
          <template #header>
            <div class="card-header">
              <span>模型输入字段</span>
              <el-tag type="info" effect="plain">{{ features.length }} 项</el-tag>
            </div>
          </template>

          <el-empty v-if="!features.length && !metaLoading" description="暂无字段信息" />
          <el-skeleton v-else-if="metaLoading" :rows="5" animated />
          <div v-else class="feature-list">
            <el-tag v-for="feature in features" :key="feature" effect="plain">{{ feature }}</el-tag>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ChatDotRound, Document, Histogram, Tickets } from '@element-plus/icons-vue';
import { computed, onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';

import { getFeatures, getHealth, getLabels } from '@/api/meta';
import { ApiServiceError } from '@/api/request';
import HealthStatus from '@/components/HealthStatus.vue';
import UploadPanel from '@/components/UploadPanel.vue';
import { useDiagnosisStore } from '@/stores/diagnosis';
import type { DiagnosisUploadResponse, FeatureList, HealthStatus as HealthStatusType, LabelMap } from '@/types/api';

const router = useRouter();
const diagnosisStore = useDiagnosisStore();

const health = ref<HealthStatusType | null>(null);
const healthLoading = ref(false);
const healthError = ref('');
const labels = ref<LabelMap>({});
const features = ref<FeatureList>([]);
const metaLoading = ref(false);
const metaError = ref('');

const entries = [
  { title: '上传诊断', desc: '提交 Excel / CSV 并调用模型', path: '/diagnosis/upload', icon: Tickets },
  { title: '查看标签映射', desc: '确认标签与故障名称', path: '/', icon: Histogram },
  { title: '生成报告', desc: '按 diagnosis_id 生成 Markdown', path: '/reports', icon: Document },
  { title: '诊断问答', desc: '围绕诊断记录继续追问', path: '/chat', icon: ChatDotRound },
];

const labelRows = computed(() => Object.entries(labels.value).map(([label, name]) => ({ label, name })));

onMounted(() => {
  void loadHealth();
  void loadMeta();
});

async function loadHealth() {
  healthLoading.value = true;
  healthError.value = '';

  try {
    health.value = await getHealth();
  } catch (error) {
    health.value = null;
    healthError.value = error instanceof ApiServiceError ? error.message : '后端服务不可用';
  } finally {
    healthLoading.value = false;
  }
}

async function loadMeta() {
  metaLoading.value = true;
  metaError.value = '';

  try {
    const [labelMap, featureList] = await Promise.all([getLabels(), getFeatures()]);
    labels.value = labelMap;
    features.value = featureList;
    diagnosisStore.setLabels(labelMap);
  } catch (error) {
    metaError.value = error instanceof ApiServiceError ? error.message : '元信息加载失败';
  } finally {
    metaLoading.value = false;
  }
}

function handleUploadSuccess(result: DiagnosisUploadResponse) {
  diagnosisStore.setLatestResult(result);
  void router.push('/diagnosis/result');
}
</script>

<style scoped>
.dashboard-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.25fr) minmax(320px, 0.75fr);
  gap: 16px;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: #172b4d;
  font-weight: 700;
}

.quick-grid {
  display: grid;
  gap: 10px;
}

.quick-entry {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px;
  border: 1px solid #dce9f5;
  border-radius: 8px;
  background: #fbfdff;
  transition:
    border-color 0.2s,
    transform 0.2s;
}

.quick-entry:hover {
  border-color: #0f8ab8;
  transform: translateY(-1px);
}

.quick-entry .el-icon {
  color: #0f6b9f;
  font-size: 24px;
}

.quick-title {
  color: #172b4d;
  font-weight: 700;
}

.quick-desc {
  margin-top: 3px;
  color: #7a869a;
  font-size: 12px;
}

.feature-card {
  height: 100%;
}

.feature-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  max-height: 260px;
  overflow: auto;
}

@media (max-width: 1040px) {
  .dashboard-grid {
    grid-template-columns: 1fr;
  }
}
</style>
