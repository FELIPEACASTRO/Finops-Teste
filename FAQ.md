# ❓ FAQ - Perguntas Frequentes

**Versão**: 3.1 FIXED  
**Data**: 24/11/2025

---

## 💰 Custos e Pricing

### Q: Quanto custa a solução?

**A**: Aproximadamente **$5-15/mês**, dependendo do uso:

| Serviço | Custo Mensal |
|:---|---:|
| Lambda | $0.10 - $0.50 |
| S3 | $0.05 - $0.20 |
| DynamoDB | $0.00 (free tier) |
| **Bedrock (Claude 3 Sonnet)** | **$5 - $10** |
| SES | $0.00 (primeiros 62k grátis) |
| **TOTAL** | **$5 - $15** |

### Q: Como reduzir custos?

**A**: 
1. Reduzir frequência (semanal em vez de diária)
2. Limitar número de recursos analisados
3. Usar modelo mais barato (Claude 3 Haiku)
4. Reduzir período de análise (7 dias em vez de 30)

---

## 🔧 Configuração

### Q: Quais regiões são suportadas?

**A**: Qualquer região AWS, mas **us-east-1** é recomendado para Bedrock.

### Q: Preciso de uma conta AWS separada?

**A**: Não, pode usar sua conta existente. Recomendamos criar uma IAM Role dedicada.

### Q: Como verificar se o Bedrock está configurado?

**A**:
```bash
aws bedrock list-foundation-models --region us-east-1
```

---

## 📧 E-mail e Relatórios

### Q: Por que não recebo e-mails?

**A**: Verifique:
1. E-mail remetente verificado no SES
2. SES fora do sandbox mode (para produção)
3. Destinatários verificados (se em sandbox)
4. Logs da Lambda para erros

### Q: Posso personalizar o relatório HTML?

**A**: Sim! Edite a função `generate_html_report()` no código.

### Q: Onde ficam salvos os relatórios?

**A**: No bucket S3 `finops-reports-{ACCOUNT_ID}` em:
- `/finops-reports/YYYY-MM-DD_HH-MM_complete_analysis.json`
- `/finops-reports/YYYY-MM-DD_HH-MM_report.html`

---

## 🤖 Bedrock e IA

### Q: Qual modelo do Bedrock é usado?

**A**: Por padrão, **Claude 3 Sonnet** (`anthropic.claude-3-sonnet-20240229-v1:0`).

### Q: Posso usar outro modelo?

**A**: Sim! Altere a variável `BEDROCK_MODEL_ID`:
- Claude 3 Haiku (mais barato): `anthropic.claude-3-haiku-20240307-v1:0`
- Claude 3 Opus (mais poderoso): `anthropic.claude-3-opus-20240229-v1:0`

### Q: O Bedrock analisa dados sensíveis?

**A**: Não. Apenas métricas (CPU, memória) e metadados (tipo de instância, tags). Nenhum dado de aplicação é enviado.

---

## 🔒 Segurança e Permissões

### Q: Quais permissões IAM são necessárias?

**A**: Veja a lista completa no CloudFormation template. Principais:
- `bedrock:InvokeModel`
- `ec2:DescribeInstances`
- `rds:DescribeDBInstances`
- `ce:GetCostAndUsage`
- `s3:PutObject`
- `ses:SendEmail`

### Q: Os dados são criptografados?

**A**: Sim! S3 usa criptografia AES256 em repouso.

### Q: Posso usar em VPC privada?

**A**: Sim, configure VPC Endpoints para Bedrock, S3 e outros serviços.

---

## 📊 Análise e Recomendações

### Q: Quais serviços AWS são analisados?

**A**: Atualmente:
- EC2 (instâncias)
- RDS (databases)
- ELB (load balancers)
- Lambda (funções)
- EBS (volumes)

### Q: Como adicionar novos serviços?

**A**: Adicione funções `collect_XXX_data()` no código seguindo o padrão existente.

### Q: As recomendações são confiáveis?

**A**: Sim, mas **sempre revise** antes de aplicar. O Bedrock analisa padrões reais, mas contexto de negócio é importante.

### Q: Posso automatizar a aplicação das recomendações?

**A**: Não recomendado por segurança. Sempre revise manualmente.

---

## ⚙️ Operação

### Q: Com que frequência devo executar?

**A**: Recomendamos **diariamente** para monitoramento contínuo. Semanal para economizar custos.

### Q: Como testar localmente?

**A**:
```bash
export AWS_REGION=us-east-1
export S3_BUCKET_NAME=finops-reports-123456789012
export BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0
python3 lambda_finops_v3_FIXED.py
```

### Q: Como atualizar o código?

**A**:
```bash
zip lambda-v3.zip lambda_finops_v3_FIXED.py
aws lambda update-function-code \
  --function-name finops-analyzer-v3 \
  --zip-file fileb://lambda-v3.zip
```

---

## 🐛 Problemas Conhecidos

### Q: Lambda dá timeout em contas grandes

**A**: Aumente o timeout ou reduza o número de recursos analisados (max_resources).

### Q: Bedrock retorna JSON inválido

**A**: Raro, mas pode acontecer. O código tenta limpar automaticamente. Se persistir, ajuste o prompt.

### Q: Custo do Bedrock muito alto

**A**: Reduza `max_resources` ou use Claude 3 Haiku.

---

## 📚 Recursos Adicionais

### Q: Onde encontro mais documentação?

**A**:
- README.md - Visão geral
- BEDROCK_SETUP_GUIDE.md - Configuração Bedrock
- TROUBLESHOOTING.md - Solução de problemas
- DEPLOY_GUIDE.md - Guia de deploy

### Q: Como contribuir?

**A**: Abra Pull Requests no GitHub! Toda contribuição é bem-vinda.

### Q: Há suporte comercial?

**A**: Não oficialmente, mas a comunidade é ativa no GitHub.

---

**Não encontrou sua pergunta? Abra uma issue no GitHub!** 🚀
