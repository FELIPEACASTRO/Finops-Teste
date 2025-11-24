let allServices = {};
let currentFilter = 'all';

async function loadStats() {
    try {
        const response = await fetch('/api/stats');
        const data = await response.json();
        
        const statsGrid = document.getElementById('statsGrid');
        statsGrid.innerHTML = `
            <div class="stat-item">
                <div class="stat-value">${data.version}</div>
                <div class="stat-label">Versão</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">${data.total_services}+</div>
                <div class="stat-label">Serviços AWS</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">${data.categories}</div>
                <div class="stat-label">Categorias</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">${data.tests_passing}</div>
                <div class="stat-label">Testes Passando</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">${data.code_coverage}</div>
                <div class="stat-label">Cobertura</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">✅</div>
                <div class="stat-label">${data.status}</div>
            </div>
        `;
    } catch (error) {
        console.error('Erro ao carregar estatísticas:', error);
    }
}

async function loadServices() {
    try {
        const response = await fetch('/api/services');
        const data = await response.json();
        
        allServices = data.categories;
        
        document.getElementById('totalServices').textContent = data.total_services;
        document.getElementById('totalCategories').textContent = data.total_categories;
        
        displayServices();
    } catch (error) {
        console.error('Erro ao carregar serviços:', error);
        document.getElementById('servicesContainer').innerHTML = '<p>Erro ao carregar serviços.</p>';
    }
}

function displayServices() {
    const container = document.getElementById('servicesContainer');
    container.innerHTML = '';
    
    let servicesToShow = [];
    
    if (currentFilter === 'all') {
        Object.values(allServices).forEach(services => {
            servicesToShow = servicesToShow.concat(services);
        });
    } else {
        servicesToShow = allServices[currentFilter] || [];
    }
    
    if (servicesToShow.length === 0) {
        container.innerHTML = '<p>Nenhum serviço encontrado.</p>';
        return;
    }
    
    servicesToShow.forEach(service => {
        const card = document.createElement('div');
        card.className = 'service-card';
        card.innerHTML = `
            <div class="service-name">${service.info.name}</div>
            <div class="service-type">${service.type}</div>
            <div class="service-category">${service.info.category.value || service.info.category}</div>
        `;
        container.appendChild(card);
    });
}

function showAllServices() {
    currentFilter = 'all';
    updateActiveTab(0);
    displayServices();
}

function filterByCategory(category) {
    currentFilter = category;
    updateActiveTab(-1);
    displayServices();
}

function updateActiveTab(index) {
    const tabs = document.querySelectorAll('.tab-btn');
    tabs.forEach((tab, i) => {
        if (index === -1) {
            tab.classList.remove('active');
            if (tab.textContent.trim() === currentFilter) {
                tab.classList.add('active');
            }
        } else if (i === index) {
            tab.classList.add('active');
        } else {
            tab.classList.remove('active');
        }
    });
}

async function loadDemoAnalysis() {
    const resultsContainer = document.getElementById('demoResults');
    resultsContainer.innerHTML = '<p>⏳ Gerando análise...</p>';
    
    try {
        const response = await fetch('/api/demo-analysis');
        const data = await response.json();
        
        resultsContainer.innerHTML = `
            <div class="analysis-summary">
                <h3>📊 Resumo da Análise</h3>
                <p><strong>Período:</strong> ${data.analysis_period_days} dias</p>
                <p><strong>Recursos Analisados:</strong> ${data.resources_analyzed}</p>
                <p><strong>Regiões:</strong> ${data.regions.join(', ')}</p>
                
                <div class="summary-stats">
                    <div class="summary-stat">
                        <div class="summary-stat-value">$${data.summary.total_monthly_savings_usd.toFixed(2)}</div>
                        <div class="summary-stat-label">Economia Mensal</div>
                    </div>
                    <div class="summary-stat">
                        <div class="summary-stat-value">$${data.summary.total_annual_savings_usd.toFixed(2)}</div>
                        <div class="summary-stat-label">Economia Anual</div>
                    </div>
                    <div class="summary-stat">
                        <div class="summary-stat-value">${data.summary.high_priority_actions}</div>
                        <div class="summary-stat-label">Ações Prioritárias</div>
                    </div>
                </div>
            </div>
            
            <h3>🎯 Top Recomendações</h3>
            <div class="recommendations">
                ${data.top_recommendations.map(rec => `
                    <div class="recommendation-card">
                        <div class="rec-header">
                            <div class="rec-resource">
                                ${rec.resource_type}: ${rec.resource_id}
                            </div>
                            <div class="rec-priority ${rec.priority}">${rec.priority}</div>
                        </div>
                        <p><strong>Região:</strong> ${rec.region}</p>
                        <p><strong>Configuração Atual:</strong> ${rec.current_config}</p>
                        <p><strong>Recomendação:</strong> ${rec.recommendation.details}</p>
                        <p><strong>Justificativa:</strong> ${rec.recommendation.reasoning}</p>
                        <div class="rec-savings">
                            <div class="savings-amount">
                                💰 $${rec.savings.monthly_usd.toFixed(2)}/mês
                            </div>
                            <div>
                                ($${rec.savings.annual_usd.toFixed(2)}/ano - ${rec.savings.percentage}% de economia)
                            </div>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    } catch (error) {
        console.error('Erro ao carregar análise demo:', error);
        resultsContainer.innerHTML = '<p>❌ Erro ao gerar análise.</p>';
    }
}

document.addEventListener('DOMContentLoaded', () => {
    loadStats();
    loadServices();
});
