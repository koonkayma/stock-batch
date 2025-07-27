<template>
  <div class="container mt-5">
    <h1 class="mb-4">SEC Financial Data Viewer</h1>
    <div class="row">
      <div class="col-md-7">
        <label class="form-label">Select Company</label>
        <Select2 :options="companyOptions" v-model="selectedCompanyCik"></Select2>
      </div>
      <div class="col-md-5">
        <label class="form-label">Select Financial Metrics</label>
        <DualListBox v-model="selectedMetrics" :options="allMetrics" :disabled="!selectedCompanyCik || isLoading"></DualListBox>
      </div>
    </div>

    <div id="charts-container" class="mt-5">
      <div v-if="isLoading" class="text-center">
        <div class="spinner-border" role="status"><span class="visually-hidden">Loading...</span></div>
      </div>
      <div v-else>
        <FinancialChartCard
          v-for="metric in selectedMetrics"
          :key="metric"
          :metric="metric"
          :financial-data="financialData"
        ></FinancialChartCard>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, computed } from 'vue';
import FinancialChartCard from '../components/FinancialChartCard.vue';
import Select2 from '../components/Select2.vue';
import DualListBox from '../components/DualListBox.vue';

const companies = ref([]);
const selectedCompanyCik = ref(null);
const allMetrics = ref([]);
const selectedMetrics = ref([]);
const financialData = ref({ data: [], columns: [] });
const isLoading = ref(false);

const companyOptions = computed(() => companies.value.map(c => ({ id: c.cik, text: `${c.title} (${c.ticker})` })));

const fetchCompanies = async () => {
  try {
    const res = await fetch('/api/companies');
    companies.value = await res.json();
  } catch (e) {
    console.error("Failed to fetch companies", e);
  }
};

const fetchFinancials = async (cik) => {
  if (!cik) return;
  isLoading.value = true;
  selectedMetrics.value = [];
  try {
    const res = await fetch(`/api/financials/${cik}`);
    const data = await res.json();
    financialData.value = data;
    allMetrics.value = data.columns.filter(c => c !== 'fiscal_year').sort();
  } catch (e) {
    console.error("Failed to fetch financials", e);
  } finally {
    isLoading.value = false;
  }
};

onMounted(fetchCompanies);
watch(selectedCompanyCik, fetchFinancials);
</script>
