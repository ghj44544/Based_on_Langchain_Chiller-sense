<template>
  <el-card class="panel-card" shadow="never">
    <template #header>
      <div class="card-header">
        <span>预测分布</span>
        <el-radio-group v-model="chartType" size="small">
          <el-radio-button label="bar">柱状图</el-radio-button>
          <el-radio-button label="pie">饼图</el-radio-button>
        </el-radio-group>
      </div>
    </template>

    <el-empty v-if="!entries.length" description="暂无预测分布数据" />
    <div v-else ref="chartRef" class="chart"></div>
  </el-card>
</template>

<script setup lang="ts">
import * as echarts from 'echarts';
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue';

import type { LabelMap } from '@/types/api';

const props = defineProps<{
  distribution: Record<string, number>;
  labels: LabelMap;
}>();

const chartRef = ref<HTMLDivElement | null>(null);
const chartType = ref<'bar' | 'pie'>('bar');
let chart: echarts.ECharts | null = null;

const entries = computed(() =>
  Object.entries(props.distribution || {}).map(([label, value]) => ({
    label,
    name: props.labels[label] ? `${label} - ${props.labels[label]}` : label,
    value,
  })),
);

watch([entries, chartType], () => {
  void renderChart();
});

onMounted(() => {
  void renderChart();
  window.addEventListener('resize', resizeChart);
});

onBeforeUnmount(() => {
  window.removeEventListener('resize', resizeChart);
  chart?.dispose();
});

async function renderChart() {
  await nextTick();
  if (!chartRef.value || !entries.value.length) return;

  chart ||= echarts.init(chartRef.value);
  chart.clear();

  if (chartType.value === 'pie') {
    chart.setOption({
      tooltip: { trigger: 'item' },
      legend: { bottom: 0, type: 'scroll' },
      series: [
        {
          name: '预测数量',
          type: 'pie',
          radius: ['42%', '68%'],
          center: ['50%', '44%'],
          data: entries.value.map((item) => ({ name: item.name, value: item.value })),
          label: { formatter: '{b}\n{d}%' },
        },
      ],
    });
    return;
  }

  chart.setOption({
    grid: { left: 46, right: 24, top: 28, bottom: 88 },
    tooltip: { trigger: 'axis' },
    xAxis: {
      type: 'category',
      data: entries.value.map((item) => item.name),
      axisLabel: { interval: 0, rotate: 28 },
    },
    yAxis: { type: 'value', name: '数量' },
    series: [
      {
        name: '预测数量',
        type: 'bar',
        data: entries.value.map((item) => item.value),
        itemStyle: { color: '#0f8ab8', borderRadius: [4, 4, 0, 0] },
        barMaxWidth: 44,
      },
    ],
  });
}

function resizeChart() {
  chart?.resize();
}
</script>

<style scoped>
.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  color: #172b4d;
  font-weight: 700;
}

.chart {
  width: 100%;
  height: 360px;
}
</style>
