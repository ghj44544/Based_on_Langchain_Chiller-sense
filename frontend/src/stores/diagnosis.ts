import { defineStore } from 'pinia';
import { computed, ref } from 'vue';

import type { DiagnosisUploadResponse, LabelMap } from '@/types/api';

const RESULT_KEY = 'chiller-sense.latest-diagnosis';
const LABEL_KEY = 'chiller-sense.labels';

function readJson<T>(key: string): T | null {
  const raw = window.sessionStorage.getItem(key);
  if (!raw) return null;

  try {
    return JSON.parse(raw) as T;
  } catch {
    window.sessionStorage.removeItem(key);
    return null;
  }
}

export const useDiagnosisStore = defineStore('diagnosis', () => {
  const latestResult = ref<DiagnosisUploadResponse | null>(readJson<DiagnosisUploadResponse>(RESULT_KEY));
  const labels = ref<LabelMap>(readJson<LabelMap>(LABEL_KEY) || {});

  const latestDiagnosisId = computed(() => latestResult.value?.diagnosis_id ?? null);

  function setLatestResult(result: DiagnosisUploadResponse) {
    latestResult.value = result;
    window.sessionStorage.setItem(RESULT_KEY, JSON.stringify(result));
  }

  function setLabels(nextLabels: LabelMap) {
    labels.value = nextLabels;
    window.sessionStorage.setItem(LABEL_KEY, JSON.stringify(nextLabels));
  }

  function resolveLabel(label: string | number) {
    const key = String(label);
    return labels.value[key] ? `${key} - ${labels.value[key]}` : key;
  }

  return {
    labels,
    latestResult,
    latestDiagnosisId,
    setLatestResult,
    setLabels,
    resolveLabel,
  };
});
