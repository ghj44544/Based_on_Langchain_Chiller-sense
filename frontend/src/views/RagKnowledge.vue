<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h2 class="page-title">知识库问答</h2>
        <p class="page-subtitle">面向 backend-rag 的知识库检索与问答，展示检索模式、来源和命中文档片段。</p>
      </div>
      <el-button :loading="sourcesLoading" @click="loadSources">刷新来源</el-button>
    </div>

    <el-card class="panel-card" shadow="never">
      <el-form label-position="top" @submit.prevent>
        <el-form-item label="问题">
          <el-input
            v-model="query"
            type="textarea"
            :rows="3"
            maxlength="500"
            show-word-limit
            placeholder="例如：冷却水流量不足有哪些典型表现？应该优先检查哪些参数？"
          />
        </el-form-item>

        <div class="control-row">
          <el-form-item label="检索模式">
            <el-segmented v-model="retriever" :options="retrieverOptions" />
          </el-form-item>
          <el-form-item label="top_k">
            <el-input-number v-model="topK" :min="1" :max="20" :precision="0" controls-position="right" />
          </el-form-item>
          <el-form-item label="操作">
            <div class="actions">
              <el-button type="primary" :loading="searchLoading" :disabled="!query.trim()" @click="handleSearch">
                检索
              </el-button>
              <el-button :loading="askLoading" :disabled="!query.trim()" @click="handleAsk">问答</el-button>
            </div>
          </el-form-item>
        </div>
      </el-form>

      <el-alert v-if="errorMessage" :title="errorMessage" type="error" show-icon :closable="false" />
    </el-card>

    <el-row :gutter="16">
      <el-col :xs="24" :lg="8">
        <el-card class="panel-card" shadow="never">
          <template #header>
            <div class="card-header">
              <span>知识库来源</span>
              <el-tag type="info" effect="plain">{{ normalizedSources.length }} 项</el-tag>
            </div>
          </template>

          <el-skeleton v-if="sourcesLoading" :rows="4" animated />
          <el-empty v-else-if="!normalizedSources.length" description="暂无来源信息" />
          <div v-else class="source-list">
            <div v-for="source in normalizedSources" :key="source.key" class="source-item">
              <div class="source-title">{{ source.title }}</div>
              <div v-if="source.detail" class="source-detail">{{ source.detail }}</div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="16">
        <el-card class="panel-card" shadow="never">
          <template #header>
            <div class="card-header">
              <span>RAG 问答结果</span>
              <el-tag v-if="askResult?.retriever" type="primary" effect="plain">{{ askResult.retriever }}</el-tag>
            </div>
          </template>

          <el-empty v-if="!askResult" description="点击“问答”后展示 LLM 回答和引用来源" />
          <template v-else>
            <div class="answer-block">{{ askResult.answer }}</div>
            <div class="source-tags">
              <span>RAG 知识库来源：</span>
              <el-tag v-if="!askResult.sources?.length" type="info" effect="plain">本次未返回知识库来源</el-tag>
              <el-tag v-for="source in askResult.sources" :key="source" effect="plain">{{ source }}</el-tag>
            </div>
          </template>
        </el-card>

        <el-card class="panel-card hit-card" shadow="never">
          <template #header>
            <div class="card-header">
              <span>命中文档片段</span>
              <el-tag type="info" effect="plain">{{ activeHits.length }} 条</el-tag>
            </div>
          </template>

          <el-empty v-if="!activeHits.length" description="点击“检索”或“问答”后展示命中文档" />
          <div v-else class="hit-list">
            <div v-for="hit in activeHits" :key="`${hit.source}-${hit.chunk_id}`" class="hit-item">
              <div class="hit-meta">
                <el-tag type="primary" effect="plain">{{ hit.source }}</el-tag>
                <span class="muted">chunk_id: {{ hit.chunk_id }}</span>
                <span class="muted">score: {{ formatScore(hit.score) }}</span>
              </div>
              <div class="hit-content">{{ hit.content }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';

import { askRag, getRagSources, searchRag } from '@/api/rag';
import { ApiServiceError } from '@/api/request';
import type { RagAskResponse, RagHit, RagRetriever, RagSearchResponse, RagSource } from '@/types/api';

type SelectableRetriever = Extract<RagRetriever, 'hybrid' | 'vector' | 'keyword'>;

interface NormalizedSource {
  key: string;
  title: string;
  detail: string;
}

const query = ref('');
const retriever = ref<SelectableRetriever>('hybrid');
const topK = ref(4);
const sources = ref<RagSource[]>([]);
const sourcesLoading = ref(false);
const searchLoading = ref(false);
const askLoading = ref(false);
const errorMessage = ref('');
const searchResult = ref<RagSearchResponse | null>(null);
const askResult = ref<RagAskResponse | null>(null);

const retrieverOptions: Array<{ label: string; value: SelectableRetriever }> = [
  { label: 'Hybrid', value: 'hybrid' },
  { label: 'Vector', value: 'vector' },
  { label: 'Keyword', value: 'keyword' },
];

const normalizedSources = computed(() => sources.value.map(normalizeSource));
const activeHits = computed<RagHit[]>(() => askResult.value?.hits || searchResult.value?.hits || []);

onMounted(() => {
  void loadSources();
});

async function loadSources() {
  sourcesLoading.value = true;
  errorMessage.value = '';

  try {
    const response = await getRagSources();
    sources.value = Array.isArray(response) ? response : response.sources || [];
  } catch (error) {
    errorMessage.value = error instanceof ApiServiceError ? error.message : '知识库来源加载失败';
  } finally {
    sourcesLoading.value = false;
  }
}

async function handleSearch() {
  const text = query.value.trim();
  if (!text) return;

  searchLoading.value = true;
  errorMessage.value = '';
  askResult.value = null;

  try {
    searchResult.value = await searchRag({
      query: text,
      retriever: retriever.value,
      top_k: topK.value,
    });
  } catch (error) {
    errorMessage.value = error instanceof ApiServiceError ? error.message : 'RAG 检索失败';
  } finally {
    searchLoading.value = false;
  }
}

async function handleAsk() {
  const text = query.value.trim();
  if (!text) return;

  askLoading.value = true;
  errorMessage.value = '';
  searchResult.value = null;

  try {
    askResult.value = await askRag({
      question: text,
      retriever: retriever.value,
      top_k: topK.value,
    });
  } catch (error) {
    errorMessage.value = error instanceof ApiServiceError ? error.message : 'RAG 问答失败';
  } finally {
    askLoading.value = false;
  }
}

function normalizeSource(source: RagSource, index: number): NormalizedSource {
  if (typeof source === 'string') {
    return { key: `${source}-${index}`, title: source, detail: '' };
  }

  const title = String(source.filename || source.source || source.name || source.path || `来源 ${index + 1}`);
  const detailParts = Object.entries(source)
    .filter(([key]) => !['filename', 'source', 'name', 'path'].includes(key))
    .map(([key, value]) => `${key}: ${String(value)}`);

  return {
    key: `${title}-${index}`,
    title,
    detail: detailParts.join('，'),
  };
}

function formatScore(score: number) {
  return Number.isFinite(score) ? score.toFixed(4) : '-';
}
</script>

<style scoped>
.control-row {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  gap: 14px;
}

.actions {
  display: flex;
  gap: 10px;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  color: #172b4d;
  font-weight: 700;
}

.source-list,
.hit-list {
  display: grid;
  gap: 10px;
}

.source-item,
.hit-item {
  padding: 12px;
  border: 1px solid #dce9f5;
  border-radius: 8px;
  background: #fbfdff;
}

.source-title {
  color: #172b4d;
  font-weight: 700;
  word-break: break-word;
}

.source-detail {
  margin-top: 6px;
  color: #6b778c;
  font-size: 12px;
  line-height: 1.6;
  word-break: break-word;
}

.answer-block {
  padding: 14px;
  border: 1px solid #dce9f5;
  border-radius: 8px;
  background: #fbfdff;
  color: #253858;
  line-height: 1.7;
  white-space: pre-wrap;
}

.source-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 12px;
  color: #6b778c;
  font-size: 13px;
}

.hit-card {
  margin-top: 16px;
}

.hit-meta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.hit-content {
  color: #253858;
  line-height: 1.7;
  white-space: pre-wrap;
  word-break: break-word;
}

@media (max-width: 760px) {
  .control-row,
  .actions {
    align-items: stretch;
    flex-direction: column;
  }
}
</style>
