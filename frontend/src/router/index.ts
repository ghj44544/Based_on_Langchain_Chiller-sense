import { createRouter, createWebHistory } from 'vue-router';

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'dashboard',
      component: () => import('@/views/Dashboard.vue'),
      meta: { title: '系统工作台' },
    },
    {
      path: '/diagnosis/upload',
      name: 'diagnosis-upload',
      component: () => import('@/views/DiagnosisUpload.vue'),
      meta: { title: '上传诊断' },
    },
    {
      path: '/diagnosis/result',
      name: 'diagnosis-result',
      component: () => import('@/views/DiagnosisResult.vue'),
      meta: { title: '诊断结果' },
    },
    {
      path: '/reports',
      name: 'reports',
      component: () => import('@/views/Reports.vue'),
      meta: { title: '诊断报告' },
    },
    {
      path: '/chat',
      name: 'chat',
      component: () => import('@/views/Chat.vue'),
      meta: { title: '诊断问答' },
    },
  ],
});

export default router;
