let allServices = {};
let currentFilter = 'all';

document.addEventListener('DOMContentLoaded', () => {
    initNavigation();
    initMobileMenu();
    loadServices();
    initFilterButtons();
    initKeyboardNavigation();
});

function initNavigation() {
    const navLinks = document.querySelectorAll('.nav-link');
    const mobileLinks = document.querySelectorAll('.mobile-link');
    
    [...navLinks, ...mobileLinks].forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const section = link.getAttribute('data-section');
            scrollToSection(section);
            
            navLinks.forEach(l => l.classList.remove('active'));
            const activeLink = document.querySelector(`.nav-link[data-section="${section}"]`);
            if (activeLink) activeLink.classList.add('active');
            
            closeMobileMenu();
        });
    });

    let scrollTimeout;
    window.addEventListener('scroll', () => {
        if (scrollTimeout) clearTimeout(scrollTimeout);
        scrollTimeout = setTimeout(() => {
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
        }, 50);
    });
}

function initMobileMenu() {
    const mobileMenuBtn = document.querySelector('.mobile-menu-btn');
    const mobileMenu = document.getElementById('mobile-menu');
    
    if (!mobileMenuBtn || !mobileMenu) return;
    
    mobileMenuBtn.addEventListener('click', () => {
        const isExpanded = mobileMenuBtn.getAttribute('aria-expanded') === 'true';
        mobileMenuBtn.setAttribute('aria-expanded', !isExpanded);
        mobileMenu.classList.toggle('open');
        
        if (!isExpanded) {
            const firstLink = mobileMenu.querySelector('.mobile-link');
            if (firstLink) firstLink.focus();
        }
    });
    
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && mobileMenu.classList.contains('open')) {
            closeMobileMenu();
            mobileMenuBtn.focus();
        }
    });
    
    document.addEventListener('click', (e) => {
        if (!mobileMenuBtn.contains(e.target) && !mobileMenu.contains(e.target)) {
            closeMobileMenu();
        }
    });
}

function closeMobileMenu() {
    const mobileMenuBtn = document.querySelector('.mobile-menu-btn');
    const mobileMenu = document.getElementById('mobile-menu');
    
    if (mobileMenuBtn) mobileMenuBtn.setAttribute('aria-expanded', 'false');
    if (mobileMenu) mobileMenu.classList.remove('open');
}

function initKeyboardNavigation() {
    const filterBtns = document.querySelectorAll('.filter-btn');
    
    filterBtns.forEach((btn, index) => {
        btn.addEventListener('keydown', (e) => {
            let nextIndex;
            
            if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {
                e.preventDefault();
                nextIndex = (index + 1) % filterBtns.length;
            } else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
                e.preventDefault();
                nextIndex = (index - 1 + filterBtns.length) % filterBtns.length;
            } else if (e.key === 'Home') {
                e.preventDefault();
                nextIndex = 0;
            } else if (e.key === 'End') {
                e.preventDefault();
                nextIndex = filterBtns.length - 1;
            }
            
            if (nextIndex !== undefined) {
                filterBtns[nextIndex].focus();
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
        
        section.setAttribute('tabindex', '-1');
        section.focus({ preventScroll: true });
    }
}

async function loadServices() {
    const container = document.getElementById('services-panel');
    if (!container) return;
    
    try {
        const response = await fetch('/api/services');
        const data = await response.json();
        
        allServices = data.categories;
        const countEl = document.getElementById('countAll');
        if (countEl) countEl.textContent = data.total_services;
        
        displayServices();
    } catch (error) {
        console.error('Erro ao carregar serviços:', error);
        container.innerHTML = `
            <div class="loading-state" role="alert">
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
            
            filterBtns.forEach(b => {
                b.classList.remove('active');
                b.setAttribute('aria-selected', 'false');
            });
            btn.classList.add('active');
            btn.setAttribute('aria-selected', 'true');
            
            const panel = document.getElementById('services-panel');
            if (panel) {
                panel.setAttribute('aria-labelledby', btn.id);
            }
            
            displayServices();
            
            announceToScreenReader(`Mostrando serviços da categoria ${category === 'all' ? 'todos' : category}`);
        });
    });
}

function displayServices() {
    const container = document.getElementById('services-panel');
    if (!container) return;
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
            <div class="loading-state" role="status">
                <p>Nenhum serviço encontrado nesta categoria.</p>
            </div>
        `;
        return;
    }

    const servicesWrapper = document.createElement('div');
    servicesWrapper.className = 'services-grid';
    servicesWrapper.setAttribute('role', 'list');
    
    servicesToShow.slice(0, 50).forEach((service, index) => {
        const card = document.createElement('article');
        card.className = 'service-card';
        card.setAttribute('role', 'listitem');
        card.setAttribute('tabindex', '0');
        card.style.animationDelay = `${index * 0.02}s`;
        card.innerHTML = `
            <div class="service-name">${escapeHtml(service.info.name)}</div>
            <div class="service-category">${escapeHtml(service.info.category)}</div>
        `;
        servicesWrapper.appendChild(card);
    });

    if (servicesToShow.length > 50) {
        const moreCard = document.createElement('article');
        moreCard.className = 'service-card';
        moreCard.setAttribute('role', 'listitem');
        moreCard.innerHTML = `
            <div class="service-name">+${servicesToShow.length - 50} mais</div>
            <div class="service-category">Serviços adicionais</div>
        `;
        servicesWrapper.appendChild(moreCard);
    }
    
    container.appendChild(servicesWrapper);
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function announceToScreenReader(message) {
    const announcement = document.createElement('div');
    announcement.setAttribute('role', 'status');
    announcement.setAttribute('aria-live', 'polite');
    announcement.setAttribute('aria-atomic', 'true');
    announcement.className = 'sr-only';
    announcement.style.cssText = 'position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0;';
    announcement.textContent = message;
    
    document.body.appendChild(announcement);
    
    setTimeout(() => {
        document.body.removeChild(announcement);
    }, 1000);
}

async function runDemoAnalysis() {
    const resultsContainer = document.getElementById('analysisResults');
    const btn = document.getElementById('btnAnalyze');
    
    btn.classList.add('loading');
    btn.setAttribute('aria-busy', 'true');
    btn.innerHTML = `
        <div class="loading-spinner" style="width: 18px; height: 18px; border-width: 2px;" aria-hidden="true"></div>
        <span>Analisando...</span>
    `;
    
    resultsContainer.innerHTML = `
        <div class="analysis-placeholder" role="status" aria-live="polite">
            <div class="loading-spinner" aria-hidden="true"></div>
            <p>Executando análise com IA...</p>
        </div>
    `;
    
    announceToScreenReader('Iniciando análise de custos AWS');
    
    try {
        const response = await fetch('/api/demo-analysis');
        const data = await response.json();
        
        resultsContainer.innerHTML = `
            <div class="results-summary" role="list" aria-label="Resumo da análise">
                <div class="summary-card" role="listitem">
                    <div class="summary-value green" aria-label="Economia mensal">$${data.summary.total_monthly_savings_usd.toLocaleString('en-US', {minimumFractionDigits: 2})}</div>
                    <div class="summary-label">Economia Mensal</div>
                </div>
                <div class="summary-card" role="listitem">
                    <div class="summary-value blue" aria-label="Economia anual">$${data.summary.total_annual_savings_usd.toLocaleString('en-US', {minimumFractionDigits: 2})}</div>
                    <div class="summary-label">Economia Anual</div>
                </div>
                <div class="summary-card" role="listitem">
                    <div class="summary-value" aria-label="Recursos analisados">${data.resources_analyzed}</div>
                    <div class="summary-label">Recursos Analisados</div>
                </div>
                <div class="summary-card" role="listitem">
                    <div class="summary-value purple" aria-label="Ações prioritárias">${data.summary.high_priority_actions}</div>
                    <div class="summary-label">Ações Prioritárias</div>
                </div>
            </div>
            
            <h4 id="recommendations-heading" style="margin-bottom: 1rem; color: var(--text-primary);">Top Recomendações</h4>
            <div class="recommendations-list" role="list" aria-labelledby="recommendations-heading">
                ${data.top_recommendations.map(rec => `
                    <article class="recommendation-card ${rec.priority}" role="listitem">
                        <div class="rec-header">
                            <span class="rec-type">${escapeHtml(rec.resource_type)}: ${escapeHtml(rec.resource_id)}</span>
                            <span class="rec-priority ${rec.priority}" aria-label="Prioridade ${rec.priority}">${rec.priority}</span>
                        </div>
                        <p class="rec-details">
                            <strong>Atual:</strong> ${escapeHtml(rec.current_config)}<br>
                            <strong>Recomendação:</strong> ${escapeHtml(rec.recommendation.details)}<br>
                            <strong>Motivo:</strong> ${escapeHtml(rec.recommendation.reasoning)}
                        </p>
                        <span class="rec-savings" aria-label="Economia de ${rec.savings.percentage} por cento">
                            Economia: $${rec.savings.monthly_usd.toFixed(2)}/mês (${rec.savings.percentage}%)
                        </span>
                    </article>
                `).join('')}
            </div>
        `;
        
        announceToScreenReader(`Análise concluída. Economia mensal potencial de ${data.summary.total_monthly_savings_usd.toFixed(2)} dólares.`);
        
    } catch (error) {
        console.error('Erro ao gerar análise:', error);
        resultsContainer.innerHTML = `
            <div class="analysis-placeholder" role="alert">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true">
                    <circle cx="12" cy="12" r="10"/>
                    <path d="M15 9l-6 6M9 9l6 6"/>
                </svg>
                <p>Erro ao gerar análise. Tente novamente.</p>
            </div>
        `;
        
        announceToScreenReader('Erro ao gerar análise. Tente novamente.');
    }
    
    btn.classList.remove('loading');
    btn.setAttribute('aria-busy', 'false');
    btn.innerHTML = `
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
            <polygon points="5,3 19,12 5,21"/>
        </svg>
        <span>Executar Análise</span>
    `;
}
