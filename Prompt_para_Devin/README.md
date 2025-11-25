# 🤖 Prompt para Devin - Finops-Teste

Esta pasta contém os arquivos necessários para que o **Devin** (AI Software Engineer) construa a plataforma **Finops-Teste** de forma autônoma.

---

## 📁 Arquivos Incluídos

### 1. `PROMPT_FOR_DEVIN.md`
**Descrição**: Este é o arquivo principal que você deve fornecer ao Devin. Ele contém:
- Missão clara e objetivos estratégicos
- Restrições e princípios não negociáveis
- Mandatos arquiteturais
- Stack tecnológica
- SLOs e métricas de qualidade
- Plano de implementação faseado
- Critérios de aceitação final

**Como usar**: Copie o conteúdo deste arquivo e cole diretamente no chat do Devin para iniciar o projeto.

### 2. `KNOWLEDGE_BASE.md`
**Descrição**: Base de conhecimento completa com todos os detalhes técnicos, exemplos de código, padrões de design, e melhores práticas. Este arquivo é uma referência para o Devin consultar durante o desenvolvimento.

**Tamanho**: 71 KB, 2.476 linhas  
**Conteúdo**: 
- Princípios SOLID, DRY, KISS, YAGNI
- Clean Architecture e DDD
- FinOps Framework 2025
- React 19 best practices
- UX/UI e acessibilidade (WCAG 2.2)
- Testing strategies
- Security (DevSecOps)
- Observability
- Performance optimization

---

## 🚀 Como Usar com Devin

1. **Inicie uma nova conversa** com o Devin.
2. **Cole o conteúdo** do arquivo `PROMPT_FOR_DEVIN.md` no chat.
3. **Adicione o contexto** do `KNOWLEDGE_BASE.md` se o Devin solicitar mais detalhes sobre algum tópico específico.
4. **Acompanhe o progresso**: O Devin reportará o progresso ao completar cada fase.
5. **Revise os entregáveis**: Código, documentação, testes, e configurações de deploy.

---

## 📊 Estrutura Esperada do Projeto

O Devin criará a seguinte estrutura de diretórios:

```
finops-teste/
├── backend/
│   ├── cmd/
│   ├── internal/
│   │   ├── domain/
│   │   ├── usecase/
│   │   ├── controller/
│   │   ├── repository/
│   │   └── infra/
│   ├── pkg/
│   ├── tests/
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── hooks/
│   │   ├── services/
│   │   └── utils/
│   ├── tests/
│   └── Dockerfile
├── docker-compose.yml
├── .github/
│   └── workflows/
│       └── ci-cd.yml
├── docs/
│   ├── ADRs/
│   └── runbooks/
└── README.md
```

---

## ✅ Critérios de Sucesso

O projeto estará completo quando:

- [ ] Aplicação funcional e testada
- [ ] Código no repositório Git
- [ ] Documentação completa (README, ADRs, API specs)
- [ ] `docker-compose up` inicia a aplicação
- [ ] Todos os testes passando (cobertura > 80%)
- [ ] SLOs atendidos (2000 TPS, P95 < 200ms)
- [ ] Checks de segurança e acessibilidade passando

---

**Autor**: Manus AI  
**Data**: 25 de novembro de 2025
