<template>
  <div class="card mb-4">
    <div class="card-header">
      <h5>{{ metric }}</h5>
    </div>
    <div class="card-body">
      <canvas ref="chartCanvas"></canvas>
      <div class="table-responsive mt-4">
        <table class="table table-bordered table-sm">
          <thead>
            <tr>
              <th>Fiscal Year</th>
              <th>Value</th>
              <th>% Change</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in tableRows" :key="item.year">
              <td>{{ item.year }}</td>
              <td>{{ item.value }}</td>
              <td>{{ item.percentageChange }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, computed } from 'vue';
import Chart from 'chart.js/auto';

const props = defineProps(['metric', 'financialData']);
const chartCanvas = ref(null);
let chartInstance = null;

const tableRows = computed(() => {
  const labels = props.financialData.data.map(d => d.fiscal_year);
  const values = props.financialData.data.map(d => d[props.metric]);
  return labels.map((year, i) => {
    const value = values[i];
    let percentageChange = 'N/A';
    if (i > 0 && values[i - 1] != null && values[i - 1] != 0) {
      const prevValue = values[i - 1];
      const change = ((value - prevValue) / Math.abs(prevValue)) * 100;
      percentageChange = change.toFixed(2) + '%';
    }
    return { year, value: value?.toLocaleString() ?? 'N/A', percentageChange };
  });
});

const renderChart = () => {
  if (chartInstance) {
    chartInstance.destroy();
  }
  if (chartCanvas.value) {
    const labels = props.financialData.data.map(d => d.fiscal_year);
    const values = props.financialData.data.map(d => d[props.metric]);
    chartInstance = new Chart(chartCanvas.value.getContext('2d'), {
      type: 'line',
      data: {
        labels,
        datasets: [{
          label: props.metric,
          data: values,
          borderColor: 'rgba(75, 192, 192, 1)',
          tension: 0.1
        }]
      }
    });
  }
};

onMounted(renderChart);
watch(() => props.financialData, renderChart, { deep: true });
</script>
