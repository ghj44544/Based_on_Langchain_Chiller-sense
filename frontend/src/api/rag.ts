import { request } from '@/api/request';
import type { RagAskPayload, RagAskResponse, RagSearchPayload, RagSearchResponse, RagSource } from '@/types/api';

export function getRagSources() {
  return request<RagSource[] | { sources: RagSource[] }>({
    method: 'GET',
    url: '/api/rag/sources',
  });
}

export function searchRag(payload: RagSearchPayload) {
  return request<RagSearchResponse>({
    method: 'POST',
    url: '/api/rag/search',
    data: payload,
  });
}

export function askRag(payload: RagAskPayload) {
  return request<RagAskResponse>({
    method: 'POST',
    url: '/api/rag/ask',
    data: payload,
  });
}
