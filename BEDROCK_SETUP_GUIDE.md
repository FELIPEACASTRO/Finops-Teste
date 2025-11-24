# 🤖 Guia Completo de Configuração do Amazon Bedrock

**Versão**: 3.1 FIXED  
**Data**: 24/11/2025

---

## 📋 Pré-requisitos

- Conta AWS ativa
- Permissões de administrador (ou IAM com bedrock:*)
- AWS CLI configurado
- Região suportada pelo Bedrock

---

## 🌍 Regiões Suportadas

O Amazon Bedrock está disponível nas seguintes regiões:

- **us-east-1** (N. Virginia) ✅ Recomendado
- **us-west-2** (Oregon)
- **eu-west-1** (Ireland)
- **eu-central-1** (Frankfurt)
- **ap-southeast-1** (Singapore)
- **ap-northeast-1** (Tokyo)

---

## 🚀 Passo 1: Habilitar Amazon Bedrock

### Via Console AWS:

1. Acesse o **Console AWS**
2. Navegue para **Amazon Bedrock**
3. Clique em **Get Started**
4. Aceite os termos de serviço

### Via AWS CLI:

```bash
# Verificar se Bedrock está disponível
aws bedrock list-foundation-models --region us-east-1
```

---

## 🔑 Passo 2: Solicitar Acesso ao Claude 3 Sonnet

### Via Console AWS:

1. No console do Bedrock, vá para **Model access**
2. Clique em **Manage model access**
3. Encontre **Anthropic Claude 3 Sonnet**
4. Marque a caixa de seleção
5. Clique em **Request model access**
6. Preencha o formulário (geralmente aprovado instantaneamente)
7. Aguarde aprovação (pode levar alguns minutos)

### Verificar Status:

```bash
# Listar modelos disponíveis
aws bedrock list-foundation-models \
  --region us-east-1 \
  --query "modelSummaries[?contains(modelId, 'claude-3-sonnet')]"
```

---

## ✅ Passo 3: Testar Acesso

### Teste via AWS CLI:

```bash
# Criar arquivo de teste
cat > test-bedrock.json << 'EOFJSON'
{
  "anthropic_version": "bedrock-2023-05-31",
  "max_tokens": 100,
  "messages": [
    {
      "role": "user",
      "content": "Olá! Você está funcionando?"
    }
  ]
}
EOFJSON

# Invocar modelo
aws bedrock-runtime invoke-model \
  --region us-east-1 \
  --model-id anthropic.claude-3-sonnet-20240229-v1:0 \
  --body file://test-bedrock.json \
  output.json

# Ver resposta
cat output.json | jq -r '.content[0].text'
```

### Teste via Python:

```python
import boto3
import json

bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')

request_body = {
    "anthropic_version": "bedrock-2023-05-31",
    "max_tokens": 100,
    "messages": [{"role": "user", "content": "Olá! Você está funcionando?"}]
}

response = bedrock.invoke_model(
    modelId='anthropic.claude-3-sonnet-20240229-v1:0',
    body=json.dumps(request_body)
)

result = json.loads(response['body'].read())
print(result['content'][0]['text'])
```

---

## 💰 Passo 4: Configurar Quotas (Opcional)

### Via Console:

1. No Bedrock, vá para **Model access**
2. Clique em **Service quotas**
3. Ajuste os limites conforme necessário

### Quotas Padrão:

- **Requests per minute**: 1000
- **Tokens per minute**: 100,000
- **Max concurrent requests**: 100

---

## 🔒 Passo 5: Configurar Permissões IAM

### Política Mínima:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:ListFoundationModels"
      ],
      "Resource": "*"
    }
  ]
}
```

### Aplicar à Role da Lambda:

```bash
aws iam put-role-policy \
  --role-name FinOpsLambdaRole \
  --policy-name BedrockAccess \
  --policy-document file://bedrock-policy.json
```

---

## 🧪 Passo 6: Testar com a Solução FinOps

### Configurar Variável de Ambiente:

```bash
aws lambda update-function-configuration \
  --function-name finops-analyzer-v3 \
  --environment Variables="{
    BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0,
    AWS_REGION=us-east-1
  }"
```

### Invocar Lambda de Teste:

```bash
aws lambda invoke \
  --function-name finops-analyzer-v3 \
  --payload '{}' \
  output.json

cat output.json | jq
```

---

## ⚠️ Troubleshooting

### Erro: "Access Denied"

**Causa**: Modelo não aprovado ou permissões insuficientes

**Solução**:
1. Verificar status de aprovação no console
2. Verificar permissões IAM da Lambda
3. Aguardar alguns minutos após aprovação

### Erro: "Throttling"

**Causa**: Excedeu quotas de requests/tokens

**Solução**:
1. Verificar quotas no console
2. Solicitar aumento de quota
3. Implementar retry com backoff exponencial

### Erro: "Model not found"

**Causa**: Região incorreta ou modelo ID errado

**Solução**:
1. Verificar região (us-east-1 recomendado)
2. Verificar MODEL_ID correto
3. Listar modelos disponíveis

---

## 📊 Monitoramento

### CloudWatch Metrics:

- **Invocations** - Número de chamadas
- **ModelInvocationLatency** - Latência
- **ClientErrors** - Erros do cliente
- **ServerErrors** - Erros do servidor

### Logs:

```bash
# Ver logs da Lambda
aws logs tail /aws/lambda/finops-analyzer-v3 --follow
```

---

## 💡 Dicas

1. **Use us-east-1** - Melhor disponibilidade
2. **Monitore custos** - Bedrock cobra por token
3. **Implemente cache** - Evite chamadas duplicadas
4. **Use timeout adequado** - 90s recomendado
5. **Teste localmente** - Antes de deploy

---

## 📚 Recursos Adicionais

- [Documentação Bedrock](https://docs.aws.amazon.com/bedrock/)
- [Preços Bedrock](https://aws.amazon.com/bedrock/pricing/)
- [Claude 3 Docs](https://docs.anthropic.com/claude/docs)

---

**Configuração completa! Sua solução FinOps está pronta para usar o Bedrock!** 🎉
