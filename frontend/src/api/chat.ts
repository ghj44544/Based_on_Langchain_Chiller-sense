import { request } from '@/api/request';
import type { ChatRequest, ChatResponse } from '@/types/api';

export function askDiagnosisQuestion(payload: ChatRequest) {
  return request<ChatResponse>({
    method: 'POST',
    url: '/api/chat',
    data: payload,
  });
}
