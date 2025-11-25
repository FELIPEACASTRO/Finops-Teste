# 🚀 Prompt para Replit - Finops-Teste

Esta pasta contém os arquivos necessários para construir a plataforma **Finops-Teste** usando o **Replit** (Cloud IDE com AI).

---

## 📁 Arquivos Incluídos

### 1. `PROMPT_FOR_REPLIT.md`
**Descrição**: Arquivo principal com instruções específicas para o ambiente Replit. Contém:
- Objetivos do projeto
- Setup do ambiente Replit
- Stack tecnológica adaptada para Replit
- Plano de desenvolvimento faseado
- Instruções para usar a AI do Replit
- Tarefas chave

**Como usar**: Use este arquivo como guia para desenvolver o projeto no Replit, aproveitando a AI integrada.

### 2. `KNOWLEDGE_BASE.md`
**Descrição**: Base de conhecimento completa com todos os detalhes técnicos, exemplos de código, e melhores práticas.

**Tamanho**: 71 KB, 2.476 linhas

---

## 🚀 Como Usar com Replit

### Passo 1: Criar o Workspace

1. Acesse [Replit](https://replit.com)
2. Clique em **"+ Create Repl"**
3. Selecione o template **"React + Node.js"**
4. Nomeie o projeto como **"finops-teste"**

### Passo 2: Configurar o Banco de Dados

1. No painel lateral, clique em **"Database"**
2. Selecione **"PostgreSQL"**
3. Anote as credenciais (serão automaticamente adicionadas aos Secrets)

### Passo 3: Configurar Secrets

1. No painel lateral, clique em **"Secrets"**
2. Adicione as seguintes variáveis:
   - `DATABASE_URL`: URL de conexão do PostgreSQL
   - `JWT_SECRET`: Chave secreta para JWT
   - `PORT`: 3000

### Passo 4: Desenvolver com AI

1. Abra o arquivo `PROMPT_FOR_REPLIT.md`
2. Use a **AI do Replit** para:
   - Gerar código boilerplate
   - Criar componentes React
   - Implementar serviços backend
   - Escrever testes
   - Debugar erros

**Dica**: Pressione `Ctrl+K` (ou `Cmd+K` no Mac) para abrir o chat da AI.

### Passo 5: Executar o Projeto

1. Configure o arquivo `package.json` com os scripts necessários
2. Clique em **"Run"** no topo da página
3. A aplicação será executada e um preview será aberto

### Passo 6: Deploy

1. Clique em **"Deploy"** no painel lateral
2. Configure o deployment (Replit Autoscale ou Static)
3. Publique a aplicação

---

## 📊 Estrutura do Projeto no Replit

```
finops-teste/
├── backend/
│   ├── src/
│   │   ├── modules/
│   │   ├── common/
│   │   └── main.ts
│   └── test/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   └── App.tsx
│   └── tests/
├── package.json
├── replit.nix
└── README.md
```

---

## ✅ Critérios de Sucesso

O projeto estará completo quando:

- [ ] Aplicação funcional no Replit
- [ ] Database configurado e conectado
- [ ] Frontend e backend comunicando
- [ ] Testes escritos e passando
- [ ] README.md detalhado criado
- [ ] Projeto deployado no Replit

---

**Autor**: Manus AI  
**Data**: 25 de novembro de 2025
