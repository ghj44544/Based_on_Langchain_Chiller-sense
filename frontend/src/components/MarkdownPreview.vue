<template>
  <div class="markdown-preview" v-html="html"></div>
</template>

<script setup lang="ts">
import MarkdownIt from 'markdown-it';
import { computed } from 'vue';

const props = defineProps<{
  content: string;
}>();

const md = new MarkdownIt({
  breaks: true,
  html: false,
  linkify: true,
});

const html = computed(() => md.render(props.content || ''));
</script>

<style scoped>
.markdown-preview {
  color: #253858;
  line-height: 1.72;
}

.markdown-preview :deep(h1),
.markdown-preview :deep(h2),
.markdown-preview :deep(h3) {
  margin: 18px 0 10px;
  color: #172b4d;
}

.markdown-preview :deep(p) {
  margin: 8px 0;
}

.markdown-preview :deep(code) {
  padding: 2px 5px;
  border-radius: 4px;
  background: #eef4fb;
  color: #0f6b9f;
}

.markdown-preview :deep(pre) {
  overflow-x: auto;
  padding: 12px;
  border-radius: 8px;
  background: #eef4fb;
}
</style>
