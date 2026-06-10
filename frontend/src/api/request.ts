import axios, { AxiosError, type AxiosRequestConfig } from 'axios';
import type { ApiErrorPayload, ApiResponse } from '@/types/api';

export class ApiServiceError extends Error {
  code: number;
  data?: unknown;
  status?: number;

  constructor(payload: ApiErrorPayload) {
    super(payload.message);
    this.name = 'ApiServiceError';
    this.code = payload.code;
    this.data = payload.data;
    this.status = payload.status;
  }
}

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8010',
  timeout: 120000,
});

export async function request<T>(config: AxiosRequestConfig): Promise<T> {
  try {
    const response = await apiClient.request<ApiResponse<T>>(config);
    const body = response.data;

    if (body.code !== 200) {
      throw new ApiServiceError({
        code: body.code,
        message: body.message || '请求失败',
        data: body.data,
        status: response.status,
      });
    }

    return body.data;
  } catch (error) {
    if (error instanceof ApiServiceError) {
      throw error;
    }

    const axiosError = error as AxiosError<ApiResponse<unknown>>;
    if (axiosError.response?.data) {
      throw new ApiServiceError({
        code: axiosError.response.data.code || axiosError.response.status,
        message: axiosError.response.data.message || '请求失败',
        data: axiosError.response.data.data,
        status: axiosError.response.status,
      });
    }

    if (axiosError.code === 'ECONNABORTED') {
      throw new ApiServiceError({ code: 0, message: '请求超时，请稍后重试' });
    }

    throw new ApiServiceError({ code: 0, message: '后端服务不可用，请确认 FastAPI 已在 127.0.0.1:8010 启动' });
  }
}
