# 🏆 Prompt Mestre para Desenvolvimento do Projeto Finops-Teste

## 📌 Visão Geral e Objetivo Estratégico

Este documento consolida **todas as boas práticas de engenharia de software, arquitetura, qualidade, segurança, performance e observabilidade** extraídas de quatro fontes especializadas, formando um **guia definitivo e extremamente detalhado** para o desenvolvimento do projeto **Finops-Teste**.

O projeto **Finops-Teste** deve ser construído como uma solução de software de **nível enterprise**, seguindo as mais rigorosas práticas de engenharia. O sistema deve ser **escalável, resiliente, seguro, observável, de fácil manutenção e otimizado para custos (FinOps)**. O resultado final deve ser um código de **qualidade exemplar (Nota 10)**, servindo como referência para futuros projetos.

---

## 🎯 Objetivos Finais do Projeto

O projeto Finops-Teste deve alcançar os seguintes objetivos estratégicos:

1. **Qualidade de Código Nota 10**: Implementar um sistema que seja referência em qualidade, seguindo todos os princípios SOLID, Clean Code e Clean Architecture.

2. **Alta Performance**: O sistema deve suportar alta carga (2000 TPS - Transações Por Segundo) com latências baixas (P95 < 200ms para leituras, P95 < 500ms para escritas).

3. **Resiliência e Disponibilidade**: Garantir SLA de 99.9% de disponibilidade com estratégias de *retry*, *circuit breaker* e *fallback*.

4. **Observabilidade Completa**: Implementar logs estruturados, métricas de negócio e técnicas, e rastreamento distribuído (distributed tracing).

5. **Otimização de Custos (FinOps)**: Incorporar desde o início práticas de FinOps, com monitoramento de custos, dashboards de otimização e automações para redução de gastos.

6. **Escalabilidade**: Suportar crescimento horizontal e vertical, com arquitetura preparada para evolução de monólito modular para microserviços.

---

## 📐 Princípios Fundamentais (Não Negociáveis)

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

## 🚀 FinOps em Ação: Práticas Avançadas (2025+)

Esta seção incorpora as práticas mais modernas de FinOps, alinhadas com o FinOps Framework 2025 e as tendências de mercado.

### 1. FinOps Scopes & Cloud+

- **Definição de Scopes**: O projeto deve identificar e gerenciar múltiplos **Scopes** (segmentos de gastos tecnológicos), incluindo:
  - **Public Cloud**: AWS, Azure, GCP
  - **SaaS**: Custos de licenciamento de ferramentas (ex: Datadog, Slack, Jira)
  - **AI/ML**: Custos de treinamento e inferência de modelos
  - **Data Center/On-premises**: Custos de infraestrutura própria
  - **Licensing**: Custos de software e licenciamento
- **Gestão Cloud+**: A estratégia de FinOps deve ser holística, cobrindo todos os custos tecnológicos, não apenas nuvem pública.

### 2. FinOps no Ciclo de Vida de Desenvolvimento (SDLC)

- **Design**: Estimar custos de novas features e arquiteturas. Aprovação de design baseada em análise de custo-benefício.
- **Desenvolvimento**: Fornecer aos desenvolvedores ferramentas para visualizar o custo de seu código em tempo real (ex: Infracost).
- **CI/CD**: Integrar checagens de custo no pipeline. Falhar builds que excedam orçamentos ou usem recursos não aprovados.
- **Operação**: Monitoramento contínuo, alertas de anomalias e otimização em tempo real.
- **Decomissionamento**: Processos automatizados para desativar recursos e evitar "zombie assets".

### 3. Governança de Custos e Accountability

- **Showback/Chargeback**: Implementar dashboards que atribuam custos a cada squad, produto ou feature.
- **Tagging Strategy**: Política de tagging obrigatória (ex: `Owner`, `CostCenter`, `Project`). Automatizar a validação de tags.
- **Workflows de Aprovação**: Implementar processos de aprovação para provisionamento de recursos acima de um determinado custo.

### 4. Otimização Inteligente com IA/ML

- **Detecção de Anomalias**: Usar modelos de ML para detectar picos de custos inesperados.
- **Forecasting Avançado**: Utilizar modelos preditivos para prever gastos com alta precisão.
- **Recomendações de Rightsizing**: IA para analisar padrões de uso e recomendar automaticamente o downsizing de recursos.

### 5. Estratégias de Otimização Contínua

- **Automated Rightsizing & Scaling**: Automação para ajustar capacidade de recursos com base em métricas de negócio e custo.
- **Gestão de Desperdício (Waste Detection)**: Dashboards e automações para identificar e eliminar recursos ociosos (unattached EBS, idle RDS, etc.).
- **Commitment-Based Discounts**: Automação para analisar e recomendar a compra de Reserved Instances e Savings Plans. Estratégia para uso de Spot Instances em workloads tolerantes a falhas.

### 6. FinOps as Code

- **Policy as Code**: Usar ferramentas como Open Policy Agent (OPA) ou Kyverno para definir e aplicar políticas de custo como código.
- **Cost Optimization as Code**: Versionar scripts e automações de otimização em Git, integrados ao GitOps.

### 7. Rituais e Cultura FinOps

- **Educação Contínua**: Programa de treinamento obrigatório, workshops e gamificação.
- **Ciclo de Feedback**: Rituais mensais de revisão de custos com todos os stakeholders (Dev, Finanças, Negócios).
- **Benchmarking**: Comparar KPIs de eficiência de custos com médias de mercado e entre equipes.


---

## 🏗️ Arquitetura e Design de Software

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

## 6. 🌐 Frontend: React, UX/UI e Navegabilidade (2025)

Esta seção detalha as melhores práticas para o desenvolvimento do frontend em React, focando em performance, experiência do usuário (UX), design de interface (UI), acessibilidade e navegabilidade.

---
### 6.1. React 19: Novas Features e Best Practices {#react-19}

### 1.1 React Compiler (Automação de Performance)

O **React Compiler** é a maior mudança do React 19, automatizando memoização de componentes e hooks.

**Antes (React 18)**:
```javascript
import { useCallback, useMemo, useState } from "react";

function OldComponent({ data, items }) {
  const [text, setText] = useState("");
  
  // Memoização manual necessária
  const handleClick = useCallback(() => {
    console.log("Clicked:", data);
  }, [data]);
  
  const filteredItems = useMemo(() => {
    return items.filter(item => item.active);
  }, [items]);
  
  return <div>{/* ... */}</div>;
}
```

**Agora (React 19 com Compiler)**:
```javascript
import { useState } from "react";

function NewComponent({ data, items }) {
  const [text, setText] = useState("");
  
  // Compiler otimiza automaticamente
  const handleClick = () => {
    console.log("Clicked:", data);
  };
  
  const filteredItems = items.filter(item => item.active);
  
  return <div>{/* ... */}</div>;
}
```

**Best Practices**:
- ✅ Escreva código JavaScript direto e simples
- ✅ Deixe o compiler otimizar automaticamente
- ✅ Use memoização manual apenas em casos extremos documentados
- ❌ Não use useCallback/useMemo por padrão

---

### 1.2 Actions API (Simplificação de Operações Assíncronas)

**Actions** gerenciam automaticamente estados de pending, error e success em operações assíncronas.

**Implementação**:
```javascript
// actions.js
"use server"; // Next.js Server Actions

export async function updateUser(userId, formData) {
  const name = formData.get("name");
  const email = formData.get("email");
  
  try {
    await db.users.update(userId, { name, email });
    return { success: true };
  } catch (error) {
    return { success: false, error: error.message };
  }
}
```

```javascript
// ProfilePage.jsx
import { updateUser } from "./actions";

function ProfilePage({ userId }) {
  const updateUserWithId = updateUser.bind(null, userId);
  
  return (
    <form action={updateUserWithId}>
      <input type="text" name="name" required />
      <input type="email" name="email" required />
      <SubmitButton />
    </form>
  );
}
```

**Best Practices**:
- ✅ Use Actions para todas as mutações de dados
- ✅ Combine com useFormStatus para feedback de UI
- ✅ Implemente error handling robusto
- ✅ Valide dados no servidor

---

### 1.3 useOptimistic (Optimistic Updates)

**useOptimistic** permite atualizações otimistas para melhor UX.

**Implementação**:
```javascript
import { useOptimistic } from "react";

function CommentList({ comments }) {
  const [optimisticComments, addOptimisticComment] = useOptimistic(
    comments,
    (state, newComment) => [
      ...state, 
      { id: Date.now(), text: newComment, sending: true }
    ]
  );
  
  const formAction = async (formData) => {
    const comment = formData.get("comment");
    addOptimisticComment(comment);
    await sendComment(comment);
  };
  
  return (
    <>
      <ul>
        {optimisticComments.map(c => (
          <li key={c.id}>
            {c.text}
            {c.sending && <span className="text-gray-400"> (Enviando...)</span>}
          </li>
        ))}
      </ul>
      <form action={formAction}>
        <input type="text" name="comment" required />
        <button type="submit">Enviar</button>
      </form>
    </>
  );
}
```

**Best Practices**:
- ✅ Use para operações frequentes (likes, comments, votes)
- ✅ Sempre implemente rollback em caso de erro
- ✅ Mostre indicador visual de "pending"
- ✅ Combine com toast notifications para confirmação

---

### 1.4 useFormStatus (Status de Formulários)

**useFormStatus** permite acesso ao status do formulário sem prop drilling.

**Implementação**:
```javascript
import { useFormStatus } from "react-dom";

function SubmitButton() {
  const { pending, data, method, action } = useFormStatus();
  
  return (
    <button 
      type="submit" 
      disabled={pending}
      className={pending ? "opacity-50 cursor-not-allowed" : ""}
    >
      {pending ? (
        <>
          <Spinner className="mr-2" />
          Salvando...
        </>
      ) : (
        "Salvar"
      )}
    </button>
  );
}
```

**Best Practices**:
- ✅ Use em componentes reutilizáveis de formulário
- ✅ Desabilite botões durante pending
- ✅ Mostre loading indicators
- ✅ Previna double-submit

---

### 1.5 Server Components (RSC)

**React Server Components** renderizam no servidor, reduzindo bundle size.

**Quando Usar**:
- ✅ Buscar dados de APIs/databases
- ✅ Acessar recursos backend diretamente
- ✅ Renderizar conteúdo estático
- ✅ Manter secrets no servidor

**Quando NÃO Usar**:
- ❌ Componentes com interatividade (onClick, onChange)
- ❌ Hooks de estado (useState, useEffect)
- ❌ Browser APIs (localStorage, window)

**Exemplo**:
```javascript
// ServerComponent.jsx (Server Component)
async function UserProfile({ userId }) {
  // Busca dados diretamente no servidor
  const user = await db.users.findById(userId);
  
  return (
    <div>
      <h1>{user.name}</h1>
      <ClientInteractiveButton userId={userId} />
    </div>
  );
}

// ClientInteractiveButton.jsx (Client Component)
"use client";

function ClientInteractiveButton({ userId }) {
  const [liked, setLiked] = useState(false);
  
  return (
    <button onClick={() => setLiked(!liked)}>
      {liked ? "❤️" : "🤍"}
    </button>
  );
}
```

---

### 6.2. Performance Optimization {#performance}

### 2.1 Core Web Vitals

**Métricas Essenciais**:

| Métrica | Target | Descrição |
|---------|--------|-----------|
| **LCP** (Largest Contentful Paint) | < 2.5s | Tempo para renderizar maior elemento visível |
| **FID** (First Input Delay) | < 100ms | Tempo até primeira interação ser processada |
| **CLS** (Cumulative Layout Shift) | < 0.1 | Estabilidade visual durante carregamento |
| **INP** (Interaction to Next Paint) | < 200ms | Responsividade a interações (substitui FID) |
| **TTFB** (Time to First Byte) | < 600ms | Tempo até primeiro byte do servidor |
| **FCP** (First Contentful Paint) | < 1.8s | Tempo até primeiro conteúdo renderizado |

**Implementação no React**:
```javascript
import { onCLS, onFID, onLCP, onINP, onFCP, onTTFB } from 'web-vitals';

function reportWebVitals(metric) {
  // Enviar para analytics
  console.log(metric);
  
  // Enviar para serviço de monitoramento
  fetch('/api/analytics', {
    method: 'POST',
    body: JSON.stringify(metric),
  });
}

// No componente raiz
useEffect(() => {
  onCLS(reportWebVitals);
  onFID(reportWebVitals);
  onLCP(reportWebVitals);
  onINP(reportWebVitals);
  onFCP(reportWebVitals);
  onTTFB(reportWebVitals);
}, []);
```

---

### 2.2 Code Splitting e Lazy Loading

**Técnicas**:

1. **Route-based Code Splitting**:
```javascript
import { lazy, Suspense } from 'react';

const Dashboard = lazy(() => import('./pages/Dashboard'));
const Reports = lazy(() => import('./pages/Reports'));
const Settings = lazy(() => import('./pages/Settings'));

function App() {
  return (
    <Suspense fallback={<LoadingSpinner />}>
      <Routes>
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/reports" element={<Reports />} />
        <Route path="/settings" element={<Settings />} />
      </Routes>
    </Suspense>
  );
}
```

2. **Component-based Lazy Loading**:
```javascript
const HeavyChart = lazy(() => import('./components/HeavyChart'));

function Dashboard() {
  return (
    <div>
      <QuickStats />
      <Suspense fallback={<ChartSkeleton />}>
        <HeavyChart data={data} />
      </Suspense>
    </div>
  );
}
```

3. **Dynamic Imports**:
```javascript
async function loadHeavyLibrary() {
  const { default: heavyLib } = await import('heavy-library');
  return heavyLib;
}
```

---

### 2.3 Bundle Size Optimization (Vite)

**Técnicas para Reduzir Bundle**:

1. **Tree Shaking**:
```javascript
// ❌ Importa toda a biblioteca
import _ from 'lodash';

// ✅ Importa apenas o necessário
import debounce from 'lodash/debounce';
import throttle from 'lodash/throttle';
```

2. **Vite Build Optimization**:
```javascript
// vite.config.js
export default {
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          'vendor': ['react', 'react-dom'],
          'charts': ['recharts', 'd3'],
          'utils': ['lodash', 'date-fns']
        }
      }
    },
    chunkSizeWarningLimit: 500,
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true,
        drop_debugger: true
      }
    }
  }
};
```

3. **Image Optimization**:
```javascript
// Usar next/image ou bibliotecas similares
import Image from 'next/image';

<Image
  src="/chart.png"
  width={800}
  height={600}
  alt="Cost trend chart"
  loading="lazy"
  placeholder="blur"
/>
```

---

### 2.4 Virtualization (Listas Grandes)

Para listas com 1000+ items, use virtualização:

```javascript
import { FixedSizeList } from 'react-window';

function LargeList({ items }) {
  const Row = ({ index, style }) => (
    <div style={style}>
      {items[index].name}
    </div>
  );
  
  return (
    <FixedSizeList
      height={600}
      itemCount={items.length}
      itemSize={50}
      width="100%"
    >
      {Row}
    </FixedSizeList>
  );
}
```

**Bibliotecas Recomendadas**:
- **react-window**: Leve e performático
- **react-virtualized**: Mais features, mais pesado
- **TanStack Virtual**: Moderno, flexível

---

### 6.3. Testing Strategies {#testing}

### 3.1 Pirâmide de Testes

```
        /\
       /  \
      / E2E \          10% - Testes End-to-End (Playwright)
     /--------\
    /          \
   / Integration \     20% - Testes de Integração
  /--------------\
 /                \
/   Unit Tests     \   70% - Testes Unitários (Vitest + RTL)
--------------------
```

---

### 3.2 Unit Testing (Vitest + React Testing Library)

**Setup**:
```javascript
// vitest.config.js
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: './src/test/setup.ts',
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      exclude: ['node_modules/', 'src/test/']
    }
  }
});
```

**Exemplo de Teste**:
```javascript
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import Button from './Button';

describe('Button Component', () => {
  it('should render with correct text', () => {
    render(<Button>Click me</Button>);
    expect(screen.getByText('Click me')).toBeInTheDocument();
  });
  
  it('should call onClick when clicked', () => {
    const handleClick = vi.fn();
    render(<Button onClick={handleClick}>Click</Button>);
    
    fireEvent.click(screen.getByText('Click'));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });
  
  it('should be disabled when loading', () => {
    render(<Button loading>Submit</Button>);
    expect(screen.getByRole('button')).toBeDisabled();
  });
});
```

**Best Practices**:
- ✅ Teste comportamento, não implementação
- ✅ Use queries por acessibilidade (getByRole, getByLabelText)
- ✅ Evite testar detalhes de implementação
- ✅ Mock apenas dependências externas
- ✅ Cobertura mínima: 80%

---

### 3.3 Integration Testing

**Exemplo**:
```javascript
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import LoginForm from './LoginForm';

describe('LoginForm Integration', () => {
  it('should login user successfully', async () => {
    const user = userEvent.setup();
    const queryClient = new QueryClient();
    
    render(
      <QueryClientProvider client={queryClient}>
        <LoginForm />
      </QueryClientProvider>
    );
    
    await user.type(screen.getByLabelText('Email'), 'user@example.com');
    await user.type(screen.getByLabelText('Password'), 'password123');
    await user.click(screen.getByRole('button', { name: /login/i }));
    
    await waitFor(() => {
      expect(screen.getByText('Welcome back!')).toBeInTheDocument();
    });
  });
});
```

---

### 3.4 E2E Testing (Playwright)

**Setup**:
```javascript
// playwright.config.ts
import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure'
  },
  webServer: {
    command: 'pnpm dev',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI
  }
});
```

**Exemplo de Teste E2E**:
```javascript
import { test, expect } from '@playwright/test';

test('user can view cost dashboard', async ({ page }) => {
  await page.goto('/dashboard');
  
  // Verificar elementos principais
  await expect(page.getByRole('heading', { name: 'Cost Dashboard' })).toBeVisible();
  
  // Verificar gráficos carregados
  await expect(page.locator('canvas')).toBeVisible();
  
  // Interagir com filtros
  await page.getByLabel('Date Range').selectOption('last-30-days');
  
  // Verificar atualização
  await expect(page.getByText('Last 30 Days')).toBeVisible();
  
  // Screenshot para visual regression
  await expect(page).toHaveScreenshot('dashboard.png');
});
```

**Best Practices**:
- ✅ Teste user journeys completos
- ✅ Use Page Object Model para reutilização
- ✅ Implemente visual regression testing
- ✅ Execute em CI/CD pipeline
- ✅ Teste em múltiplos browsers

---

### 6.4. UX/UI Design Principles {#ux-ui}

### 4.1 10 Heurísticas de Nielsen

1. **Visibility of System Status**: Sistema deve sempre informar o usuário sobre o que está acontecendo
2. **Match Between System and Real World**: Usar linguagem familiar ao usuário
3. **User Control and Freedom**: Fornecer "saídas de emergência" (undo/redo)
4. **Consistency and Standards**: Seguir convenções da plataforma
5. **Error Prevention**: Prevenir erros antes que ocorram
6. **Recognition Rather Than Recall**: Minimizar carga de memória do usuário
7. **Flexibility and Efficiency of Use**: Atalhos para usuários experientes
8. **Aesthetic and Minimalist Design**: Diálogos sem informação irrelevante
9. **Help Users Recognize, Diagnose, and Recover from Errors**: Mensagens de erro claras
10. **Help and Documentation**: Documentação fácil de buscar e focada em tarefas

---

### 4.2 Princípios de Design Visual

**Hierarquia Visual**:
- **Tamanho**: Elementos maiores atraem mais atenção
- **Cor**: Cores vibrantes destacam elementos importantes
- **Contraste**: Alto contraste para CTAs e alertas
- **Espaçamento**: White space melhora legibilidade
- **Tipografia**: Máximo 2-3 fontes diferentes

**Exemplo de Hierarquia em Dashboard**:
```
┌─────────────────────────────────────┐
│  📊 Cost Dashboard          [Filter]│  ← Header (48px)
├─────────────────────────────────────┤
│  ┌──────┐  ┌──────┐  ┌──────┐     │
│  │ $12K │  │ +15% │  │  85% │     │  ← KPI Cards (destaque)
│  │Total │  │Growth│  │ Eff. │     │
│  └──────┘  └──────┘  └──────┘     │
├─────────────────────────────────────┤
│  ┌───────────────────────────────┐ │
│  │   📈 Trend Chart (grande)     │ │  ← Gráfico Principal
│  │                               │ │
│  └───────────────────────────────┘ │
├─────────────────────────────────────┤
│  ┌──────────┐  ┌──────────────────┐│
│  │ Breakdown│  │  Recent Activity ││  ← Gráficos Secundários
│  └──────────┘  └──────────────────┘│
└─────────────────────────────────────┘
```

---

### 4.3 Color Theory para Dashboards

**Paleta Funcional**:
- **Primary**: Ações principais (azul: #3B82F6)
- **Success**: Confirmações, crescimento (verde: #10B981)
- **Warning**: Alertas moderados (amarelo: #F59E0B)
- **Danger**: Erros, decréscimos (vermelho: #EF4444)
- **Neutral**: Texto e backgrounds (cinza: #6B7280)

**Acessibilidade de Cores**:
- Contraste mínimo 4.5:1 para texto
- Não usar apenas cor para transmitir informação
- Suportar modo claro e escuro
- Considerar daltonismo (usar padrões além de cores)

---

### 4.4 Micro-interactions

**Feedback Visual Imediato**:
```javascript
function InteractiveCard({ onClick }) {
  return (
    <div 
      onClick={onClick}
      className="
        transition-all duration-200
        hover:scale-105 hover:shadow-lg
        active:scale-95
        cursor-pointer
      "
    >
      {/* conteúdo */}
    </div>
  );
}
```

**Loading States**:
```javascript
function DataCard({ isLoading, data }) {
  if (isLoading) {
    return <Skeleton className="h-32 w-full" />;
  }
  
  return <div>{data}</div>;
}
```

---

### 6.5. Acessibilidade (WCAG 2.2) {#acessibilidade}

### 5.1 Checklist de Acessibilidade

**Nível A (Mínimo)**:
- [ ] Todas as imagens têm alt text descritivo
- [ ] Formulários têm labels associados
- [ ] Navegação por teclado funciona
- [ ] Contraste de cores adequado (4.5:1)
- [ ] Sem conteúdo que pisca > 3x por segundo

**Nível AA (Recomendado)**:
- [ ] Indicador de foco visível
- [ ] Mensagens de erro descritivas
- [ ] Headings hierárquicos (h1, h2, h3)
- [ ] Landmarks ARIA (nav, main, aside)
- [ ] Target size mínimo 44x44px para touch

**Nível AAA (Ideal)**:
- [ ] Contraste de cores 7:1
- [ ] Sem timeout em sessões
- [ ] Ajuda contextual disponível

---

### 5.2 ARIA Best Practices

**Roles**:
```javascript
<nav role="navigation" aria-label="Main">
  <ul role="list">
    <li role="listitem">
      <a href="/dashboard" aria-current="page">Dashboard</a>
    </li>
  </ul>
</nav>

<main role="main" aria-labelledby="page-title">
  <h1 id="page-title">Cost Dashboard</h1>
</main>

<aside role="complementary" aria-label="Filters">
  {/* filtros */}
</aside>
```

**Live Regions** (para conteúdo dinâmico):
```javascript
function AlertBanner({ message, type }) {
  return (
    <div 
      role="alert" 
      aria-live="assertive"
      aria-atomic="true"
      className={`alert alert-${type}`}
    >
      {message}
    </div>
  );
}
```

**Form Accessibility**:
```javascript
<form>
  <div>
    <label htmlFor="email">Email</label>
    <input 
      id="email"
      type="email"
      aria-required="true"
      aria-invalid={errors.email ? "true" : "false"}
      aria-describedby={errors.email ? "email-error" : undefined}
    />
    {errors.email && (
      <span id="email-error" role="alert">
        {errors.email}
      </span>
    )}
  </div>
</form>
```

---

### 6.6. Dashboard Design {#dashboard}

### 6.1 Tipos de Dashboards

| Tipo | Propósito | Características |
|------|-----------|-----------------|
| **Reporting** | Contar história com dados | Export, share, visualizações estáticas |
| **Monitoring** | Alertar e avisar | Real-time, alertas, anomalias |
| **Exploring** | Descobrir insights | Filtros, drill-down, interatividade |
| **Functional** | Guiar foco do usuário | Integrado ao workflow, ações rápidas |
| **Homepage** | Navegação contextual | Overview + navegação |

---

### 6.2 Anatomia de um Dashboard

**Estrutura Recomendada**:

1. **Header** (Navegação e Contexto)
   - Título da página
   - Breadcrumbs
   - Filtros globais (date range, team, project)
   - Actions (export, share, refresh)

2. **KPI Cards** (Métricas Principais)
   - 3-5 KPIs mais importantes
   - Valor atual + comparação (vs. período anterior)
   - Sparklines para tendência
   - Indicador visual (↑ verde, ↓ vermelho)

3. **Primary Visualization** (Gráfico Principal)
   - Maior gráfico da página
   - Tendência ao longo do tempo
   - Interativo (zoom, pan, tooltip)

4. **Secondary Visualizations** (Gráficos Secundários)
   - Breakdown por categoria
   - Comparações
   - Distribuições

5. **Data Table** (Detalhes)
   - Dados tabulares
   - Sorting, filtering, pagination
   - Export CSV/Excel

---

### 6.3 Escolha de Visualizações

| Objetivo | Tipo de Gráfico | Quando Usar |
|----------|-----------------|-------------|
| **Tendência ao longo do tempo** | Line Chart | Mostrar evolução de custos |
| **Comparação entre categorias** | Bar Chart | Comparar custos por serviço |
| **Distribuição percentual** | Pie/Donut Chart | Mostrar % de custos por categoria |
| **Hierarquia de valores** | Treemap | Visualizar custos hierárquicos |
| **Correlação entre variáveis** | Scatter Plot | Relação entre uso e custo |
| **Padrões ao longo do tempo** | Heatmap | Uso por hora/dia da semana |
| **Performance vs. Target** | Gauge Chart | KPIs vs. metas |
| **Comparação de múltiplas métricas** | Radar Chart | Comparar dimensões |

---

### 6.4 Best Practices de Dashboard UX

**Progressive Disclosure**:
```
Level 1: Overview (default)
  ↓ (click para drill-down)
Level 2: Category Breakdown
  ↓ (click para drill-down)
Level 3: Individual Items
```

**Filters e Controls**:
- Posicionar no topo ou sidebar
- Mostrar filtros ativos claramente
- Permitir "clear all filters"
- Salvar preferências de filtro

**Loading States**:
```javascript
function Dashboard() {
  const { data, isLoading } = useQuery('costs', fetchCosts);
  
  if (isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-32 w-full" />
        <Skeleton className="h-64 w-full" />
        <Skeleton className="h-48 w-full" />
      </div>
    );
  }
  
  return <DashboardContent data={data} />;
}
```

**Empty States**:
```javascript
function EmptyState() {
  return (
    <div className="text-center py-12">
      <Icon name="chart-empty" className="w-24 h-24 mx-auto text-gray-300" />
      <h3 className="mt-4 text-lg font-medium">No data available</h3>
      <p className="mt-2 text-gray-500">
        Try adjusting your filters or date range
      </p>
      <button className="mt-4">Clear Filters</button>
    </div>
  );
}
```

---

### 6.7. Navegabilidade e Information Architecture {#navegabilidade}

### 7.1 Navigation Patterns

**1. Top Navigation (Horizontal)**:
- Ideal para 5-7 items principais
- Sempre visível
- Indica página atual

**2. Sidebar Navigation (Vertical)**:
- Ideal para 8+ items
- Pode ser collapsible
- Suporta hierarquia (nested menus)

**3. Breadcrumbs**:
```javascript
function Breadcrumbs({ items }) {
  return (
    <nav aria-label="Breadcrumb">
      <ol className="flex items-center space-x-2">
        {items.map((item, index) => (
          <li key={item.path} className="flex items-center">
            {index > 0 && <span className="mx-2">/</span>}
            {index === items.length - 1 ? (
              <span aria-current="page">{item.label}</span>
            ) : (
              <a href={item.path}>{item.label}</a>
            )}
          </li>
        ))}
      </ol>
    </nav>
  );
}
```

**4. Tabs**:
- Para conteúdo relacionado na mesma página
- Máximo 5-7 tabs
- Indicar tab ativo claramente

---

### 7.2 Search UX

**Autocomplete**:
```javascript
function SearchWithAutocomplete() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  
  const debouncedSearch = useDebouncedCallback(
    async (value) => {
      const data = await searchAPI(value);
      setResults(data);
    },
    300
  );
  
  return (
    <div className="relative">
      <input
        type="search"
        value={query}
        onChange={(e) => {
          setQuery(e.target.value);
          debouncedSearch(e.target.value);
        }}
        aria-label="Search"
        aria-autocomplete="list"
        aria-controls="search-results"
      />
      {results.length > 0 && (
        <ul id="search-results" role="listbox">
          {results.map(result => (
            <li key={result.id} role="option">
              {result.name}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
```

**Best Practices**:
- ✅ Debounce de 300ms
- ✅ Mostrar sugestões após 2-3 caracteres
- ✅ Highlight do termo buscado
- ✅ Keyboard navigation (arrow keys)
- ✅ Mostrar "No results" quando vazio

---

### 7.3 Pagination vs. Infinite Scroll

**Pagination** (Recomendado para Dashboards):
```javascript
function PaginatedTable({ data, pageSize = 20 }) {
  const [page, setPage] = useState(1);
  
  const paginatedData = data.slice(
    (page - 1) * pageSize,
    page * pageSize
  );
  
  return (
    <>
      <Table data={paginatedData} />
      <Pagination
        currentPage={page}
        totalPages={Math.ceil(data.length / pageSize)}
        onPageChange={setPage}
      />
    </>
  );
}
```

**Quando Usar Cada Um**:
- **Pagination**: Dashboards, tabelas, relatórios, quando usuário precisa encontrar item específico
- **Infinite Scroll**: Feeds sociais, galerias de imagens, quando consumo é contínuo

---

### 6.8. Design Systems {#design-systems}

### 8.1 Design Tokens

**Estrutura**:
```javascript
// tokens/colors.js
export const colors = {
  // Brand
  primary: {
    50: '#EFF6FF',
    100: '#DBEAFE',
    500: '#3B82F6',  // Main
    600: '#2563EB',
    900: '#1E3A8A'
  },
  
  // Semantic
  success: '#10B981',
  warning: '#F59E0B',
  error: '#EF4444',
  info: '#3B82F6',
  
  // Neutral
  gray: {
    50: '#F9FAFB',
    100: '#F3F4F6',
    500: '#6B7280',
    900: '#111827'
  }
};

// tokens/spacing.js
export const spacing = {
  xs: '0.25rem',  // 4px
  sm: '0.5rem',   // 8px
  md: '1rem',     // 16px
  lg: '1.5rem',   // 24px
  xl: '2rem',     // 32px
  '2xl': '3rem'   // 48px
};

// tokens/typography.js
export const typography = {
  fontFamily: {
    sans: 'Inter, system-ui, sans-serif',
    mono: 'Fira Code, monospace'
  },
  fontSize: {
    xs: '0.75rem',    // 12px
    sm: '0.875rem',   // 14px
    base: '1rem',     // 16px
    lg: '1.125rem',   // 18px
    xl: '1.25rem',    // 20px
    '2xl': '1.5rem',  // 24px
    '3xl': '1.875rem' // 30px
  },
  fontWeight: {
    normal: 400,
    medium: 500,
    semibold: 600,
    bold: 700
  }
};
```

---

### 8.2 Component Architecture

**Atomic Design**:
```
Atoms (Básicos)
  ├─ Button
  ├─ Input
  ├─ Label
  └─ Icon

Molecules (Compostos)
  ├─ FormField (Label + Input + Error)
  ├─ SearchBar (Input + Icon + Button)
  └─ Card (Container + Header + Body)

Organisms (Complexos)
  ├─ Header (Logo + Nav + Search + User)
  ├─ DataTable (Headers + Rows + Pagination)
  └─ ChartCard (Title + Chart + Legend)

Templates (Layouts)
  ├─ DashboardLayout
  ├─ FormLayout
  └─ ReportLayout

Pages (Instâncias)
  ├─ CostDashboard
  ├─ UserSettings
  └─ MonthlyReport
```

---

### 6.9. TypeScript Best Practices {#typescript}

### 9.1 Component Props Typing

```typescript
// Tipos básicos
interface ButtonProps {
  children: React.ReactNode;
  variant?: 'primary' | 'secondary' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  disabled?: boolean;
  loading?: boolean;
  onClick?: () => void;
}

export function Button({ 
  children, 
  variant = 'primary',
  size = 'md',
  disabled = false,
  loading = false,
  onClick 
}: ButtonProps) {
  return (
    <button
      disabled={disabled || loading}
      onClick={onClick}
      className={`btn btn-${variant} btn-${size}`}
    >
      {loading ? <Spinner /> : children}
    </button>
  );
}
```

**Tipos Avançados**:
```typescript
// Generics para componentes reutilizáveis
interface DataTableProps<T> {
  data: T[];
  columns: Column<T>[];
  onRowClick?: (row: T) => void;
}

function DataTable<T extends { id: string }>({ 
  data, 
  columns, 
  onRowClick 
}: DataTableProps<T>) {
  return (
    <table>
      {/* implementação */}
    </table>
  );
}

// Uso
<DataTable<User> 
  data={users} 
  columns={userColumns}
  onRowClick={(user) => console.log(user.email)}
/>
```

---

### 9.2 API Response Typing

```typescript
// types/api.ts
export interface CostData {
  date: string;
  total: number;
  breakdown: {
    service: string;
    cost: number;
  }[];
}

export interface ApiResponse<T> {
  data: T;
  meta: {
    page: number;
    totalPages: number;
    totalItems: number;
  };
}

// hooks/useCosts.ts
export function useCosts(filters: CostFilters) {
  return useQuery<ApiResponse<CostData[]>>({
    queryKey: ['costs', filters],
    queryFn: () => fetchCosts(filters)
  });
}
```

---

### 6.10. Security Frontend {#security}

### 10.1 XSS Prevention

```javascript
// ❌ NUNCA fazer isso
function DangerousComponent({ userInput }) {
  return <div dangerouslySetInnerHTML={{ __html: userInput }} />;
}

// ✅ Sanitizar input
import DOMPurify from 'dompurify';

function SafeComponent({ userInput }) {
  const sanitized = DOMPurify.sanitize(userInput);
  return <div dangerouslySetInnerHTML={{ __html: sanitized }} />;
}

// ✅ Melhor ainda: evitar HTML
function BestComponent({ userInput }) {
  return <div>{userInput}</div>; // React escapa automaticamente
}
```

---

### 10.2 CSRF Protection

```javascript
// Incluir CSRF token em requests
async function submitForm(formData) {
  const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content;
  
  const response = await fetch('/api/update', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRF-Token': csrfToken
    },
    body: JSON.stringify(formData)
  });
  
  return response.json();
}
```

---

### 10.3 Content Security Policy (CSP)

```html
<!-- index.html -->
<meta 
  http-equiv="Content-Security-Policy" 
  content="
    default-src 'self';
    script-src 'self' 'unsafe-inline' https://cdn.example.com;
    style-src 'self' 'unsafe-inline';
    img-src 'self' data: https:;
    font-src 'self' data:;
    connect-src 'self' https://api.example.com;
  "
/>
```

---

### 10.4 Sensitive Data Handling

```javascript
// ❌ NUNCA armazenar tokens em localStorage
localStorage.setItem('authToken', token);

// ✅ Usar httpOnly cookies (gerenciado pelo backend)
// ✅ Ou sessionStorage para dados temporários
sessionStorage.setItem('tempData', JSON.stringify(data));

// ✅ Limpar dados sensíveis ao desmontar
useEffect(() => {
  return () => {
    sessionStorage.removeItem('tempData');
  };
}, []);
```

---

### 6.X. Resumo de Ferramentas Recomendadas

### Build Tools
- **Vite**: Build tool moderno e rápido
- **Turbopack**: Next.js bundler (experimental)

### State Management
- **TanStack Query**: Server state (recomendado)
- **Zustand**: Client state simples
- **Jotai**: Atomic state management

### Forms
- **React Hook Form**: Performance e DX
- **Zod**: Validação com TypeScript

### Styling
- **Tailwind CSS**: Utility-first (recomendado)
- **CSS Modules**: Scoped CSS
- **styled-components**: CSS-in-JS

### UI Components
- **shadcn/ui**: Componentes copiáveis (recomendado)
- **Radix UI**: Headless components
- **Headless UI**: Tailwind-friendly

### Charts
- **Recharts**: Declarativo, fácil de usar
- **Chart.js**: Flexível, performático
- **D3.js**: Máximo controle (curva de aprendizado)

### Testing
- **Vitest**: Unit/Integration (recomendado)
- **React Testing Library**: Component testing
- **Playwright**: E2E testing
- **MSW**: API mocking

### Accessibility
- **axe DevTools**: Testes automatizados
- **WAVE**: Avaliação visual
- **Lighthouse**: Auditoria completa

---

### 6.X. Checklist de Qualidade Frontend

### Performance
- [ ] LCP < 2.5s
- [ ] FID/INP < 100ms
- [ ] CLS < 0.1
- [ ] Bundle size < 200KB (initial)
- [ ] Code splitting implementado
- [ ] Images otimizadas (WebP, lazy loading)
- [ ] Fonts otimizadas (subset, preload)

### Acessibilidade
- [ ] WCAG 2.2 Level AA compliance
- [ ] Keyboard navigation funcional
- [ ] Screen reader testado
- [ ] Contraste adequado (4.5:1)
- [ ] ARIA labels corretos
- [ ] Focus indicators visíveis

### UX/UI
- [ ] Loading states em todas as operações
- [ ] Error states com mensagens claras
- [ ] Empty states informativos
- [ ] Responsive design (mobile, tablet, desktop)
- [ ] Dark mode suportado
- [ ] Micro-interactions implementadas

### Testing
- [ ] Cobertura de testes > 80%
- [ ] Testes E2E para fluxos críticos
- [ ] Visual regression testing
- [ ] Performance testing
- [ ] Accessibility testing automatizado

### Security
- [ ] XSS prevention
- [ ] CSRF protection
- [ ] CSP configurado
- [ ] Sensitive data não exposta
- [ ] Dependencies atualizadas

---

### 6.X. Aplicação Específica para Finops-Teste

### Dashboard de Custos

**KPIs Principais**:
1. **Total Spend** (Gasto Total)
2. **Cost per Customer** (Custo por Cliente)
3. **Cloud Efficiency Rate** (Taxa de Eficiência)
4. **Forecasted Costs** (Custos Previstos)
5. **Waste Percentage** (% de Desperdício)

**Visualizações Recomendadas**:
- **Line Chart**: Tendência de custos ao longo do tempo
- **Treemap**: Breakdown de custos por serviço/região
- **Bar Chart**: Comparação mensal
- **Gauge**: Eficiência vs. target
- **Heatmap**: Uso por hora/dia

**Filtros Essenciais**:
- Date Range (Last 7/30/90 days, Custom)
- Service (EC2, S3, RDS, Lambda, etc.)
- Region (us-east-1, us-west-2, etc.)
- Team/Project
- Environment (prod, staging, dev)

**Interações**:
- Drill-down de custos totais → por serviço → por recurso
- Export para CSV/Excel
- Share dashboard (link, email)
- Save custom views
- Set budget alerts

---

### 6.X. Referências

1. React 19 Official Docs - https://react.dev/blog/2024/12/05/react-19
2. WCAG 2.2 Guidelines - https://www.w3.org/TR/WCAG22/
3. Nielsen Norman Group - https://www.nngroup.com/
4. Web.dev Performance - https://web.dev/vitals/
5. Pencil & Paper Dashboard UX - https://www.pencilandpaper.io/articles/ux-pattern-analysis-data-dashboards
6. CloudZero FinOps Dashboards - https://www.cloudzero.com/blog/finops-dashboards/

---

**Última Atualização**: 25 de novembro de 2025


---

## 🌱 Green IT e Sustentabilidade

O projeto deve ser ambientalmente responsável, minimizando seu impacto ecológico.

- **Métricas de Sustentabilidade**: Monitorar e reportar:
  - **Carbon Emissions (CO2)**: Emissões de carbono por workload/serviço.
  - **Energy Consumption**: Consumo de energia.
- **Carbon-Aware Computing**: Quando possível, agendar workloads em regiões e horários com maior disponibilidade de energia renovável.
- **Código Eficiente**: Adotar práticas de programação que reduzam o consumo de CPU e memória.
- **Ferramentas**: Utilizar ferramentas como Cloud Carbon Footprint para medição.

---

## 🧪 Qualidade e Estratégia de Testes

A qualidade será garantida por uma estratégia de testes abrangente, automatizada e integrada ao pipeline de CI/CD.

### 1. Pirâmide de Testes

A base será de **testes unitários**, seguidos por **testes de integração** e uma pequena quantidade de **testes End-to-End (E2E)**.

```
        /\
       /  \  E2E (poucos)
      /____\
     /      \  Integration (médio)
    /________\
   /          \  Unit (muitos)
  /____________\
```

### 2. Test-Driven Development (TDD)

As regras de negócio e a lógica de domínio serão desenvolvidas utilizando TDD (Red-Green-Refactor).

**Ciclo TDD**:
1. **Red**: Escrever um teste que falha
2. **Green**: Escrever o código mínimo para passar o teste
3. **Refactor**: Melhorar o código mantendo os testes passando

### 3. Behavior-Driven Development (BDD)

Os casos de uso serão guiados por especificações de comportamento em linguagem natural.

**Exemplo**:
```gherkin
Feature: Otimização de Custos
  Scenario: Identificar recursos subutilizados
    Given um recurso EC2 com uso de CPU < 30% por 7 dias
    When o sistema analisa métricas de utilização
    Then uma recomendação de downsizing deve ser gerada
```

### 4. Cobertura de Testes

A cobertura de código por testes automatizados deve ser **superior a 80%**.

**Métricas de Cobertura**:
- **Domain Layer**: 100% (regras de negócio críticas)
- **Use Cases**: > 90%
- **Controllers**: > 70%
- **Infrastructure**: > 60% (com Testcontainers)

### 5. Tipos de Testes

#### Testes Unitários
- Testar unidades isoladas (funções, métodos, classes)
- Utilizar mocks para dependências externas
- Rápidos e determinísticos

#### Testes de Integração
- Testar a integração entre componentes
- Utilizar **Testcontainers** para bancos de dados reais
- Validar contratos de API

#### Testes de Contrato
- Garantir compatibilidade entre serviços
- Utilizar ferramentas como Pact

#### Testes de Performance
- **Load Testing**: Validar comportamento sob carga esperada
- **Stress Testing**: Identificar limites do sistema
- **Soak Testing**: Validar estabilidade em execução prolongada
- Ferramenta: k6, JMeter ou Gatling

#### Testes de Segurança
- **SAST (Static Application Security Testing)**: Análise estática de código
- **DAST (Dynamic Application Security Testing)**: Análise dinâmica em runtime
- **Dependency Scanning**: Verificar vulnerabilidades em dependências

#### Testes End-to-End (E2E)
- Testar fluxos críticos completos
- Mínimo necessário (3-5 fluxos principais)
- Ambiente isolado e reproduzível

### 6. Testes de Mutação

Avaliar a eficácia dos testes introduzindo falhas no código. Ferramentas: Stryker, PIT.

---

## 🔒 Segurança e Operações (DevSecOps)

A segurança será integrada em todo o ciclo de vida do desenvolvimento, desde a concepção até a produção.

### 1. OWASP Top 10

Mitigar proativamente as principais vulnerabilidades de segurança web:

- **Injection**: Validar e sanitizar todas as entradas
- **Broken Authentication**: Implementar autenticação robusta (OAuth 2.0, JWT)
- **Sensitive Data Exposure**: Criptografar dados sensíveis em trânsito e em repouso
- **XML External Entities (XXE)**: Desabilitar processamento de entidades externas
- **Broken Access Control**: Implementar RBAC (Role-Based Access Control)
- **Security Misconfiguration**: Hardening de configurações
- **Cross-Site Scripting (XSS)**: Escapar outputs e usar CSP (Content Security Policy)
- **Insecure Deserialization**: Validar dados deserializados
- **Using Components with Known Vulnerabilities**: Manter dependências atualizadas
- **Insufficient Logging & Monitoring**: Implementar logging abrangente

### 2. Threat Modeling

Identificar e mitigar ameaças específicas do domínio:

- Manipulação de dados de custo
- Acesso não autorizado a recursos sensíveis
- Race conditions em operações críticas
- SQL Injection e NoSQL Injection
- Account takeover
- Fraude financeira

### 3. Gestão de Segredos

Nenhum segredo (chaves de API, senhas, tokens) deve ser *hardcoded* no código ou em arquivos de configuração versionados.

**Estratégias**:
- Utilizar variáveis de ambiente
- Utilizar Secret Managers (HashiCorp Vault, AWS Secrets Manager, Azure Key Vault)
- Rotação automática de segredos
- Princípio do menor privilégio

### 4. Segurança de Rede

- **Zero-Trust Network**: Não confiar em nenhuma rede, mesmo internas
- **mTLS (Mutual TLS)**: Autenticação mútua entre serviços
- **Network Policies**: Micro-segmentação no Kubernetes
- **WAF (Web Application Firewall)**: Proteção contra ataques web

### 5. Compliance e Auditoria

- **Audit Logging**: Rastreabilidade completa de todas as operações críticas
- **Data Privacy**: Conformidade com GDPR, LGPD
- **Retention Policies**: Políticas de retenção e arquivamento de dados
- **Right to be Forgotten**: Implementar mecanismos de deleção de dados

---

## 📊 Observabilidade

### 3. Métricas e KPIs Avançados

Além das métricas RED/USE, o sistema deve monitorar KPIs de negócio e FinOps:

- **FinOps KPIs**:
  - **Cost per Transaction/User**: Custo por transação de negócio ou por usuário ativo.
  - **Waste Percentage**: % de custo gerado por recursos ociosos.
  - **Commitment Coverage**: % de uso coberto por RIs/Savings Plans.
  - **Spot Instance Adoption**: % de workloads em instâncias Spot.
  - **Tag Compliance Rate**: % de recursos com tags corretas.
- **Green IT KPIs**:
  - **Carbon Emissions (gCO2eq)**: Gramas de CO2 equivalente por hora/transação.
 e FinOps

O sistema deve ser totalmente observável, com um foco especial em métricas de custo e otimização.

### 1. Os 3 Pilares da Observabilidade

#### Logs Estruturados

Todos os logs devem ser em formato JSON, contendo campos obrigatórios:

```json
{
  "timestamp": "2025-11-25T10:30:00Z",
  "level": "INFO",
  "service_name": "finops-teste",
  "trace_id": "abc123",
  "correlation_id": "xyz789",
  "request_id": "req-456",
  "operation": "calculate_cost",
  "latency_ms": 45,
  "status": "success",
  "user_id": "user-123",
  "message": "Cost calculation completed"
}
```

**Centralização**: Utilizar ELK Stack (Elasticsearch, Logstash, Kibana) ou Loki.

#### Métricas

Coletar métricas em múltiplas camadas:

**Métricas de Negócio (FinOps)**:
- Custo total por período
- Custo por recurso/serviço
- Taxa de otimização de custos
- Economia gerada por recomendações
- Recursos subutilizados

**Métricas de Aplicação (RED)**:
- **Rate**: Taxa de requisições por segundo
- **Errors**: Taxa de erros
- **Duration**: Latência das requisições (P50, P95, P99)

**Métricas de Sistema (USE)**:
- **Utilization**: Uso de CPU, memória, disco
- **Saturation**: Filas, threads aguardando
- **Errors**: Erros de sistema

**Métricas Adicionais**:
- Cache hit rate
- Tamanho de filas
- Throughput de mensagens
- Database connection pool

**Ferramenta**: Prometheus + Grafana

#### Traces (Rastreamento Distribuído)

Implementar rastreamento distribuído para analisar o fluxo completo de requisições através dos componentes do sistema.

**Ferramenta**: OpenTelemetry + Jaeger ou Zipkin

### 2. Métricas e Dashboards de FinOps

Criar dashboards específicos para monitorar e otimizar custos:

**Dashboard de Custos**:
- Custo total por dia/semana/mês
- Breakdown de custos por serviço (compute, storage, network)
- Tendências de custos
- Comparação com orçamento

**Dashboard de Otimização**:
- Recursos subutilizados (CPU < 30%, memória < 40%)
- Recomendações de rightsizing
- Economia potencial
- Instâncias elegíveis para Spot/Reserved

**Dashboard de Eficiência**:
- Custo por transação
- Custo por usuário
- ROI de otimizações implementadas

### 3. Alertas Inteligentes

Configurar alertas proativos para:

- **P0 (Crítico)**: Sistema indisponível, erro rate > 5%
- **P1 (Alto)**: Latência P95 > SLO, custo > 120% do orçamento
- **P2 (Médio)**: Recursos subutilizados, oportunidades de otimização

**Estratégia de Alertas**:
- Evitar alert fatigue (fadiga de alertas)
- Alertas acionáveis
- Runbooks associados a cada alerta

---

## 🚀 Performance e Escalabilidade

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

## 🛠️ Stack Tecnológica Progressiva

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

## 📝 Documentação e Developer Experience

A documentação será tratada como código, versionada e mantida atualizada.

### 1. README.md EXTREMAMENTE DETALHADO

O README deve ser a porta de entrada do projeto, contendo:

- **Visão Geral**: O que é o projeto, qual problema resolve
- **Arquitetura**: Diagrama de arquitetura, componentes principais
- **Quick Start**: Como rodar o projeto em 5 minutos
- **Requisitos**: Dependências e pré-requisitos
- **Instalação**: Passo a passo detalhado
- **Configuração**: Variáveis de ambiente, secrets
- **Uso**: Exemplos de uso, APIs disponíveis
- **Testes**: Como rodar os testes
- **Deploy**: Como fazer deploy
- **Contribuição**: Guidelines para contribuidores
- **Troubleshooting**: Problemas comuns e soluções
- **Roadmap**: Próximas features e melhorias

### 2. Architecture Decision Records (ADRs)

Documentar todas as decisões arquiteturais importantes:

```markdown
# ADR-001: Escolha do Banco de Dados

## Status
Aceito

## Contexto
Precisamos escolher um banco de dados para o projeto Finops-Teste.

## Decisão
Utilizaremos PostgreSQL como banco de dados principal.

## Consequências
- Transações ACID nativas
- Suporte a JSONB para flexibilidade
- Maturidade e comunidade ativa
- Necessidade de gerenciar migrations
```

### 3. API Documentation

- **OpenAPI 3.0**: Especificação completa das APIs
- **Swagger UI**: Interface interativa para testar APIs
- **Exemplos**: Requests e responses de exemplo
- **Códigos de Erro**: Documentação de todos os códigos de erro

### 4. Runbooks Operacionais

Documentar procedimentos operacionais:

- Como investigar e resolver incidentes
- Como fazer rollback de deploy
- Como escalar manualmente
- Como restaurar backup
- Como rotacionar segredos

### 5. Código Auto-Documentado

- Nomes claros e expressivos
- Comentários apenas para justificar decisões complexas
- Docstrings para funções públicas
- Exemplos de uso em comentários

---

## 🔄 Estratégia de Implementação Faseada

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

## 🚫 Anti-Patterns a Evitar

Evitar ativamente os seguintes anti-patterns:

- **Distributed Monolith**: Microserviços com alto acoplamento
- **Premature Optimization**: Otimizar antes de medir
- **Over Abstraction**: Abstrações desnecessárias que complicam o código
- **Resume-Driven Development**: Usar tecnologias apenas para o currículo
- **Golden Hammer**: Usar a mesma solução para todos os problemas
- **Big Ball of Mud**: Código sem estrutura clara
- **God Object**: Classes que fazem tudo
- **Spaghetti Code**: Código difícil de seguir e entender
- **Copy-Paste Programming**: Duplicação de código
- **Magic Numbers**: Valores hardcoded sem contexto

---

## 🧭 Guia de Decisão (Evitar Over-Engineering)

Utilizar a seguinte tabela para tomar decisões pragmáticas sobre tecnologias:

| Tecnologia | Usar Quando | Evitar Quando |
|-----------|-------------|----------------|
| **Kafka** | > 1000 eventos/s, múltiplos consumidores | MVP simples, baixo volume |
| **Redis** | Leitura pesada, sessões distribuídas | Baixo tráfego, dados críticos |
| **MongoDB** | Dados flexíveis, alta escrita | Transações complexas, relacionamentos |
| **CQRS** | Leitura >> escrita, modelos diferentes | CRUD simples, baixa complexidade |
| **SAGA** | Transações distribuídas | Monólito, transações locais |
| **Event Sourcing** | Auditoria completa, reconstrução de estado | Dados simples, sem necessidade de histórico |
| **Microservices** | Times independentes, escala diferenciada | Time pequeno, domínio simples |
| **GraphQL** | Queries complexas, múltiplos clientes | APIs simples, CRUD básico |
| **Kubernetes** | Múltiplos serviços, escala dinâmica | Aplicação única, baixo tráfego |

---

## ✅ Definition of Done (DoD) Geral

Uma tarefa ou feature só será considerada concluída quando atender a **todos** os seguintes critérios:

- [ ] Código revisado e aprovado por pelo menos dois pares
- [ ] Todos os testes automatizados (unitários, integração) estão passando
- [ ] A cobertura de testes foi mantida ou aumentada (>80%)
- [ ] A documentação (README, ADRs, API docs) foi atualizada
- [ ] As métricas de performance foram validadas (dentro dos SLOs)
- [ ] A análise de segurança foi realizada (SAST, dependency scan)
- [ ] As vulnerabilidades críticas e altas foram corrigidas
- [ ] O deploy em ambiente de *staging* foi bem-sucedido
- [ ] Os logs estruturados estão sendo gerados corretamente
- [ ] As métricas estão sendo coletadas e visualizadas
- [ ] Os alertas relevantes foram configurados
- [ ] O impacto em custos foi avaliado (FinOps)

---

## 📋 Definition of Ready (DoR)

Uma tarefa só pode ser iniciada quando atender aos seguintes critérios:

- [ ] Critérios de aceitação claros e mensuráveis
- [ ] Impacto em performance analisado
- [ ] Implicações de segurança revisadas
- [ ] Estratégia de teste definida
- [ ] Dependências identificadas e disponíveis
- [ ] Estimativa de esforço realizada
- [ ] Prioridade definida

---

## 🔍 Checklist de Code Review

Utilizar o seguinte checklist em todas as revisões de código:

### Funcionalidade
- [ ] O código faz o que deveria fazer?
- [ ] Todos os casos de uso foram cobertos?
- [ ] Edge cases foram tratados?

### Qualidade
- [ ] Princípios SOLID foram aplicados?
- [ ] Código está limpo e legível?
- [ ] Nomes são claros e expressivos?
- [ ] Funções são pequenas e coesas?
- [ ] Não há duplicação de código?

### Testes
- [ ] Testes unitários foram adicionados?
- [ ] Testes de integração foram adicionados (se aplicável)?
- [ ] Cobertura de testes foi mantida ou aumentada?
- [ ] Testes estão passando?

### Segurança
- [ ] Inputs são validados e sanitizados?
- [ ] Não há segredos hardcoded?
- [ ] Autenticação e autorização estão corretas?
- [ ] Vulnerabilidades conhecidas foram evitadas?

### Performance
- [ ] Não há queries N+1?
- [ ] Cache está sendo utilizado adequadamente?
- [ ] Não há loops desnecessários?
- [ ] Complexidade algorítmica é adequada?

### Observabilidade
- [ ] Logs estruturados foram adicionados?
- [ ] Métricas relevantes estão sendo coletadas?
- [ ] Erros estão sendo tratados e logados?

### Documentação
- [ ] Código está auto-documentado?
- [ ] Comentários justificam decisões complexas?
- [ ] README foi atualizado (se necessário)?
- [ ] API docs foram atualizadas (se necessário)?

---

## 🎓 Referências e Recursos

Este prompt foi consolidado a partir das seguintes fontes de boas práticas:

1. **Implementação de Sistema E-commerce de Referência** (1812 linhas)
   - Arquitetura faseada e pragmática
   - Stack tecnológica progressiva
   - Critérios de validação detalhados

2. **Serviço Go de Alta Performance** (241 linhas)
   - Otimização para 2000 TPS
   - Observabilidade avançada
   - Padrões de resiliência

3. **Código Nota 10 - Engenharia e Arquitetura (Completo)** (234 linhas)
   - Princípios SOLID e Clean Code
   - DDD e padrões de design
   - Segurança e compliance

4. **Código Nota 10 - Engenharia e Arquitetura (Resumido)** (80 linhas)
   - Síntese dos princípios fundamentais
   - Expectativas de entregáveis

### Leituras Recomendadas

- **Clean Code** - Robert C. Martin
- **Clean Architecture** - Robert C. Martin
- **Domain-Driven Design** - Eric Evans
- **Building Microservices** - Sam Newman
- **Site Reliability Engineering** - Google
- **The Phoenix Project** - Gene Kim
- **Accelerate** - Nicole Forsgren, Jez Humble, Gene Kim

---

## 🎯 Meta Final

Este prompt servirá como a **fonte única da verdade** para todas as decisões de engenharia e arquitetura no projeto **Finops-Teste**. Qualquer desvio deve ser justificado e documentado através de um **Architecture Decision Record (ADR)**.

**Objetivo**: Obter qualidade nota 10 com suporte a evolução contínua, inspeção rigorosa e crescimento sustentável do projeto.

---

**Autor**: Manus AI  
**Data**: 25 de Novembro de 2025  
**Versão**: 1.0  
**Projeto**: Finops-Teste
