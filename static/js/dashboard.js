// Dashboard JavaScript - DIPERBAIKI untuk menampilkan insights
class IPHDashboard {
    constructor() {
        this.API_BASE_URL = 'http://localhost:5001';
        this.DEBUG_MODE = true;
        this.currentModel = 'Random_Forest';
        this.currentTimeRange = 3;
        this.charts = {};
        this.isLoading = false;
        this.maxRetries = 10;
        this.retryDelay = 2000;
        this.modelInsights = {};
        this.currentInsights = [];
        this.init();
    }
    
    debugLog(message, data = null) {
        if (this.DEBUG_MODE) {
            console.log(`🔍 DEBUG: ${message}`, data);
        }
    }

    async init() {
        try {
            this.debugLog('Starting dashboard initialization');
            this.showLoading(true);
            
            const initTimeout = setTimeout(() => {
                this.showError('Dashboard initialization timeout. Silakan refresh halaman.');
                this.showLoading(false);
            }, 45000);
            
            this.debugLog('Step 1: Checking API status with retries');
            await this.waitForAPIWithRetries();
            
            this.debugLog('Step 2: Loading available models with insights');
            await this.loadAvailableModels();
            
            this.debugLog('Step 3: Loading KPI data');
            await this.loadKPIData();
            
            this.debugLog('Step 4: Loading forecast data');
            await this.loadForecastData();
            
            this.debugLog('Step 5: Setting up event listeners');
            this.setupEventListeners();
            
            this.debugLog('Step 6: Starting auto refresh');
            this.startAutoRefresh();
            
            clearTimeout(initTimeout);
            this.showLoading(false);
            this.debugLog('Dashboard initialization completed successfully');
            
        } catch (error) {
            this.debugLog('Dashboard initialization failed', error);
            this.showError(`Dashboard gagal dimuat: ${error.message}`);
            this.showLoading(false);
            this.showRetryOption();
        }
    }

    async waitForAPIWithRetries() {
        for (let attempt = 1; attempt <= this.maxRetries; attempt++) {
            try {
                this.debugLog(`Checking API status (attempt ${attempt}/${this.maxRetries})`);
                
                const response = await fetch(`${this.API_BASE_URL}/api/status`, {
                    method: 'GET',
                    mode: 'cors',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    signal: AbortSignal.timeout(8000)
                });
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                
                const data = await response.json();
                this.debugLog(`API Status (attempt ${attempt}):`, data);
                
                if (data.initialized) {
                    this.debugLog('API server is ready and initialized!');
                    this.showSuccess('API connection established');
                    return true;
                } else {
                    this.debugLog(`API server not fully initialized yet. Error: ${data.error}`);
                    throw new Error(`API not initialized: ${data.error}`);
                }
                
            } catch (error) {
                this.debugLog(`API check attempt ${attempt} failed:`, error.message);
                
                if (attempt === this.maxRetries) {
                    throw new Error(`API server tidak dapat diakses setelah ${this.maxRetries} percobaan.`);
                }
                
                this.updateLoadingMessage(`Menunggu API server... (${attempt}/${this.maxRetries})`);
                await new Promise(resolve => setTimeout(resolve, this.retryDelay));
            }
        }
    }

    updateLoadingMessage(message) {
        const elements = ['predictionValue', 'accuracyValue', 'lastChangeValue'];
        elements.forEach(id => {
            const element = document.getElementById(id);
            if (element && element.textContent.includes('Loading')) {
                element.textContent = message;
            }
        });
    }

    async apiRequest(endpoint, options = {}) {
        try {
            const url = `${this.API_BASE_URL}${endpoint}`;
            this.debugLog(`Making API request to: ${url}`);
            
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 15000);
            
            const response = await fetch(url, {
                ...options,
                signal: controller.signal,
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                }
            });
            
            clearTimeout(timeoutId);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            this.debugLog(`API Response received from ${endpoint}:`, data);
            
            if (data.success === false) {
                throw new Error(data.error || 'API request failed');
            }
            
            return data;
            
        } catch (error) {
            if (error.name === 'AbortError') {
                throw new Error('Request timeout - API server mungkin tidak responsif');
            }
            
            this.debugLog(`API Request failed for ${endpoint}:`, error);
            throw error;
        }
    }

    showLoading(show) {
        const elements = ['predictionValue', 'accuracyValue', 'lastChangeValue'];
        elements.forEach(id => {
            const element = document.getElementById(id);
            if (element) {
                element.textContent = show ? 'Loading...' : element.textContent;
            }
        });
    }

    async loadAvailableModels() {
        try {
            this.debugLog('Loading models with insights...');
            const data = await this.apiRequest('/api/models');
            
            const modelSelect = document.getElementById('modelSelect');
            if (!modelSelect) {
                throw new Error('Model select element not found');
            }
            
            modelSelect.innerHTML = '';
            
            // Store insights
            this.modelInsights = data.model_insights || {};
            this.debugLog('Model insights loaded:', this.modelInsights);
            
            // Display model recommendation
            if (data.recommendation) {
                this.displayModelRecommendation(data.recommendation);
                this.debugLog('Model recommendation displayed:', data.recommendation);
            }
            
            data.models.forEach(model => {
                const option = document.createElement('option');
                option.value = model;
                option.textContent = this.getModelDisplayName(model);
                
                // Add performance indicator
                if (this.modelInsights[model] && this.modelInsights[model].performance) {
                    const accuracy = this.modelInsights[model].performance.recent_accuracy;
                    const indicator = accuracy < 0.9 ? '🟢' : accuracy < 1.2 ? '🟡' : '🔴';
                    option.textContent += ` ${indicator}`;
                }
                
                if (model === data.default) {
                    option.selected = true;
                    this.currentModel = model;
                }
                modelSelect.appendChild(option);
            });
            
            this.debugLog('Available models loaded with insights:', data.models);
            
        } catch (error) {
            this.debugLog('Error loading models:', error);
            this.showError('Gagal memuat daftar model: ' + error.message);
            throw error;
        }
    }

    displayModelRecommendation(recommendation) {
        const container = document.getElementById('modelRecommendation');
        if (!container) {
            this.debugLog('Model recommendation container not found');
            return;
        }
        
        const recommendedModel = this.getModelDisplayName(recommendation.recommended_model);
        
        container.innerHTML = `
            <div class="recommendation-card">
                <div class="recommendation-header">
                    <span class="recommendation-icon">🏆</span>
                    <span class="recommendation-title">Model Rekomendasi</span>
                </div>
                <div class="recommendation-content">
                    <div class="recommended-model">${recommendedModel}</div>
                    <div class="recommendation-reason">${recommendation.reason}</div>
                    <div class="recommendation-score">Score: ${recommendation.score}/100</div>
                </div>
            </div>
        `;
        
        this.debugLog('Model recommendation displayed successfully');
    }

    getModelDisplayName(model) {
        const displayNames = {
            'Random_Forest': 'Random Forest',
            'LightGBM': 'LightGBM',
            'KNN': 'KNN',
            'XGBoost_Advanced': 'XGBoost Advanced'
        };
        return displayNames[model] || model;
    }

    async loadKPIData() {
        try {
            const data = await this.apiRequest('/api/kpi');
            
            this.updateKPIValue('predictionValue', data.next_week_prediction, '%');
            this.updateKPIValue('accuracyValue', data.model_accuracy, '', 2);
            this.updateKPIValue('lastChangeValue', data.last_change, '%');
            
            // Update change indicators
            const changeElement = document.getElementById('predictionChange');
            if (changeElement) {
                if (data.change_from_previous > 0) {
                    changeElement.className = 'kpi-change positive';
                    changeElement.innerHTML = `<i class="arrow up"></i> ${data.change_from_previous.toFixed(2)}% dari minggu lalu`;
                } else if (data.change_from_previous < 0) {
                    changeElement.className = 'kpi-change negative';
                    changeElement.innerHTML = `<i class="arrow down"></i> ${Math.abs(data.change_from_previous).toFixed(2)}% dari minggu lalu`;
                } else {
                    changeElement.className = 'kpi-change neutral';
                    changeElement.innerHTML = `<i class="arrow stable"></i> Tidak ada perubahan`;
                }
            }
            
            const lastUpdateElement = document.getElementById('lastUpdate');
            if (lastUpdateElement) {
                lastUpdateElement.textContent = data.last_update;
            }
            
            this.updateStatusIndicator(data.next_week_prediction, data.market_status);
            
            // Display quick insights
            if (data.quick_insights && data.quick_insights.length > 0) {
                this.displayQuickInsights(data.quick_insights);
                this.debugLog('Quick insights displayed:', data.quick_insights);
            }
            
            this.debugLog('KPI data loaded successfully');
            
        } catch (error) {
            this.debugLog('Error loading KPI data:', error);
            this.showError('Gagal memuat data KPI: ' + error.message);
            throw error;
        }
    }

    displayQuickInsights(insights) {
        const container = document.getElementById('quickInsights');
        if (!container) {
            this.debugLog('Quick insights container not found');
            return;
        }
        
        if (!insights || insights.length === 0) {
            container.innerHTML = '';
            return;
        }
        
        container.innerHTML = insights.map(insight => `
            <div class="quick-insight ${insight.type}">
                <span class="insight-message">${insight.message}</span>
            </div>
        `).join('');
        
        this.debugLog('Quick insights displayed successfully');
    }

    updateKPIValue(elementId, value, suffix = '', decimals = 2) {
        const element = document.getElementById(elementId);
        if (!element) return;
        
        const formattedValue = `${value > 0 ? '+' : ''}${value.toFixed(decimals)}${suffix}`;
        
        element.classList.add('updating');
        setTimeout(() => {
            element.textContent = formattedValue;
            element.classList.remove('updating');
        }, 200);
    }

    updateStatusIndicator(prediction, marketStatus = 'normal') {
        const statusLight = document.getElementById('statusLight');
        const statusText = document.getElementById('statusText');
        
        if (!statusLight || !statusText) return;
        
        let status = 'normal';
        let text = 'Normal';
        
        if (marketStatus === 'volatile') {
            status = 'danger';
            text = 'Volatil';
        } else if (Math.abs(prediction) > 3) {
            status = 'danger';
            text = 'Siaga';
        } else if (Math.abs(prediction) > 1) {
            status = 'warning';
            text = 'Waspada';
        }
        
        statusLight.className = `status-light ${status}`;
        statusText.textContent = text;
    }

    async loadForecastData() {
        try {
            this.debugLog(`Loading forecast data for model: ${this.currentModel}, time range: ${this.currentTimeRange}`);
            
            const chartTitle = document.querySelector('.chart-title');
            if (chartTitle) {
                chartTitle.textContent = `Memuat data untuk ${this.getModelDisplayName(this.currentModel)}...`;
            }
            
            // Show loading in insights container
            this.showInsightsLoading();
            
            const params = this.currentTimeRange ? `?months=${this.currentTimeRange}` : '';
            const data = await this.apiRequest(`/api/forecast/${this.currentModel}${params}`);
            
            this.debugLog('Forecast data received:', data);
            
            if (!data.historical || !data.forecast || !data.model_info) {
                throw new Error('Invalid forecast data structure');
            }
            
            this.renderForecastChart(data);
            this.updateKPIValue('accuracyValue', data.model_info.mae, '', 3);
            
            if (chartTitle) {
                chartTitle.textContent = `Forecasting Indikator Perubahan Harga - Model: ${this.getModelDisplayName(this.currentModel)}`;
            }
            
            // Display insights - IMPROVED ERROR HANDLING
            if (data.insights) {
                this.debugLog('Insights received from API:', data.insights);
                this.displayInsights(data.insights);
            } else {
                this.debugLog('No insights received from API, trying to generate fallback');
                // Show fallback insights
                const fallbackInsights = {
                    model_insights: [{
                        type: 'info',
                        icon: '📊',
                        title: 'Model Aktif',
                        message: `Model ${this.getModelDisplayName(this.currentModel)} sedang digunakan untuk prediksi.`
                    }],
                    market_insights: [{
                        type: 'info',
                        icon: '📈',
                        title: 'Data Tersedia',
                        message: `Menggunakan ${data.historical.length} data historis untuk analisis.`
                    }]
                };
                this.displayInsights(fallbackInsights);
            }
            
            this.debugLog('Forecast data loaded successfully');
            
        } catch (error) {
            this.debugLog('Error loading forecast data:', error);
            this.showInsightsError(error.message);
            
            const chartContainer = document.querySelector('.chart-wrapper');
            if (chartContainer) {
                chartContainer.innerHTML = `
                    <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; text-align: center; color: #ef4444;">
                        <div style="font-size: 3rem; margin-bottom: 1rem;">⚠️</div>
                        <h3 style="margin-bottom: 0.5rem;">Gagal Memuat Data Forecast</h3>
                        <p style="color: #6b7280; margin-bottom: 1rem;">${error.message}</p>
                        <button onclick="window.dashboard.loadForecastData()" style="padding: 0.5rem 1rem; background: #3b82f6; color: white; border: none; border-radius: 0.5rem; cursor: pointer;">
                            🔄 Coba Lagi
                        </button>
                    </div>
                `;
            }
            
            this.showError(`Gagal memuat data forecast: ${error.message}`);
        }
    }

    showInsightsLoading() {
        const container = document.getElementById('insightsContainer');
        if (!container) return;
        
        container.innerHTML = `
            <div class="insights-loading">
                <span>Memuat insight...</span>
            </div>
        `;
    }

    showInsightsEmpty() {
        const container = document.getElementById('insightsContainer');
        if (!container) return;
        
        container.innerHTML = `
            <div class="insights-empty">
                <div class="insights-empty-icon">🤔</div>
                <p>Tidak ada insight yang tersedia untuk model ini.</p>
            </div>
        `;
    }

    showInsightsError(message) {
        const container = document.getElementById('insightsContainer');
        if (!container) return;
        
        container.innerHTML = `
            <div class="insights-empty">
                <div class="insights-empty-icon">⚠️</div>
                <p>Gagal memuat insight: ${message}</p>
                <button onclick="window.dashboard.loadForecastData()" style="margin-top: 1rem; padding: 0.5rem 1rem; background: #3b82f6; color: white; border: none; border-radius: 0.5rem; cursor: pointer;">
                    🔄 Coba Lagi
                </button>
            </div>
        `;
    }

    displayInsights(insights) {
        const container = document.getElementById('insightsContainer');
        if (!container) {
            this.debugLog('Insights container not found');
            return;
        }
        
        this.debugLog('Displaying insights:', insights);
        
        // Check if insights object exists and has data
        if (!insights || ((!insights.model_insights || insights.model_insights.length === 0) && 
                         (!insights.market_insights || insights.market_insights.length === 0))) {
            this.showInsightsEmpty();
            return;
        }
        
        let insightHTML = '';
        
        // Model insights
        if (insights.model_insights && insights.model_insights.length > 0) {
            insightHTML += `
                <div class="insights-section">
                    <h4 class="insights-title">💡 Insight Model</h4>
                    <div class="insights-list">
                        ${insights.model_insights.map(insight => `
                            <div class="insight-item ${insight.type || 'info'}">
                                <span class="insight-icon">${insight.icon || '💡'}</span>
                                <div class="insight-content">
                                    <div class="insight-title">${insight.title || 'Insight'}</div>
                                    <div class="insight-message">${insight.message || 'No message'}</div>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
        }
        
        // Market insights
        if (insights.market_insights && insights.market_insights.length > 0) {
            insightHTML += `
                <div class="insights-section">
                    <h4 class="insights-title">📊 Insight Pasar</h4>
                    <div class="insights-list">
                        ${insights.market_insights.map(insight => `
                            <div class="insight-item ${insight.type || 'info'}">
                                <span class="insight-icon">${insight.icon || '📊'}</span>
                                <div class="insight-content">
                                    <div class="insight-title">${insight.title || 'Insight'}</div>
                                    <div class="insight-message">${insight.message || 'No message'}</div>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
        }
        
        // If still no insights, show empty state
        if (!insightHTML) {
            this.showInsightsEmpty();
            return;
        }
        
        container.innerHTML = insightHTML;
        this.debugLog('Insights displayed successfully');
    }
    
    renderForecastChart(data) {
        const ctx = document.getElementById('forecastChart');
        if (!ctx) {
            this.debugLog('Chart canvas not found');
            return;
        }

        // Destroy existing chart
        if (this.charts.forecast) {
            this.charts.forecast.destroy();
        }

        // Prepare data
        const labels = [];
        const historicalValues = [];
        const forecastValues = [];
        const upperBoundValues = [];
        const lowerBoundValues = [];

        // Add historical data
        data.historical.forEach(item => {
            labels.push(item.date);
            historicalValues.push(item.value);
            forecastValues.push(null);
            upperBoundValues.push(null);
            lowerBoundValues.push(null);
        });

        // Add forecast data
        data.forecast.forEach(item => {
            labels.push(item.date);
            historicalValues.push(null);
            forecastValues.push(item.prediction);
            upperBoundValues.push(item.upper_bound);
            lowerBoundValues.push(item.lower_bound);
        });

        // Connect last historical point to first forecast point
        if (data.historical.length > 0 && data.forecast.length > 0) {
            const lastHistoricalIndex = data.historical.length - 1;
            const firstForecastIndex = data.historical.length;
            
            forecastValues[lastHistoricalIndex] = data.historical[data.historical.length - 1].value;
            forecastValues[firstForecastIndex] = data.forecast[0].prediction;
        }

        // Model colors
        const modelColors = {
            'Random_Forest': { main: '#2E8B57', light: 'rgba(46, 139, 87, 0.2)' },
            'LightGBM': { main: '#4169E1', light: 'rgba(65, 105, 225, 0.2)' },
            'KNN': { main: '#FF6347', light: 'rgba(255, 99, 71, 0.2)' },
            'XGBoost_Advanced': { main: '#9932CC', light: 'rgba(153, 50, 204, 0.2)' }
        };

        const modelColor = modelColors[this.currentModel] || modelColors['Random_Forest'];

        this.charts.forecast = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Data Historis',
                        data: historicalValues,
                        borderColor: '#1f77b4',
                        backgroundColor: 'rgba(31, 119, 180, 0.1)',
                        fill: false,
                        tension: 0.1,
                        pointRadius: 3,
                        pointHoverRadius: 6,
                        borderWidth: 2,
                        pointBackgroundColor: '#1f77b4',
                        pointBorderColor: '#1f77b4',
                        spanGaps: false
                    },
                    {
                        label: 'Forecast',
                        data: forecastValues,
                        borderColor: modelColor.main,
                        backgroundColor: modelColor.light,
                        fill: false,
                        tension: 0.1,
                        borderDash: [5, 5],
                        pointRadius: 4,
                        pointHoverRadius: 7,
                        borderWidth: 3,
                        pointBackgroundColor: modelColor.main,
                        pointBorderColor: modelColor.main,
                        spanGaps: true
                    },
                    {
                        label: 'Rentang Kepercayaan (Lower)',
                        data: lowerBoundValues,
                        borderColor: 'rgba(255, 165, 0, 0.3)',
                        backgroundColor: 'rgba(255, 165, 0, 0.1)',
                        fill: '+1',
                        tension: 0.1,
                        pointRadius: 0,
                        borderWidth: 1,
                        spanGaps: true
                    },
                    {
                        label: 'Rentang Kepercayaan (90%)',
                        data: upperBoundValues,
                        borderColor: 'rgba(255, 165, 0, 0.3)',
                        backgroundColor: 'rgba(255, 165, 0, 0.1)',
                        fill: false,
                        tension: 0.1,
                        pointRadius: 0,
                        borderWidth: 1,
                        spanGaps: true
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: {
                    duration: 1000,
                    easing: 'easeInOutQuart'
                },
                plugins: {
                    title: {
                        display: true,
                        text: `Forecasting IPH - ${this.getModelDisplayName(this.currentModel)}`,
                        font: {
                            size: 16,
                            weight: 'bold'
                        },
                        color: '#2c3e50',
                        padding: 20
                    },
                    legend: {
                        display: true,
                        position: 'top',
                        labels: {
                            usePointStyle: true,
                            padding: 20,
                            filter: function(legendItem) {
                                return !legendItem.text.includes('Lower');
                            }
                        }
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: '#fff',
                        bodyColor: '#fff',
                        borderColor: modelColor.main,
                        borderWidth: 1,
                        callbacks: {
                            title: function(context) {
                                return `Tanggal: ${context[0].label}`;
                            },
                            label: function(context) {
                                if (context.dataset.label.includes('Lower') || 
                                    context.parsed.y === null) {
                                    return null;
                                }
                                let label = context.dataset.label || '';
                                if (label) {
                                    label += ': ';
                                }
                                label += context.parsed.y.toFixed(2) + '%';
                                return label;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: 'Tanggal',
                            font: {
                                size: 14,
                                weight: 'bold'
                            }
                        },
                        grid: {
                            display: true,
                            color: 'rgba(0,0,0,0.1)'
                        },
                        ticks: {
                            maxRotation: 45,
                            minRotation: 45,
                            callback: function(value, index) {
                                if (index % 3 === 0) {
                                    return this.getLabelForValue(value);
                                }
                                return '';
                            }
                        }
                    },
                    y: {
                        title: {
                            display: true,
                            text: 'Indikator Perubahan Harga (%)',
                            font: {
                                size: 14,
                                weight: 'bold'
                            }
                        },
                        grid: {
                            display: true,
                            color: 'rgba(0,0,0,0.1)'
                        },
                        ticks: {
                            callback: function(value) {
                                return value.toFixed(1) + '%';
                            }
                        }
                    }
                },
                interaction: {
                    mode: 'nearest',
                    axis: 'x',
                    intersect: false
                }
            }
        });

        this.debugLog('Chart rendered successfully');
    }

    setupEventListeners() {
        // Model selection
        const modelSelect = document.getElementById('modelSelect');
        if (modelSelect) {
            modelSelect.addEventListener('change', (e) => {
                this.debugLog('Model changed from', this.currentModel, 'to', e.target.value);
                this.currentModel = e.target.value;
                
                modelSelect.classList.add('updating');
                setTimeout(() => {
                    modelSelect.classList.remove('updating');
                }, 500);
                
                this.loadForecastData();
            });
        }

        // Time range buttons
        document.querySelectorAll('.time-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                document.querySelectorAll('.time-btn').forEach(b => b.classList.remove('active'));
                e.target.classList.add('active');
                
                const range = e.target.dataset.range;
                this.currentTimeRange = range === 'all' ? null : parseInt(range);
                this.debugLog('Time range changed to:', this.currentTimeRange);
                
                this.loadForecastData();
            });
        });

        // What-if analysis
        const whatIfInput = document.getElementById('whatIfInput');
        if (whatIfInput) {
            whatIfInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.simulateForecast();
                }
            });
        }

        // Model comparison button
        const compareBtn = document.getElementById('compareModels');
        if (compareBtn) {
            compareBtn.addEventListener('click', () => {
                this.showModelComparison();
            });
        }
    }

    async showModelComparison() {
        try {
            const data = await this.apiRequest('/api/insights/comparison');
            this.displayModelComparisonModal(data);
        } catch (error) {
            this.showError('Gagal memuat perbandingan model: ' + error.message);
        }
    }

    displayModelComparisonModal(data) {
        const modal = document.createElement('div');
        modal.className = 'modal-overlay';
        
        let comparisonHTML = '<div class="model-comparison-grid">';
        
        Object.entries(data.model_comparisons).forEach(([modelName, comparison]) => {
            if (comparison.performance) {
                const perf = comparison.performance;
                comparisonHTML += `
                    <div class="model-comparison-card">
                        <h4>${this.getModelDisplayName(modelName)}</h4>
                        <div class="comparison-metrics">
                            <div class="metric">
                                <span class="metric-label">Prediksi:</span>
                                <span class="metric-value">${perf.prediction.toFixed(2)}%</span>
                            </div>
                            <div class="metric">
                                <span class="metric-label">Confidence:</span>
                                <span class="metric-value">${perf.confidence_level}</span>
                            </div>
                            <div class="metric">
                                <span class="metric-label">Akurasi:</span>
                                <span class="metric-value">${perf.recent_accuracy.toFixed(2)}</span>
                            </div>
                        </div>
                        <div class="comparison-insights">
                            ${comparison.insights.slice(0, 2).map(insight => `
                                <div class="mini-insight ${insight.type}">
                                    ${insight.icon} ${insight.title}
                                </div>
                            `).join('')}
                        </div>
                    </div>
                `;
            }
        });
        
        comparisonHTML += '</div>';
        
        modal.innerHTML = `
            <div class="modal-content large">
                <div class="modal-header">
                    <h3>📊 Perbandingan Model</h3>
                    <button class="modal-close" onclick="this.parentElement.parentElement.parentElement.remove()">×</button>
                </div>
                <div class="modal-body">
                    ${data.recommendation ? `
                        <div class="recommendation-summary">
                            <h4>🏆 Rekomendasi: ${this.getModelDisplayName(data.recommendation.recommended_model)}</h4>
                            <p>${data.recommendation.reason}</p>
                        </div>
                    ` : ''}
                    ${comparisonHTML}
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        setTimeout(() => {
            if (modal.parentElement) {
                modal.remove();
            }
        }, 30000);
    }

    async simulateForecast() {
        const input = document.getElementById('whatIfInput');
        const value = parseFloat(input.value);
        
        if (isNaN(value)) {
            this.showError('Masukkan nilai IPH yang valid');
            return;
        }
        
        try {
            const data = await this.apiRequest('/api/what-if', {
                method: 'POST',
                body: JSON.stringify({
                    current_iph: value,
                    model: this.currentModel
                })
            });
            
            this.showWhatIfResult(data);
            
        } catch (error) {
            this.debugLog('Error in what-if analysis:', error);
            this.showError('Gagal melakukan simulasi: ' + error.message);
        }
    }

    showWhatIfResult(data) {
        const modal = document.createElement('div');
        modal.className = 'modal-overlay';
        
        let insightsHTML = '';
        if (data.insights && data.insights.length > 0) {
            insightsHTML = `
                <div class="what-if-insights">
                    <h4>💡 Insight Skenario</h4>
                    ${data.insights.map(insight => `
                        <div class="insight-item ${insight.type}">
                            <span class="insight-icon">${insight.icon}</span>
                            <div class="insight-content">
                                <div class="insight-title">${insight.title || 'Insight'}</div>
                                <div class="insight-message">${insight.message}</div>
                            </div>
                        </div>
                    `).join('')}
                </div>
            `;
        }
        
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h3>🔮 Hasil Analisis What-If</h3>
                    <button class="modal-close" onclick="this.parentElement.parentElement.parentElement.remove()">×</button>
                </div>
                <div class="modal-body">
                    <p><strong>${data.scenario}</strong></p>
                    <div class="result-grid">
                        <div class="result-item">
                            <span class="result-label">Prediksi:</span>
                            <span class="result-value">${data.prediction.toFixed(2)}%</span>
                        </div>
                        <div class="result-item">
                            <span class="result-label">Rentang:</span>
                            <span class="result-value">${data.lower_bound.toFixed(2)}% - ${data.upper_bound.toFixed(2)}%</span>
                        </div>
                        <div class="result-item">
                            <span class="result-label">Model:</span>
                            <span class="result-value">${this.getModelDisplayName(data.model_used)}</span>
                        </div>
                        ${data.comparison_with_normal ? `
                        <div class="result-item">
                            <span class="result-label">Perubahan dari Normal:</span>
                            <span class="result-value">${data.comparison_with_normal.difference.toFixed(2)}%</span>
                        </div>
                        ` : ''}
                    </div>
                    ${insightsHTML}
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        setTimeout(() => {
            if (modal.parentElement) {
                modal.remove();
            }
        }, 15000);
    }

    async downloadData() {
        try {
            const data = await this.apiRequest('/api/download-data');
            
            const blob = new Blob([data.csv_data], { type: 'text/csv' });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = data.filename;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
            
            this.showSuccess('Data berhasil diunduh');
            
        } catch (error) {
            this.debugLog('Error downloading data:', error);
            this.showError('Gagal mengunduh data: ' + error.message);
        }
    }

    startAutoRefresh() {
        setInterval(() => {
            this.debugLog('Auto-refreshing KPI data...');
            this.loadKPIData().catch(error => {
                this.debugLog('Auto-refresh failed:', error);
            });
        }, 5 * 60 * 1000);
    }

    showRetryOption() {
        const chartContainer = document.querySelector('.chart-wrapper');
        if (chartContainer) {
            chartContainer.innerHTML = `
                <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; text-align: center;">
                    <div style="font-size: 3rem; margin-bottom: 1rem;">⚠️</div>
                    <h3 style="margin-bottom: 1rem; color: #ef4444;">Dashboard Gagal Dimuat</h3>
                    <p style="color: #6b7280; margin-bottom: 1rem;">API server tidak dapat diakses atau belum selesai initialize</p>
                    <button onclick="window.location.reload()" style="padding: 0.75rem 1.5rem; background: #3b82f6; color: white; border: none; border-radius: 0.5rem; cursor: pointer; font-size: 1rem; margin-right: 1rem;">
                        🔄 Refresh Dashboard
                    </button>
                    <button onclick="window.dashboard.testAPIConnection()" style="padding: 0.75rem 1.5rem; background: #10b981; color: white; border: none; border-radius: 0.5rem; cursor: pointer; font-size: 1rem;">
                        🧪 Test API Connection
                    </button>
                </div>
            `;
        }
    }

    async testAPIConnection() {
        try {
            this.debugLog('Testing API connection...');
            
            const response = await fetch(`${this.API_BASE_URL}/api/health`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                },
                signal: AbortSignal.timeout(10000)
            });
            
            const data = await response.json();
            this.debugLog('API Health Check:', data);
            
            if (response.ok) {
                let message = `✅ API Connection OK!\n\nStatus: ${data.status}\nModels: ${data.models_loaded}\nData: ${data.data_points} records`;
                
                if (data.insight_analyzer) {
                    message += `\nInsight Analyzer: ${data.insight_analyzer}`;
                }
                
                alert(message);
            } else {
                alert(`❌ API Error!\n\nStatus: ${response.status}\nError: ${data.error}`);
            }
            
        } catch (error) {
            this.debugLog('API test failed:', error);
            alert(`❌ API Connection Failed!\n\nError: ${error.message}\n\nPastikan API server berjalan di localhost:5001`);
        }
    }

    showError(message) {
        this.debugLog('Error:', message);
        this.showNotification(message, 'error');
    }

    showSuccess(message) {
        this.debugLog('Success:', message);
        this.showNotification(message, 'success');
    }

    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <span class="notification-icon">${type === 'error' ? '❌' : type === 'success' ? '✅' : 'ℹ️'}</span>
                <span class="notification-message">${message}</span>
            </div>
        `;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.classList.add('show');
        }, 100);
        
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => {
                if (notification.parentElement) {
                    notification.remove();
                }
            }, 300);
        }, type === 'error' ? 7000 : 3000);
    }
}

// Global functions
function simulateForecast() {
    if (window.dashboard) {
        window.dashboard.simulateForecast();
    }
}

function downloadData() {
    if (window.dashboard) {
        window.dashboard.downloadData();
    }
}

function showModelComparison() {
    if (window.dashboard) {
        window.dashboard.showModelComparison();
    }
}

// Initialize dashboard
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 DOM loaded, initializing dashboard...');
    window.dashboard = new IPHDashboard();
});