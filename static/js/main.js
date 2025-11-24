let allServices = {};
let currentFilter = 'all';

document.addEventListener('DOMContentLoaded', () => {
    initNavigation();
    loadServices();
    initFilterButtons();
});

function initNavigation() {
    const navLinks = document.querySelectorAll('.nav-link');
    
    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const section = link.getAttribute('data-section');
            scrollToSection(section);
            
            navLinks.forEach(l => l.classList.remove('active'));
            link.classList.add('active');
        });
    });

    window.addEventListener('scroll', () => {
        const sections = document.querySelectorAll('.section');
        let current = '';
        
        sections.forEach(section => {
            const sectionTop = section.offsetTop - 100;
            if (window.scrollY >= sectionTop) {
                current = section.getAttribute('id');
            }
        });
        
        navLinks.forEach(link => {
            link.classList.remove('active');
            if (link.getAttribute('data-section') === current) {
                link.classList.add('active');
            }
        });
    });
}

function scrollToSection(sectionId) {
    const section = document.getElementById(sectionId);
    if (section) {
        const offset = 80;
        const sectionTop = section.offsetTop - offset;
        window.scrollTo({ top: sectionTop, behavior: 'smooth' });
    }
}

async function loadServices() {
    const container = document.getElementById('servicesContainer');
    
    try {
        const response = await fetch('/api/services');
        const data = await response.json();
        
        allServices = data.categories;
        document.getElementById('countAll').textContent = data.total_services;
        
        displayServices();
    } catch (error) {
        console.error('Erro ao carregar serviços:', error);
        container.innerHTML = `
            <div class="loading-state">
                <p>Erro ao carregar serviços. Tente novamente.</p>
            </div>
        `;
    }
}

function initFilterButtons() {
    const filterBtns = document.querySelectorAll('.filter-btn');
    
    filterBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const category = btn.getAttribute('data-category');
            currentFilter = category;
            
            filterBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            displayServices();
        });
    });
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
        container.innerHTML = `
            <div class="loading-state">
                <p>Nenhum serviço encontrado nesta categoria.</p>
            </div>
        `;
        return;
    }

    servicesToShow.slice(0, 50).forEach((service, index) => {
        const card = document.createElement('div');
        card.className = 'service-card';
        card.style.animationDelay = `${index * 0.02}s`;
        card.innerHTML = `
            <div class="service-name">${service.info.name}</div>
            <div class="service-category">${service.info.category}</div>
        `;
        container.appendChild(card);
    });

    if (servicesToShow.length > 50) {
        const moreCard = document.createElement('div');
        moreCard.className = 'service-card';
        moreCard.innerHTML = `
            <div class="service-name">+${servicesToShow.length - 50} mais</div>
            <div class="service-category">Serviços adicionais</div>
        `;
        container.appendChild(moreCard);
    }
}

async function runDemoAnalysis() {
    const resultsContainer = document.getElementById('analysisResults');
    const btn = document.getElementById('btnAnalyze');
    
    btn.classList.add('loading');
    btn.innerHTML = `
        <div class="loading-spinner" style="width: 18px; height: 18px; border-width: 2px;"></div>
        <span>Analisando...</span>
    `;
    
    resultsContainer.innerHTML = `
        <div class="analysis-placeholder">
            <div class="loading-spinner"></div>
            <p>Executando análise com IA...</p>
        </div>
    `;
    
    try {
        const response = await fetch('/api/demo-analysis');
        const data = await response.json();
        
        resultsContainer.innerHTML = `
            <div class="results-summary">
                <div class="summary-card">
                    <div class="summary-value green">$${data.summary.total_monthly_savings_usd.toLocaleString('en-US', {minimumFractionDigits: 2})}</div>
                    <div class="summary-label">Economia Mensal</div>
                </div>
                <div class="summary-card">
                    <div class="summary-value blue">$${data.summary.total_annual_savings_usd.toLocaleString('en-US', {minimumFractionDigits: 2})}</div>
                    <div class="summary-label">Economia Anual</div>
                </div>
                <div class="summary-card">
                    <div class="summary-value">${data.resources_analyzed}</div>
                    <div class="summary-label">Recursos Analisados</div>
                </div>
                <div class="summary-card">
                    <div class="summary-value purple">${data.summary.high_priority_actions}</div>
                    <div class="summary-label">Ações Prioritárias</div>
                </div>
            </div>
            
            <h4 style="margin-bottom: 1rem; color: var(--text-primary);">Top Recomendações</h4>
            <div class="recommendations-list">
                ${data.top_recommendations.map(rec => `
                    <div class="recommendation-card ${rec.priority}">
                        <div class="rec-header">
                            <span class="rec-type">${rec.resource_type}: ${rec.resource_id}</span>
                            <span class="rec-priority ${rec.priority}">${rec.priority}</span>
                        </div>
                        <p class="rec-details">
                            <strong>Atual:</strong> ${rec.current_config}<br>
                            <strong>Recomendação:</strong> ${rec.recommendation.details}<br>
                            <strong>Motivo:</strong> ${rec.recommendation.reasoning}
                        </p>
                        <span class="rec-savings">
                            Economia: $${rec.savings.monthly_usd.toFixed(2)}/mês (${rec.savings.percentage}%)
                        </span>
                    </div>
                `).join('')}
            </div>
        `;
        
    } catch (error) {
        console.error('Erro ao gerar análise:', error);
        resultsContainer.innerHTML = `
            <div class="analysis-placeholder">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                    <circle cx="12" cy="12" r="10"/>
                    <path d="M15 9l-6 6M9 9l6 6"/>
                </svg>
                <p>Erro ao gerar análise. Tente novamente.</p>
            </div>
        `;
    }
    
    btn.classList.remove('loading');
    btn.innerHTML = `
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polygon points="5,3 19,12 5,21"/>
        </svg>
        <span>Executar Análise</span>
    `;
}
