$(document).ready(function() {
    const companySelect = $('#company-select');
    const metricsSelect = $('#metrics-select');
    const chartsContainer = $('#charts-container');
    let financialData = {};
    let chartInstances = {};

    // Fetch companies and initialize Select2
    $.get('/api/companies', function(data) {
        const formattedData = data.map(company => ({
            id: company.cik,
            text: `${company.title} (${company.ticker})`
        }));

        companySelect.select2({
            placeholder: 'Search for a company by ticker or name',
            data: formattedData
        });
    });

    metricsSelect.select2({
        placeholder: 'Select metrics to plot'
    });

    // Handle company selection
    companySelect.on('select2:select', function(e) {
        const cik = e.params.data.id;
        metricsSelect.val(null).trigger('change');
        metricsSelect.prop('disabled', true);
        chartsContainer.empty();
        if (chartInstances) {
            Object.values(chartInstances).forEach(chart => chart.destroy());
            chartInstances = {};
        }


        $.get(`/api/financials/${cik}`, function(data) {
            financialData = data;
            const metrics = financialData.columns.filter(c => c !== 'fiscal_year');
            metricsSelect.empty();
            metrics.forEach(metric => {
                metricsSelect.append(new Option(metric, metric, false, false));
            });
            metricsSelect.prop('disabled', false);
            metricsSelect.trigger('change');
        });
    });

    // Handle metric selection
    metricsSelect.on('change', function() {
        const selectedMetrics = $(this).val() || [];
        
        // Remove charts for deselected metrics
        Object.keys(chartInstances).forEach(metric => {
            if (!selectedMetrics.includes(metric)) {
                $(`#chart-card-${metric}`).remove();
                chartInstances[metric].destroy();
                delete chartInstances[metric];
            }
        });

        selectedMetrics.forEach(metric => {
            if (!chartInstances[metric]) {
                renderChartAndTable(metric);
            }
        });
    });

    function renderChartAndTable(metric) {
        const labels = financialData.data.map(d => d.fiscal_year);
        const values = financialData.data.map(d => d[metric]);

        // Create card for chart and table
        const chartCard = `
            <div class="card mb-4" id="chart-card-${metric}">
                <div class="card-header">
                    <h5>${metric}</h5>
                </div>
                <div class="card-body">
                    <canvas id="chart-${metric}"></canvas>
                    <div class="table-responsive mt-4">
                        <table class="table table-bordered table-sm">
                            <thead>
                                <tr>
                                    <th>Fiscal Year</th>
                                    <th>Value</th>
                                    <th>% Change</th>
                                </tr>
                            </thead>
                            <tbody id="table-body-${metric}">
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        `;
        chartsContainer.append(chartCard);

        // Render Chart
        const ctx = document.getElementById(`chart-${metric}`).getContext('2d');
        chartInstances[metric] = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: metric,
                    data: values,
                    borderColor: 'rgba(75, 192, 192, 1)',
                    tension: 0.1
                }]
            }
        });

        // Populate Table
        const tableBody = $(`#table-body-${metric}`);
        for (let i = 0; i < labels.length; i++) {
            const year = labels[i];
            const value = values[i];
            let percentageChange = 'N/A';
            if (i > 0 && values[i-1] !== 0 && values[i-1] !== null) {
                const prevValue = values[i-1];
                const change = ((value - prevValue) / prevValue) * 100;
                percentageChange = change.toFixed(2) + '%';
            }
            const row = `
                <tr>
                    <td>${year}</td>
                    <td>${value !== null ? value.toLocaleString() : 'N/A'}</td>
                    <td>${percentageChange}</td>
                </tr>
            `;
            tableBody.append(row);
        }
    }
});
