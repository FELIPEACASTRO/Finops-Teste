# 🚀 Replit Project Brief: Build the Finops-Teste Platform

**Project**: Finops-Teste
**Objective**: Create a full-stack, enterprise-grade FinOps platform using Replit's cloud IDE and AI capabilities.

---

## 1. Your Role: AI-Powered Developer

Your task is to leverage Replit's AI and cloud environment to build the **Finops-Teste** application. You will be responsible for setting up the environment, writing the code (backend and frontend), configuring the database, and ensuring the project is fully functional within the Replit ecosystem.

---

## 2. Core Project Goals



O projeto Finops-Teste deve alcançar os seguintes objetivos estratégicos:

1. **Qualidade de Código Nota 10**: Implementar um sistema que seja referência em qualidade, seguindo todos os princípios SOLID, Clean Code e Clean Architecture.

2. **Alta Performance**: O sistema deve suportar alta carga (2000 TPS - Transações Por Segundo) com latências baixas (P95 < 200ms para leituras, P95 < 500ms para escritas).

3. **Resiliência e Disponibilidade**: Garantir SLA de 99.9% de disponibilidade com estratégias de *retry*, *circuit breaker* e *fallback*.

4. **Observabilidade Completa**: Implementar logs estruturados, métricas de negócio e técnicas, e rastreamento distribuído (distributed tracing).

5. **Otimização de Custos (FinOps)**: Incorporar desde o início práticas de FinOps, com monitoramento de custos, dashboards de otimização e automações para redução de gastos.

6. **Escalabilidade**: Suportar crescimento horizontal e vertical, com arquitetura preparada para evolução de monólito modular para microserviços.



---

## 3. Replit Environment & Setup

1.  **Workspace Setup**: Create a new Replit workspace using the **"React + Node.js"** template.
2.  **Database**: Use **Replit's built-in PostgreSQL database**. Configure it and create the necessary tables.
3.  **Secrets**: Use Replit's `Secrets` manager for all environment variables (database credentials, API keys, etc.). **Do not hardcode secrets**.
4.  **Deployment**: The project must be deployable using Replit's built-in deployment features.

---

## 4. Technology Stack (Replit-focused)



A escolha da stack será pragmática, evoluindo conforme as necessidades do projeto.

### Fase 1: MVP Funcional

**Backend**:
- Linguagem: Go (para alta performance) ou Node.js/TypeScript (para produtividade)
- Framework: Fiber (Go) ou NestJS (Node.js)

**Database**:
- PostgreSQL (transacional, com JSONB para flexibilidade)

**Cache**:
- In-memory (node-cache) ou Redis básico

**API**:
- REST puro com OpenAPI/Swagger

**Auth**:
- JWT simples

**Deploy**:
- Docker + docker-compose

**CI/CD**:
- GitHub Actions ou GitLab CI

### Fase 2: Production-Ready

**Cache**:
- Redis (sessões, queries, rate limiting)

**Queue**:
- BullMQ (Node.js) ou RabbitMQ

**Events**:
- Event-driven interno (EventEmitter2)

**Search**:
- PostgreSQL Full-Text Search ou Elasticsearch

**API**:
- REST + GraphQL para queries complexas

**Monitoring**:
- Prometheus + Grafana + Sentry

**Deploy**:
- Kubernetes (managed: GKE/EKS/AKS)

### Fase 3: Enterprise-Grade

**Message Broker**:
- Apache Kafka (eventos de domínio)

**Service Mesh**:
- Istio (traffic management, security)

**Database**:
- PostgreSQL (primary) + Read Replicas
- MongoDB (analytics, logs históricos)

**CDN**:
- CloudFlare ou CloudFront

**Secrets**:
- HashiCorp Vault ou Cloud KMS

**APM**:
- Datadog ou New Relic

**Security**:
- SAST (SonarQube), DAST (OWASP ZAP), Container scanning



**Key Adaptations for Replit**:

-   **Backend**: Use the Node.js/TypeScript + NestJS stack, as it integrates seamlessly with Replit's environment.
-   **Database**: Use Replit's PostgreSQL. Your code should connect to it using the environment variables provided by Replit.
-   **CI/CD**: Replit's deployment process will serve as the CI/CD pipeline. Ensure your `replit.nix` and `package.json` scripts are correctly configured for building and running the application.

---

## 5. Phased Development Plan

Follow this phased plan. Use Replit's AI to help you generate code, debug issues, and write tests.



O projeto será desenvolvido em fases, garantindo entregas de valor incrementais e validação contínua.

### 🎯 Fase 1: MVP Funcional (Fundação Sólida)

**Duração**: 2-3 semanas

**Objetivos**:
- Sistema funcional end-to-end
- Código limpo e testável
- Base sólida para evolução

**Funcionalidades Core**:
- CRUD completo de recursos de custo
- Autenticação e autorização básica
- Coleta de métricas de utilização
- Cálculo básico de custos
- Dashboard simples

**Arquitetura**:
- Modular Monolith com Bounded Contexts claros
- Clean Architecture em camadas
- Repositórios como abstrações

**Testes**:
- Unit Tests: Domain models e business logic (>70%)
- Integration Tests: APIs principais
- E2E: 3-5 fluxos críticos

**Definition of Done**:
- [ ] Aplicação roda com `docker-compose up`
- [ ] Seed data disponível para testes
- [ ] Todos os testes passando
- [ ] README com quick start
- [ ] API documentada (Swagger/OpenAPI)
- [ ] Health check endpoint funcionando

### 🚀 Fase 2: Production-Ready (Escalabilidade e Observabilidade)

**Duração**: 4-6 semanas

**Objetivos**:
- Alta disponibilidade
- Performance otimizada
- Observabilidade completa

**Melhorias Arquiteturais**:
- CQRS para leitura/escrita separadas
- Event-Driven para comunicação entre módulos
- Cache Strategy com Redis
- Rate Limiting e Circuit Breaker

**Funcionalidades Adicionais**:
- Análise avançada de utilização de recursos
- Recomendações de otimização (rightsizing)
- Notificações assíncronas
- Webhooks para integrações
- Logs estruturados (JSON)
- Distributed tracing (OpenTelemetry)

**Observabilidade**:
- Logs: ELK Stack ou Loki
- Metrics: RED + USE
- Traces: Jaeger ou Zipkin
- Alerts: Prometheus Alertmanager

**Testes**:
- Unit Tests: >80% coverage
- Integration Tests: Testcontainers para DB real
- Contract Tests: Pact para APIs
- Load Tests: k6 para 1000 RPS
- Chaos Engineering: Básico (timeouts, failures)

**Definition of Done**:
- [ ] Sistema suporta 1000 usuários concorrentes
- [ ] Alertas configurados para métricas críticas
- [ ] Rollback strategy documentada e testada
- [ ] Load tests validando SLOs
- [ ] Zero-downtime deployment funcionando
- [ ] Runbooks para incidentes comuns

### 🏢 Fase 3: Enterprise-Grade (Resiliência Total e FinOps Avançado)

**Duração**: 8+ semanas

**Objetivos**:
- Multi-região (se aplicável)
- Compliance total
- Disaster recovery
- Otimização de custos avançada

**Arquitetura Avançada**:
- Microservices seletivos (se necessário)
- SAGA Pattern para transações distribuídas
- Event Sourcing para auditoria crítica
- API Gateway com rate limiting e auth

**Funcionalidades Enterprise**:
- Advanced fraud detection
- A/B testing framework
- Feature flags (LaunchDarkly/Unleash)
- Data privacy compliance (GDPR/LGPD)
- Advanced analytics e BI
- Multi-currency e i18n
- Backup e restore automatizados

**FinOps Avançado**:
- Análise preditiva de custos (Machine Learning)
- Automação de otimizações (rightsizing automático)
- Chargeback e showback
- Budget alerts e forecasting
- Integração com múltiplos cloud providers

**Segurança Hardening**:
- Zero-trust network com micro-segmentação
- mTLS entre serviços
- Certificate rotation automatizada
- Vulnerability scanning contínuo
- Penetration testing trimestral
- SOC 2 / ISO 27001 compliance readiness

**Disaster Recovery**:
- RTO (Recovery Time Objective): < 30 minutos
- RPO (Recovery Point Objective): < 5 minutos
- Strategy: Active-Passive multi-region
- Backup: Automated daily + incremental 4h
- Testing: Quarterly DR drills

**Definition of Done**:
- [ ] Failover testado e documentado
- [ ] Compliance checklist completa
- [ ] Security audit aprovado
- [ ] DR drill bem-sucedido
- [ ] Runbooks completos para todas as operações
- [ ] Treinamento de on-call realizado



**How to use Replit AI**:

-   **Code Generation**: Use the AI to generate boilerplate for components, services, and tests.
-   **Debugging**: When you encounter errors, ask the AI to explain the error and suggest a fix.
-   **Refactoring**: Use the AI to refactor complex functions and improve code quality.

---

## 6. Key Tasks & Instructions

1.  **Initialize Project**: Set up the Replit workspace and configure the PostgreSQL database.
2.  **Backend Development**: Build the NestJS backend, following the Clean Architecture principles. Create all necessary modules, services, and controllers.
3.  **Frontend Development**: Build the React frontend using Vite. Implement the dashboard, charts, and all UI components as specified.
4.  **Connect Frontend & Backend**: Ensure the React app can communicate with the NestJS API running in the same Replit workspace.
5.  **Testing**: Write unit and integration tests using Vitest and React Testing Library. Run tests using the Replit shell.
6.  **Documentation**: Create a detailed `README.md` file explaining how to set up, run, and use the project within Replit.

---

## 7. Final Goal

The project is complete when it is fully functional, deployed on Replit, and meets all the objectives outlined above. The `README.md` must provide clear instructions for anyone to clone the Repl and run the application.

For detailed implementation guidance, refer to the full knowledge base at `PROMPT_FINOPS_TESTE_FINAL_V3.md`.

