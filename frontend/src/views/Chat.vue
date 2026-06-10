<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h2 class="page-title">诊断问答</h2>
        <p class="page-subtitle">围绕某次 diagnosis_id 继续提问，回答由后端 LangChain 接口决定。</p>
      </div>
    </div>

    <el-card class="panel-card" shadow="never">
      <el-form label-position="top" @submit.prevent>
        <el-row :gutter="14">
          <el-col :xs="24" :sm="6">
            <el-form-item label="diagnosis_id">
              <el-input-number v-model="diagnosisId" :min="1" :precision="0" controls-position="right" class="full-width" />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="18">
            <el-form-item label="问题">
              <el-input
                v-model="question"
                placeholder="例如：为什么判断为这个故障？应该优先检查哪里？"
                clearable
                @keyup.enter="submit"
              />
            </el-form-item>
          </el-col>
        </el-row>

        <el-button type="primary" :loading="loading" :disabled="!question.trim()" @click="submit">发送问题</el-button>
      </el-form>
    </el-card>

    <el-card class="panel-card chat-card" shadow="never">
      <template #header>
        <div class="card-header">
          <span>问答记录</span>
          <el-tag type="info" effect="plain">{{ messages.length }} 条</el-tag>
        </div>
      </template>

      <el-empty v-if="!messages.length" description="暂无问答记录" />
      <div v-else class="message-list">
        <div v-for="message in messages" :key="message.id" class="message" :class="message.role">
          <div class="message-meta">
            <el-tag :type="message.role === 'user' ? 'primary' : message.isError ? 'warning' : 'success'" size="small">
              {{ message.role === 'user' ? '用户' : '助手' }}
            </el-tag>
            <span v-if="message.isError" class="muted">业务提示</span>
          </div>
          <div class="message-content">{{ message.content }}</div>
          <div v-if="message.role === 'assistant' && !message.isError" class="rag-block">
            <div class="rag-title">
              <span>RAG 知识库来源</span>
              <el-tag v-if="message.retriever" type="primary" effect="plain" size="small">{{ message.retriever }}</el-tag>
            </div>
            <div class="sources">
              <el-tag v-if="!message.sources?.length" type="info" effect="plain" size="small">
                本次未返回知识库来源
              </el-tag>
              <el-tag v-for="source in message.sources" :key="source" effect="plain" size="small">{{ source }}</el-tag>
            </div>
            <div v-if="message.hits?.length" class="hit-list">
              <div v-for="hit in message.hits" :key="`${hit.source}-${hit.chunk_id}`" class="hit-item">
                <div class="hit-meta">
                  <span>{{ hit.source }}</span>
                  <span>chunk_id: {{ hit.chunk_id }}</span>
                  <span>score: {{ formatScore(hit.score) }}</span>
                </div>
                <div class="hit-content">{{ hit.content }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { useRoute } from 'vue-router';

import { askDiagnosisQuestion } from '@/api/chat';
import { ApiServiceError } from '@/api/request';
import { useDiagnosisStore } from '@/stores/diagnosis';
import type { RagHit } from '@/types/api';

interface ChatMessage {
  id: number;
  role: 'user' | 'assistant';
  content: string;
  retriever?: string;
  sources?: string[];
  hits?: RagHit[];
  isError?: boolean;
}

const route = useRoute();
const diagnosisStore = useDiagnosisStore();
const diagnosisId = ref(1);
const question = ref('');
const loading = ref(false);
const messages = ref<ChatMessage[]>([]);
let nextId = 1;

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
  const text = question.value.trim();
  if (!text) return;

  messages.value.push({ id: nextId++, role: 'user', content: text });
  question.value = '';
  loading.value = true;

  try {
    const response = await askDiagnosisQuestion({
      diagnosis_id: diagnosisId.value,
      question: text,
    });
    messages.value.push({
      id: nextId++,
      role: 'assistant',
      content: response.answer,
      retriever: response.retriever,
      sources: response.sources,
      hits: response.hits,
    });
  } catch (error) {
    const message = error instanceof ApiServiceError ? error.message : '问答接口调用失败';
    messages.value.push({
      id: nextId++,
      role: 'assistant',
      content: message,
      isError: true,
    });
  } finally {
    loading.value = false;
  }
}

function formatScore(score: number) {
  return Number.isFinite(score) ? score.toFixed(4) : '-';
}
</script>

<style scoped>
.full-width {
  width: 100%;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: #172b4d;
  font-weight: 700;
}

.chat-card {
  min-height: 360px;
}

.message-list {
  display: grid;
  gap: 14px;
}

.message {
  max-width: 860px;
  padding: 14px;
  border: 1px solid #dce9f5;
  border-radius: 8px;
  background: #fbfdff;
}

.message.user {
  margin-left: auto;
  background: #eef8fc;
}

.message-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.message-content {
  color: #253858;
  line-height: 1.7;
  white-space: pre-wrap;
}

.rag-block {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #dce9f5;
}

.rag-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 8px;
  color: #172b4d;
  font-size: 13px;
  font-weight: 700;
}

.sources {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  color: #6b778c;
  font-size: 13px;
}

.hit-list {
  display: grid;
  gap: 8px;
  margin-top: 10px;
}

.hit-item {
  padding: 10px;
  border: 1px solid #e3edf7;
  border-radius: 8px;
  background: #fff;
}

.hit-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 6px;
  color: #6b778c;
  font-size: 12px;
}

.hit-content {
  color: #253858;
  font-size: 13px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
}
</style>
