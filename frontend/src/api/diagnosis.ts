import { request } from '@/api/request';
import type { DiagnosisUploadResponse } from '@/types/api';

export function uploadDiagnosisFile(file: File) {
  const formData = new FormData();
  formData.append('file', file);

  return request<DiagnosisUploadResponse>({
    method: 'POST',
    url: '/api/diagnosis/upload',
    data: formData,
    headers: { 'Content-Type': 'multipart/form-data' },
  });
}
