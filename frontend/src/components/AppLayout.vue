<template>
  <el-container class="app-shell">
    <el-aside class="app-aside" width="232px">
      <div class="brand">
        <div class="brand-mark">CS</div>
        <div>
          <div class="brand-title">Chiller Sense</div>
          <div class="brand-subtitle">故障诊断工作台</div>
        </div>
      </div>

      <el-menu :default-active="route.path" router class="nav-menu">
        <el-menu-item index="/">
          <el-icon><DataLine /></el-icon>
          <span>系统工作台</span>
        </el-menu-item>
        <el-menu-item index="/diagnosis/upload">
          <el-icon><UploadFilled /></el-icon>
          <span>上传诊断</span>
        </el-menu-item>
        <el-menu-item index="/diagnosis/result">
          <el-icon><Histogram /></el-icon>
          <span>诊断结果</span>
        </el-menu-item>
        <el-menu-item index="/reports">
          <el-icon><Document /></el-icon>
          <span>诊断报告</span>
        </el-menu-item>
        <el-menu-item index="/chat">
          <el-icon><ChatDotRound /></el-icon>
          <span>诊断问答</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header class="app-header">
        <div>
          <h1>冷水机组故障诊断智能系统</h1>
          <p>对接 FastAPI / MATLAB ultra 模型，上传数据后生成诊断结果与报告。</p>
        </div>
        <el-tag type="info" effect="plain">API: {{ apiBaseUrl }}</el-tag>
      </el-header>

      <el-main class="app-main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { ChatDotRound, DataLine, Document, Histogram, UploadFilled } from '@element-plus/icons-vue';
import { useRoute } from 'vue-router';

const route = useRoute();
const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';
</script>

<style scoped>
.app-shell {
  min-height: 100vh;
}

.app-aside {
  border-right: 1px solid #d8e4f0;
  background: #f8fbff;
}

.brand {
  display: flex;
  align-items: center;
  gap: 12px;
  height: 76px;
  padding: 0 18px;
  border-bottom: 1px solid #d8e4f0;
}

.brand-mark {
  display: grid;
  width: 40px;
  height: 40px;
  place-items: center;
  border-radius: 8px;
  background: #0f6b9f;
  color: #fff;
  font-weight: 700;
}

.brand-title {
  color: #172b4d;
  font-size: 16px;
  font-weight: 700;
}

.brand-subtitle {
  margin-top: 2px;
  color: #7a869a;
  font-size: 12px;
}

.nav-menu {
  border-right: 0;
  background: transparent;
}

.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  height: 76px;
  padding: 0 24px;
  border-bottom: 1px solid #d8e4f0;
  background: #fff;
}

.app-header h1 {
  margin: 0;
  color: #172b4d;
  font-size: 20px;
}

.app-header p {
  margin: 5px 0 0;
  color: #6b778c;
  font-size: 13px;
}

.app-main {
  padding: 20px 24px 28px;
}

@media (max-width: 860px) {
  .app-shell {
    display: block;
  }

  .app-aside {
    width: 100% !important;
  }

  .brand {
    height: 64px;
  }

  .nav-menu {
    display: flex;
    overflow-x: auto;
  }

  .app-header {
    align-items: flex-start;
    flex-direction: column;
    height: auto;
    padding: 14px 16px;
  }

  .app-main {
    padding: 16px;
  }
}
</style>
