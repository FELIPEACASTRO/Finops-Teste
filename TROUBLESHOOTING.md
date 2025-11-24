# 🔧 Guia de Troubleshooting - FinOps Analyzer v3.1

**Versão**: 3.1 FIXED  
**Data**: 24/11/2025

---

## 🚨 Problemas Comuns e Soluções

### 1. Lambda Retorna Erro 500

#### Sintomas:
- StatusCode: 500
- Mensagem: "Internal Server Error"

#### Causas Possíveis:
- Permissões IAM insuficientes
- Bedrock não configurado
- Variáveis de ambiente faltando

#### Solução:

```bash
# 1. Verificar logs
aws logs tail /aws/lambda/finops-analyzer-v3 --follow

# 2. Verificar variáveis de ambiente
aws lambda get-function-configuration \
  --function-name finops-analyzer-v3 \
  --query 'Environment.Variables'

# 3. Verificar permissões IAM
aws iam get-role-policy \
  --role-name FinOpsLambdaRole \
  --policy-name FinOpsLambdaPolicy
```

---

### 2. Bedrock Access Denied

#### Sintomas:
- Erro: "AccessDeniedException"
- Mensagem: "User is not authorized to perform: bedrock:InvokeModel"

#### Causas:
- Modelo Claude 3 não aprovado
- Permissões IAM faltando
- Região incorreta

#### Solução:

```bash
# 1. Verificar acesso ao modelo
aws bedrock list-foundation-models \
  --region us-east-1 \
  --query "modelSummaries[?contains(modelId, 'claude-3-sonnet')]"

# 2. Solicitar acesso (se necessário)
# Via console: Bedrock > Model access > Request access

# 3. Adicionar permissão IAM
aws iam put-role-policy \
  --role-name FinOpsLambdaRole \
  --policy-name BedrockAccess \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Action": ["bedrock:InvokeModel"],
      "Resource": "*"
    }]
  }'
```

---

### 3. E-mail Não Enviado

#### Sintomas:
- Lambda executa com sucesso
- Relatório salvo no S3
- E-mail não chega

#### Causas:
- E-mail remetente não verificado no SES
- SES em sandbox mode
- Destinatários não verificados

#### Solução:

```bash
# 1. Verificar e-mail verificado
aws ses list-verified-email-addresses

# 2. Verificar novo e-mail
aws ses verify-email-identity \
  --email-address seu-email@exemplo.com

# 3. Sair do sandbox (produção)
# Via console: SES > Account dashboard > Request production access

# 4. Verificar logs de envio
aws logs filter-log-events \
  --log-group-name /aws/lambda/finops-analyzer-v3 \
  --filter-pattern "E-mail"
```

---

### 4. Lambda Timeout

#### Sintomas:
- Erro: "Task timed out after 600.00 seconds"
- Execução interrompida

#### Causas:
- Muitos recursos para analisar
- Bedrock lento
- Timeout muito baixo

#### Solução:

```bash
# 1. Aumentar timeout
aws lambda update-function-configuration \
  --function-name finops-analyzer-v3 \
  --timeout 900  # 15 minutos

# 2. Reduzir período de análise
aws lambda update-function-configuration \
  --function-name finops-analyzer-v3 \
  --environment Variables="{HISTORICAL_DAYS=7}"

# 3. Verificar tempo de execução
aws logs filter-log-events \
  --log-group-name /aws/lambda/finops-analyzer-v3 \
  --filter-pattern "Duration"
```

---

### 5. Custo Muito Alto

#### Sintomas:
- Fatura AWS elevada
- Bedrock cobrando muito

#### Causas:
- Muitas execuções
- Prompt muito grande
- Tokens excessivos

#### Solução:

```bash
# 1. Verificar número de invocações
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Invocations \
  --dimensions Name=FunctionName,Value=finops-analyzer-v3 \
  --start-time 2025-11-01T00:00:00Z \
  --end-time 2025-11-30T23:59:59Z \
  --period 86400 \
  --statistics Sum

# 2. Reduzir frequência
aws events put-rule \
  --name daily-finops-report-trigger \
  --schedule-expression "cron(0 8 ? * MON *)"  # Apenas segundas

# 3. Limitar recursos analisados
# Editar código: max_resources = 20 (linha 485)
```

---

### 6. Relatório Vazio

#### Sintomas:
- Lambda executa
- Relatório JSON vazio ou com poucos dados

#### Causas:
- Sem recursos na conta
- Filtros muito restritivos
- Região errada

#### Solução:

```bash
# 1. Verificar recursos manualmente
aws ec2 describe-instances --region us-east-1
aws rds describe-db-instances --region us-east-1

# 2. Verificar região da Lambda
aws lambda get-function-configuration \
  --function-name finops-analyzer-v3 \
  --query 'Environment.Variables.AWS_REGION'

# 3. Ver logs de coleta
aws logs filter-log-events \
  --log-group-name /aws/lambda/finops-analyzer-v3 \
  --filter-pattern "coletadas"
```

---

## 📊 Comandos Úteis de Debug

### Ver Logs em Tempo Real:

```bash
aws logs tail /aws/lambda/finops-analyzer-v3 --follow
```

### Buscar Erros:

```bash
aws logs filter-log-events \
  --log-group-name /aws/lambda/finops-analyzer-v3 \
  --filter-pattern "ERROR"
```

### Invocar Manualmente:

```bash
aws lambda invoke \
  --function-name finops-analyzer-v3 \
  --log-type Tail \
  --query 'LogResult' \
  --output text \
  output.json | base64 -d
```

### Verificar Dead Letter Queue:

```bash
aws sqs receive-message \
  --queue-url https://sqs.us-east-1.amazonaws.com/ACCOUNT_ID/finops-analyzer-dlq
```

---

## 🆘 Suporte

Se o problema persistir:

1. **Verifique os logs** completos
2. **Colete informações**:
   - Mensagem de erro exata
   - Logs do CloudWatch
   - Configuração da Lambda
3. **Abra uma issue** no GitHub
4. **Contate o suporte** AWS se necessário

---

**Boa sorte! 🍀**
