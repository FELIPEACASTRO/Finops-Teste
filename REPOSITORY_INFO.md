# Informações do Repositório

## 📦 Repositório GitHub

**URL**: https://github.com/FELIPEACASTRO/Finops-Teste

**Branch Principal**: main

**Descrição**: Solução automatizada de FinOps para AWS - Análise diária de custos e recomendações de otimização

## 📁 Estrutura do Repositório

```
Finops-Teste/
├── README.md                          # Documentação principal
├── EXECUTIVE_SUMMARY.md               # Resumo executivo
├── DEPLOY_GUIDE.md                    # Guia de implementação
├── LICENSE                            # Licença MIT
├── .gitignore                         # Arquivos ignorados pelo Git
├── requirements.txt                   # Dependências Python
├── lambda_finops_analyzer.py          # Código da função Lambda (500+ linhas)
├── cloudformation-template.yaml       # Template IaC para deploy
├── finops_architecture.png            # Diagrama da arquitetura
└── finops_architecture_design.md      # Documento de design detalhado
```

## 🚀 Como Usar Este Repositório

### 1. Clonar o Repositório

```bash
git clone https://github.com/FELIPEACASTRO/Finops-Teste.git
cd Finops-Teste
```

### 2. Seguir o Guia de Deploy

Leia o arquivo `DEPLOY_GUIDE.md` para instruções detalhadas de implementação.

### 3. Deploy com CloudFormation

```bash
aws cloudformation create-stack \
  --stack-name finops-automation \
  --template-body file://cloudformation-template.yaml \
  --parameters \
    ParameterKey=EmailFrom,ParameterValue=seu-email@exemplo.com \
    ParameterKey=EmailTo,ParameterValue=admin@exemplo.com \
  --capabilities CAPABILITY_NAMED_IAM
```

## 📊 Estatísticas

- **Linhas de Código Python**: 500+
- **Documentação**: 4 arquivos completos
- **Arquivos Totais**: 10
- **Licença**: MIT (uso livre)

## 🤝 Contribuições

Contribuições são bem-vindas! Sinta-se à vontade para:

1. Fazer fork do repositório
2. Criar uma branch para sua feature (`git checkout -b feature/nova-funcionalidade`)
3. Commit suas mudanças (`git commit -m 'Adiciona nova funcionalidade'`)
4. Push para a branch (`git push origin feature/nova-funcionalidade`)
5. Abrir um Pull Request

## 📝 Licença

Este projeto está licenciado sob a Licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

## 👨‍💻 Autor

**Manus AI**

## 📧 Suporte

Para dúvidas ou problemas, abra uma issue no repositório.

---

**Criado em**: 24 de Novembro de 2025
