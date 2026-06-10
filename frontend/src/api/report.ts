import { request } from '@/api/request';
import type { ReportFormat, ReportResponse } from '@/types/api';

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

export function generateReport(diagnosisId: number, reportFormat: ReportFormat = 'md') {
  return request<ReportResponse>({
    method: 'POST',
    url: `/api/report/generate/${diagnosisId}`,
    params: { report_format: reportFormat },
  });
}

export function getLatestReport(diagnosisId: number, reportFormat?: ReportFormat) {
  return request<ReportResponse>({
    method: 'GET',
    url: `/api/report/latest/${diagnosisId}`,
    params: reportFormat ? { report_format: reportFormat } : undefined,
  });
}

export function getLatestReportDownloadUrl(diagnosisId: number, reportFormat?: ReportFormat) {
  const query = reportFormat ? `?report_format=${encodeURIComponent(reportFormat)}` : '';
  return buildDownloadUrl(`/api/report/download/latest/${diagnosisId}${query}`);
}

export function buildDownloadUrl(downloadUrl: string) {
  if (/^https?:\/\//i.test(downloadUrl)) {
    return downloadUrl;
  }
  return `${apiBaseUrl.replace(/\/$/, '')}${downloadUrl.startsWith('/') ? downloadUrl : `/${downloadUrl}`}`;
}
