import { request } from '@/api/request';
import type { FeatureList, HealthStatus, LabelMap } from '@/types/api';

export function getHealth() {
  return request<HealthStatus>({ method: 'GET', url: '/api/health' });
}

export function getFeatures() {
  return request<FeatureList>({ method: 'GET', url: '/api/meta/features' });
}

export function getLabels() {
  return request<LabelMap>({ method: 'GET', url: '/api/meta/labels' });
}
