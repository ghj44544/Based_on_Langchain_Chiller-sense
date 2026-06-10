<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h2 class="page-title">上传诊断</h2>
        <p class="page-subtitle">支持 RP1043 数据文件，前端只负责上传和展示后端诊断结果。</p>
      </div>
    </div>

    <UploadPanel @success="handleSuccess" />
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router';

import UploadPanel from '@/components/UploadPanel.vue';
import { useDiagnosisStore } from '@/stores/diagnosis';
import type { DiagnosisUploadResponse } from '@/types/api';

const router = useRouter();
const diagnosisStore = useDiagnosisStore();

function handleSuccess(result: DiagnosisUploadResponse) {
  diagnosisStore.setLatestResult(result);
  void router.push('/diagnosis/result');
}
</script>
