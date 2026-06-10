<template>
  <el-card class="panel-card" shadow="never">
    <template #header>
      <div class="card-header">
        <span>上传诊断数据</span>
        <el-tag type="info" effect="plain">.xlsx / .xls / .csv</el-tag>
      </div>
    </template>

    <el-upload
      v-model:file-list="fileList"
      drag
      :auto-upload="false"
      :limit="1"
      accept=".xlsx,.xls,.csv"
      :on-change="handleFileChange"
      :on-remove="handleFileRemove"
      :on-exceed="handleExceed"
    >
      <el-icon class="upload-icon"><UploadFilled /></el-icon>
      <div class="el-upload__text">将 Excel / CSV 文件拖到此处，或点击选择</div>
      <template #tip>
        <div class="upload-tip">前端不会解析或改写数据，文件将直接提交到后端诊断接口。</div>
      </template>
    </el-upload>

    <div v-if="selectedFile" class="file-info">
      <div>
        <div class="file-name">{{ selectedFile.name }}</div>
        <div class="file-size">{{ formatFileSize(selectedFile.size) }}</div>
      </div>
      <el-tag type="success" effect="plain">已选择</el-tag>
    </div>

    <el-alert
      v-if="errorMessage"
      class="upload-error"
      :title="errorMessage"
      type="error"
      show-icon
      :closable="false"
    />

    <div class="actions">
      <el-button type="primary" :disabled="!selectedFile" :loading="uploading" @click="submit">
        开始诊断
      </el-button>
      <el-button :disabled="uploading || !selectedFile" @click="reset">清空</el-button>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { UploadFilled } from '@element-plus/icons-vue';
import { ElMessage } from 'element-plus';
import type { UploadFile, UploadFiles, UploadUserFile } from 'element-plus';
import { ref } from 'vue';

import { uploadDiagnosisFile } from '@/api/diagnosis';
import { ApiServiceError } from '@/api/request';
import type { DiagnosisUploadResponse } from '@/types/api';

const emit = defineEmits<{
  success: [result: DiagnosisUploadResponse];
}>();

const fileList = ref<UploadUserFile[]>([]);
const selectedFile = ref<File | null>(null);
const uploading = ref(false);
const errorMessage = ref('');

function handleFileChange(uploadFile: UploadFile) {
  errorMessage.value = '';
  selectedFile.value = uploadFile.raw || null;
}

function handleFileRemove() {
  selectedFile.value = null;
}

function handleExceed(_files: File[], uploadFiles: UploadFiles) {
  ElMessage.warning(`一次只能上传 1 个文件，请先移除 ${uploadFiles[0]?.name || '当前文件'}`);
}

function reset() {
  fileList.value = [];
  selectedFile.value = null;
  errorMessage.value = '';
}

async function submit() {
  if (!selectedFile.value) return;

  uploading.value = true;
  errorMessage.value = '';

  try {
    const result = await uploadDiagnosisFile(selectedFile.value);
    ElMessage.success('诊断完成');
    emit('success', result);
  } catch (error) {
    errorMessage.value = error instanceof ApiServiceError ? error.message : '上传诊断失败';
  } finally {
    uploading.value = false;
  }
}

function formatFileSize(size: number) {
  if (size < 1024) return `${size} B`;
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`;
  return `${(size / 1024 / 1024).toFixed(2)} MB`;
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

.upload-icon {
  color: #0f6b9f;
  font-size: 46px;
}

.upload-tip {
  color: #7a869a;
  font-size: 12px;
}

.file-info {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-top: 14px;
  padding: 12px;
  border: 1px solid #dce9f5;
  border-radius: 8px;
  background: #f8fbff;
}

.file-name {
  color: #172b4d;
  font-weight: 700;
  word-break: break-all;
}

.file-size {
  margin-top: 4px;
  color: #7a869a;
  font-size: 12px;
}

.upload-error {
  margin-top: 14px;
}

.actions {
  display: flex;
  gap: 10px;
  margin-top: 16px;
}
</style>
