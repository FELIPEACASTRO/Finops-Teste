# 🤖 Mission Briefing for Devin: Build the Finops-Teste Platform

**Project Title**: Finops-Teste: Enterprise-Grade Cost Optimization & Cloud Management Platform

**Version**: 1.0

**Date**: November 25, 2025

---

## 1. Core Mission

Your mission is to act as an autonomous AI Software Engineer and build a complete, enterprise-grade, full-stack software solution named **Finops-Teste**. This platform will serve as a reference for excellence in software engineering, focusing on FinOps, performance, security, and code quality.

You must handle the entire development lifecycle: planning, architecture, coding (backend and frontend), testing, documentation, and deployment setup.

---

## 2. Key Strategic Objectives & Deliverables



O projeto Finops-Teste deve alcançar os seguintes objetivos estratégicos:

1. **Qualidade de Código Nota 10**: Implementar um sistema que seja referência em qualidade, seguindo todos os princípios SOLID, Clean Code e Clean Architecture.

2. **Alta Performance**: O sistema deve suportar alta carga (2000 TPS - Transações Por Segundo) com latências baixas (P95 < 200ms para leituras, P95 < 500ms para escritas).

3. **Resiliência e Disponibilidade**: Garantir SLA de 99.9% de disponibilidade com estratégias de *retry*, *circuit breaker* e *fallback*.

4. **Observabilidade Completa**: Implementar logs estruturados, métricas de negócio e técnicas, e rastreamento distribuído (distributed tracing).

5. **Otimização de Custos (FinOps)**: Incorporar desde o início práticas de FinOps, com monitoramento de custos, dashboards de otimização e automações para redução de gastos.

6. **Escalabilidade**: Suportar crescimento horizontal e vertical, com arquitetura preparada para evolução de monólito modular para microserviços.



**Final Deliverables**:

- **Source Code**: A complete, well-documented, and tested codebase hosted in a Git repository.
- **Documentation**:
  - An extremely detailed `README.md`.
  - Architecture Decision Records (ADRs) for key architectural choices.
  - OpenAPI/Swagger specification for all APIs.
  - Runbooks for operational procedures.
- **Deployment Configuration**: Dockerfiles, `docker-compose.yml`, and Kubernetes manifests.
- **CI/CD Pipeline**: A complete GitHub Actions or GitLab CI pipeline configuration.

---

## 3. Non-Negotiable Constraints & Principles

Your implementation **must** strictly adhere to these foundational principles. They are not suggestions.



Todo o desenvolvimento do projeto Finops-Teste deve aderir estritamente aos seguintes princípios:

### 1. Princípios SOLID

#### Single Responsibility Principle (SRP)
Cada classe, módulo ou função deve ter uma única responsabilidade bem definida. Evitar classes que fazem múltiplas coisas.

**Exemplo Correto**:
```typescript
class OrderCalculator {
  calculateTotal(items: OrderItem[]): Money { }
}

class OrderNotifier {
  sendConfirmation(order: Order): Promise<void> { }
}
```

**Exemplo Incorreto**:
```typescript
class Order {
  calculateTotal() { }
  sendEmail() { }
  saveToDatabase() { }
}
```

#### Open/Closed Principle (OCP)
O código deve ser aberto para extensão, mas fechado para modificação. Utilizar abstrações (interfaces) para permitir a adição de novas funcionalidades sem alterar o código existente.

**Exemplo**:
```typescript
interface PaymentGateway {
  process(amount: Money): Promise<PaymentResult>;
}

class StripeGateway implements PaymentGateway { }
class PayPalGateway implements PaymentGateway { }
```

#### Liskov Substitution Principle (LSP)
Subtipos devem ser substituíveis por seus tipos base sem quebrar a aplicação.

#### Interface Segregation Principle (ISP)
Interfaces devem ser específicas e coesas. Evitar interfaces "gordas" que forçam implementações desnecessárias.

#### Dependency Inversion Principle (DIP)
Depender de abstrações, não de implementações concretas. Utilizar injeção de dependências.

### 3. Princípios do FinOps Framework 2025 (Atualizado)

- **Business value drives technology decisions**: As decisões de tecnologia devem ser orientadas pelo valor de negócio, não apenas pelo custo.
- **Everyone takes ownership for their technology usage**: Todos assumem a responsabilidade pelo uso de tecnologia e seus custos associados.
- **FinOps data should be accessible, timely, and accurate**: Os dados de FinOps devem ser acessíveis, atualizados e precisos.
- **FinOps should be enabled centrally**: A prática de FinOps deve ser habilitada por uma equipe centralizada que dá suporte às equipes de produto.


### 4. Princípios Complementares

- **KISS (Keep It Simple, Stupid)**: Priorizar soluções simples e diretas. Evitar complexidade desnecessária e *over-engineering*.

- **DRY (Don't Repeat Yourself)**: Eliminar duplicação de código através de abstrações e reutilização.

- **YAGNI (You Aren't Gonna Need It)**: Implementar apenas o que é estritamente necessário para os requisitos atuais.

- **Clean Code**: O código deve ser legível, autoexplicativo e fácil de entender. Nomes de variáveis, funções e classes devem ser claros e expressivos.

- **Law of Demeter**: Um objeto deve ter conhecimento limitado sobre outros objetos. Evitar cadeias de chamadas longas.

- **Composição sobre Herança**: Favorecer a composição para alcançar polimorfismo e reutilização de código.

- **Programação Defensiva**: Validar entradas, tratar erros de forma proativa e falhar o mais rápido possível (Fail-Fast Principle).

- **Imutabilidade**: Utilizar estruturas de dados imutáveis sempre que possível, especialmente em contextos concorrentes.



---

## 4. Architectural Mandates

Your design must follow these architectural patterns without deviation.



A arquitetura será a espinha dorsal do projeto, garantindo sua longevidade, capacidade de evolução e facilidade de manutenção.

### 1. Padrão Arquitetural Principal

#### Clean Architecture / Arquitetura Hexagonal (Ports and Adapters)

O núcleo do sistema (domínio e casos de uso) será completamente isolado de tecnologias externas (frameworks, bancos de dados, UI). As dependências devem sempre apontar para dentro.

**Estrutura de Camadas**:
```
/cmd                    # Ponto de entrada da aplicação
/internal
  /domain               # Entidades, Value Objects, Regras de Negócio
  /usecase              # Casos de Uso (Application Services)
  /controller           # Adaptadores de entrada (HTTP, gRPC, CLI)
  /repository           # Adaptadores de saída (Database, APIs externas)
  /infra                # Infraestrutura (Config, Logging, Metrics)
  /dto                  # Data Transfer Objects
  /middleware           # Middlewares (Auth, Rate Limiting, CORS)
  /observability        # Logs, Metrics, Traces
/pkg                    # Bibliotecas reutilizáveis
/scripts                # Scripts de setup, deploy, migrations
/tests                  # Testes E2E e de integração
```

#### Modular Monolith

Iniciar com um monólito modular bem estruturado. Cada módulo representará um **Bounded Context** claro do DDD, facilitando a futura extração para microserviços, se necessário.

**Benefícios**:
- Simplicidade operacional inicial
- Facilidade de desenvolvimento e debug
- Transações ACID nativas
- Preparado para evolução

### 2. Domain-Driven Design (DDD)

#### Linguagem Ubíqua
Desenvolver um vocabulário comum entre desenvolvedores e especialistas de domínio. Todos os termos do domínio devem ser refletidos no código.

#### Bounded Contexts
Delimitar claramente os diferentes subdomínios do Finops-Teste. Cada contexto deve ter seu próprio modelo de domínio.

**Exemplos de Bounded Contexts para FinOps**:
- **Cost Management**: Gestão de custos, orçamentos e previsões
- **Resource Optimization**: Análise de utilização e recomendações
- **Billing & Invoicing**: Faturamento e alocação de custos
- **Reporting & Analytics**: Dashboards e relatórios

#### Agregados e Raízes de Agregado
Modelar o domínio em agregados consistentes para garantir a integridade das regras de negócio. Cada agregado tem uma raiz que é o ponto de entrada para modificações.

#### Entidades e Value Objects
- **Entidades**: Objetos com identidade única (ex: `User`, `Order`)
- **Value Objects**: Objetos sem identidade, definidos por seus atributos (ex: `Money`, `Email`, `Address`)

### 3. Padrões de Design e Microserviços

#### Padrões de Design Essenciais

- **Strategy**: Para algoritmos intercambiáveis (ex: diferentes estratégias de cálculo de custos)
- **Factory / Abstract Factory**: Para criação de objetos complexos
- **Observer**: Para notificações e eventos
- **Decorator**: Para adicionar comportamentos dinamicamente
- **Builder**: Para construção de objetos complexos passo a passo
- **Repository**: Para abstração de acesso a dados

#### Padrões para Escalabilidade

### 4. Práticas Modernas (2025+)

- **Platform Engineering**: Desenvolver uma Internal Developer Platform (IDP) com controles de custos e segurança embarcados para abstrair a complexidade da infraestrutura.
- **eBPF para Observabilidade**: Utilizar ferramentas baseadas em eBPF (ex: Cilium, Pixie) para observabilidade de rede e segurança de alta performance e baixo overhead.
- **WebAssembly (Wasm)**: Considerar Wasm para workloads de edge computing que exijam alta performance e segurança com baixo custo.


- **CQRS (Command Query Responsibility Segregation)**: Separar operações de leitura e escrita para otimizar cada uma independentemente.

- **Event Sourcing**: Armazenar o estado como uma sequência de eventos para auditoria completa e reconstrução de estado.

- **Event-Driven Architecture**: Comunicação assíncrona entre módulos através de eventos de domínio.

#### Padrões de Resiliência

- **Circuit Breaker**: Prevenir cascata de falhas em chamadas a serviços externos.
- **Retry com Backoff Exponencial**: Tentar novamente operações falhadas com intervalos crescentes (máximo 3 tentativas).
- **Fallback**: Fornecer respostas alternativas quando operações principais falham.
- **Timeout**: Definir limites de tempo para operações externas.

#### Idempotência

Todas as operações de escrita (comandos) devem ser idempotentes para evitar efeitos colaterais em caso de repetições. Utilizar IDs de idempotência em requisições críticas.



---

## 5. Frontend Requirements (React)

The frontend must be a modern, performant, and accessible React application. Key requirements include:

- **React 19**: Utilize the latest features like the React Compiler, Actions, `useOptimistic`, and Server Components where appropriate.
- **Performance**: Adhere to Core Web Vitals (LCP < 2.5s, INP < 200ms, CLS < 0.1).
- **UX/UI**: Follow Nielsen's Heuristics and best practices for dashboard design.
- **Acessibilidade**: Ensure WCAG 2.2 Level AA compliance.
- **Testing**: Implement a robust testing strategy (Unit, Integration, E2E).
- **Security**: Prevent common frontend vulnerabilities (XSS, CSRF).

---

## 6. Technology Stack

You must use the following progressive technology stack. Do not introduce other technologies without explicit justification recorded in an ADR.



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



---

## 7. Quality Gates & Service Level Objectives (SLOs)

Your implementation must meet or exceed these quantitative targets.



O sistema deve ser projetado para alta performance e capacidade de escalar horizontalmente.

### 1. Service Level Objectives (SLOs)

#### Performance
- **P50 (Mediana)**: < 50ms
- **P95**: < 150ms para leituras, < 500ms para escritas
- **P99**: < 300ms para leituras, < 1000ms para escritas
- **Throughput**: 2000 TPS (Transações Por Segundo)

#### Confiabilidade
- **Availability**: 99.9% uptime (≈8.7h downtime/ano)
- **Error Rate**: < 1% para operações críticas

#### Escalabilidade
- **Conexões Simultâneas**: 10.000 usuários concorrentes
- **Utilização de CPU**: < 60% em operação normal
- **Utilização de Memória**: < 70% em operação normal

### 2. Estratégias de Otimização

#### Caching Multi-Layer

- **L1 (In-Memory)**: Cache local na aplicação (node-cache)
- **L2 (Redis)**: Cache distribuído para sessões e queries frequentes
- **L3 (CDN)**: Cache de conteúdo estático

**Estratégias**:
- **Cache-Aside**: Aplicação gerencia o cache
- **Write-Through**: Escrita síncrona no cache e DB
- **TTL Inteligente**: Tempo de vida baseado em padrões de acesso

#### Database Optimization

- **Índices Inteligentes**: Criar índices para queries frequentes
- **Query Optimization**: Analisar e otimizar queries lentas
- **Connection Pooling**: Gerenciar pool de conexões eficientemente
- **Read Replicas**: Distribuir leituras em réplicas
- **Partitioning/Sharding**: Para grandes volumes de dados

#### Processamento Assíncrono

- **Message Queues**: Processar operações não críticas de forma assíncrona (RabbitMQ, SQS, Kafka)
- **Background Jobs**: Workers dedicados para tarefas pesadas
- **Event-Driven**: Comunicação assíncrona entre módulos

### 3. Horizontal Scaling

- **Stateless Services**: Serviços sem estado para facilitar escalabilidade
- **Load Balancing**: Distribuir carga entre instâncias
- **Auto-Scaling**: Escalar automaticamente baseado em métricas (CPU, memória, requests)



---

## 8. Phased Implementation Plan

Follow this phased plan to structure your work. Treat each phase as a major milestone. Report your progress upon completion of each phase.



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



---

## 9. Final Acceptance Criteria

Before concluding the mission, verify that all of the following criteria are met:

- [ ] The application is fully functional and meets all objectives.
- [ ] The entire codebase is pushed to a Git repository.
- [ ] All specified documentation (`README.md`, ADRs, API specs) is complete and accurate.
- [ ] The application can be started locally with a single command (e.g., `docker-compose up`).
- [ ] All tests (unit, integration, E2E) are passing in the CI/CD pipeline.
- [ ] Performance and reliability SLOs are met under load tests.
- [ ] Code coverage is above 80%.
- [ ] All security and accessibility checks are passing.

---

## 10. Reference Knowledge Base

For detailed implementation guidance, code snippets, and deeper explanations of any concept mentioned in this briefing, consult the comprehensive knowledge base located at `PROMPT_FINOPS_TESTE_FINAL_V3.md`.

**Your task begins now. Plan your work, then execute.**

