const { createApp, ref, onMounted, watch, computed } = Vue;

// --- Reusable Components ---

// 1. Financial Chart/Table Card
const FinancialChartCard = {
    props: ['metric', 'financialData'],
    template: `
        <div class="card mb-4">
            <div class="card-header"><h5>{{ metric }}</h5></div>
            <div class="card-body">
                <canvas ref="chartCanvas"></canvas>
                <div class="table-responsive mt-4">
                    <table class="table table-bordered table-sm">
                        <thead>
                            <tr><th>Fiscal Year</th><th>Value</th><th>% Change</th></tr>
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
    `,
    data: () => ({ chartInstance: null }),
    computed: {
        tableRows() {
            const labels = this.financialData.data.map(d => d.fiscal_year);
            const values = this.financialData.data.map(d => d[this.metric]);
            return labels.map((year, i) => {
                const value = values[i];
                let percentageChange = 'N/A';
                if (i > 0 && values[i-1] != null && values[i-1] != 0) {
                    const prevValue = values[i-1];
                    const change = ((value - prevValue) / Math.abs(prevValue)) * 100;
                    percentageChange = change.toFixed(2) + '%';
                }
                return { year, value: value?.toLocaleString() ?? 'N/A', percentageChange };
            });
        }
    },
    methods: {
        renderChart() {
            if (this.chartInstance) this.chartInstance.destroy();
            const labels = this.financialData.data.map(d => d.fiscal_year);
            const values = this.financialData.data.map(d => d[this.metric]);
            this.chartInstance = new Chart(this.$refs.chartCanvas.getContext('2d'), {
                type: 'line',
                data: {
                    labels,
                    datasets: [{ label: this.metric, data: values, borderColor: 'rgba(75, 192, 192, 1)', tension: 0.1 }]
                }
            });
        }
    },
    mounted() { this.renderChart(); },
    watch: { 'financialData': { handler() { this.renderChart(); }, deep: true } },
    beforeUnmount() { if (this.chartInstance) this.chartInstance.destroy(); }
};

// 2. Select2 Component Wrapper for Company Search
const Select2Component = {
    props: ['options', 'modelValue'],
    template: `<select class="form-control" style="width: 100%"></select>`,
    emits: ['update:modelValue'],
    mounted() {
        const vm = this;
        $(this.$el)
            .select2({ placeholder: 'Search for a company...', data: this.options })
            .val(this.modelValue).trigger('change')
            .on('change', function () { vm.$emit('update:modelValue', this.value); });
    },
    watch: {
        options(options) { $(this.$el).empty().select2({ placeholder: 'Search for a company...', data: options }); },
        modelValue(value) { $(this.$el).val(value).trigger('change'); }
    },
    beforeUnmount() { $(this.$el).off().select2('destroy'); }
};

// 3. NEW: Dual Listbox for Metrics Selection
const DualListBox = {
    props: ['options', 'modelValue'],
    emits: ['update:modelValue'],
    template: `
        <div>
            <div class="d-flex justify-content-between mb-1">
                <small class="form-text text-muted w-50 pe-2">Available Columns</small>
                <small class="form-text text-muted w-50 ps-2">Selected Columns</small>
            </div>
            <div class="dual-list-box">
                <div class="list-box-container">
                    <input type="text" class="form-control form-control-sm mb-1" placeholder="Search..." v-model="searchQuery">
                    <div class="list-box">
                        <ul class="list-group" ref="availableList">
                            <li v-for="option in availableOptions" :key="option" class="list-group-item" :data-id="option" @dblclick="select(option)">
                                {{ option }}
                            </li>
                        </ul>
                    </div>
                </div>
                <div class="list-box-container">
                    <div class="list-box">
                        <ul class="list-group" ref="selectedList">
                            <li v-for="option in modelValue" :key="option" class="list-group-item" :data-id="option" @dblclick="deselect(option)">
                                {{ option }}
                            </li>
                        </ul>
                    </div>
                </div>
            </div>
        </div>
    `,
    data() {
        return {
            searchQuery: ''
        };
    },
    computed: {
        availableOptions() {
            const lowerCaseQuery = this.searchQuery.toLowerCase();
            return this.options
                .filter(opt => !this.modelValue.includes(opt))
                .filter(opt => opt.toLowerCase().includes(lowerCaseQuery));
        }
    },
    methods: {
        select(option) {
            this.$emit('update:modelValue', [...this.modelValue, option]);
        },
        deselect(option) {
            this.$emit('update:modelValue', this.modelValue.filter(item => item !== option));
        }
    },
    mounted() {
        const vm = this;
        new Sortable(this.$refs.selectedList, {
            group: 'metrics',
            animation: 150,
            onAdd: function (evt) {
                const newSelected = Array.from(evt.to.children).map(el => el.dataset.id);
                vm.$emit('update:modelValue', newSelected);
            }
        });
        new Sortable(this.$refs.availableList, {
            group: 'metrics',
            animation: 150
        });
    }
};


// --- Main Vue Application ---
createApp({
    components: {
        'financial-chart-card': FinancialChartCard,
        'select2': Select2Component,
        'dual-list-box': DualListBox
    },
    setup() {
        // --- State ---
        const companies = ref([]);
        const selectedCompanyCik = ref(null);
        const allMetrics = ref([]);
        const selectedMetrics = ref([]);
        const financialData = ref({ data: [], columns: [] });
        const isLoading = ref(false);

        // --- Computed ---
        const companyOptions = computed(() => companies.value.map(c => ({ id: c.cik, text: `${c.title} (${c.ticker})` })));

        // --- Methods ---
        const fetchCompanies = async () => {
            try {
                const res = await fetch('/api/companies');
                companies.value = await res.json();
            } catch (e) { console.error("Failed to fetch companies", e); }
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

        // --- Lifecycle & Watchers ---
        onMounted(fetchCompanies);
        watch(selectedCompanyCik, fetchFinancials);

        return { selectedCompanyCik, allMetrics, selectedMetrics, financialData, isLoading, companyOptions };
    },
    template: `
        <h1 class="mb-4">SEC Financial Data Viewer</h1>
        <div class="row">
            <div class="col-md-7">
                <label class="form-label">Select Company</label>
                <select2 :options="companyOptions" v-model="selectedCompanyCik"></select2>
            </div>
            <div class="col-md-5">
                <label class="form-label">Select Financial Metrics</label>
                <dual-list-box v-model="selectedMetrics" :options="allMetrics" :disabled="!selectedCompanyCik || isLoading"></dual-list-box>
            </div>
        </div>

        <div id="charts-container" class="mt-5">
            <div v-if="isLoading" class="text-center">
                <div class="spinner-border" role="status"><span class="visually-hidden">Loading...</span></div>
            </div>
            <div v-else>
                <financial-chart-card
                    v-for="metric in selectedMetrics"
                    :key="metric"
                    :metric="metric"
                    :financial-data="financialData">
                </financial-chart-card>
            </div>
        </div>
    `
}).mount('#app');