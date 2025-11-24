# Guia de Deploy - Solução de FinOps Automatizada

Este guia fornece instruções passo a passo para implantar a solução de FinOps em sua conta AWS usando CloudFormation ou manualmente.

---

## Opção 1: Deploy Automatizado com CloudFormation (Recomendado)

### Pré-requisitos

1. **Conta AWS** com permissões de administrador
2. **Amazon SES** configurado com um e-mail ou domínio verificado
3. **AWS Compute Optimizer** ativado na conta (pode levar até 12 horas para gerar recomendações)
4. **AWS CLI** instalado e configurado (opcional)

### Passos

#### 1. Preparar o Código da Lambda

Antes de fazer o deploy, você precisa empacotar o código da função Lambda:

```bash
# Criar diretório temporário
mkdir lambda-package
cd lambda-package

# Copiar o código da função
cp ../lambda_finops_analyzer.py index.py

# Criar arquivo ZIP
zip -r ../lambda-function.zip .
cd ..
```

#### 2. Fazer Upload do Código para S3 (Temporário)

```bash
# Criar bucket temporário para o código (substitua pelo nome único)
aws s3 mb s3://seu-bucket-temporario-lambda-code

# Fazer upload do código
aws s3 cp lambda-function.zip s3://seu-bucket-temporario-lambda-code/
```

#### 3. Criar a Stack do CloudFormation

**Usando AWS CLI:**

```bash
aws cloudformation create-stack \
  --stack-name finops-automation \
  --template-body file://cloudformation-template.yaml \
  --parameters \
    ParameterKey=EmailFrom,ParameterValue=no-reply@seudominio.com \
    ParameterKey=EmailTo,ParameterValue=admin@seudominio.com \
    ParameterKey=CronSchedule,ParameterValue="cron(0 8 * * ? *)" \
  --capabilities CAPABILITY_NAMED_IAM
```

**Usando Console AWS:**

1. Acesse o serviço **CloudFormation** no console AWS
2. Clique em **Create stack** > **With new resources**
3. Escolha **Upload a template file** e faça upload do `cloudformation-template.yaml`
4. Preencha os parâmetros:
   - **EmailFrom**: Seu e-mail verificado no SES
   - **EmailTo**: Lista de e-mails para receber relatórios
   - **CronSchedule**: Horário de execução (padrão: 8h UTC)
5. Marque a opção **I acknowledge that AWS CloudFormation might create IAM resources**
6. Clique em **Create stack**

#### 4. Atualizar o Código da Função Lambda

Após a criação da stack, você precisa atualizar o código da função Lambda:

```bash
# Obter o nome da função criada
FUNCTION_NAME=$(aws cloudformation describe-stacks \
  --stack-name finops-automation \
  --query 'Stacks[0].Outputs[?OutputKey==`LambdaFunctionName`].OutputValue' \
  --output text)

# Atualizar o código da função
aws lambda update-function-code \
  --function-name $FUNCTION_NAME \
  --zip-file fileb://lambda-function.zip
```

#### 5. Testar a Função

```bash
# Invocar a função manualmente para teste
aws lambda invoke \
  --function-name $FUNCTION_NAME \
  --invocation-type RequestResponse \
  --log-type Tail \
  response.json

# Ver o resultado
cat response.json
```

---

## Opção 2: Deploy Manual

Se preferir criar os recursos manualmente, siga os passos detalhados no arquivo `README.md`.

---

## Verificações Pós-Deploy

### 1. Verificar o Amazon SES

Certifique-se de que o endereço de e-mail configurado está verificado no Amazon SES:

```bash
aws ses list-verified-email-addresses
```

Se não estiver verificado:

```bash
aws ses verify-email-identity --email-address seu-email@exemplo.com
```

### 2. Ativar o AWS Compute Optimizer

O Compute Optimizer precisa estar ativado para gerar recomendações:

```bash
aws compute-optimizer get-enrollment-status
```

Se não estiver ativado:

```bash
aws compute-optimizer update-enrollment-status --status Active
```

### 3. Verificar Permissões do Trusted Advisor

Para usar a API do Trusted Advisor, você precisa de um plano de suporte **Business** ou **Enterprise**. Se você tiver apenas o plano básico, a função ainda funcionará, mas não incluirá as verificações do Trusted Advisor.

### 4. Testar o Envio de E-mail

Execute a função Lambda manualmente e verifique se o e-mail foi recebido:

```bash
aws lambda invoke \
  --function-name finops-analyzer \
  --invocation-type RequestResponse \
  response.json
```

---

## Monitoramento e Logs

### Visualizar Logs da Lambda

```bash
# Listar grupos de logs
aws logs describe-log-groups --log-group-name-prefix /aws/lambda/finops-analyzer

# Ver os logs mais recentes
aws logs tail /aws/lambda/finops-analyzer --follow
```

### Verificar Relatórios no S3

```bash
# Listar relatórios gerados
aws s3 ls s3://finops-reports-$(aws sts get-caller-identity --query Account --output text)/reports/
```

### Consultar Recomendações no DynamoDB

```bash
# Escanear a tabela (primeiros 10 itens)
aws dynamodb scan \
  --table-name finops-recommendations \
  --max-items 10
```

---

## Personalização

### Alterar o Horário de Execução

Para alterar o horário de execução diária, modifique a expressão cron na regra do EventBridge:

```bash
aws events put-rule \
  --name daily-finops-report-trigger \
  --schedule-expression "cron(0 10 * * ? *)"  # 10h UTC
```

### Adicionar Mais Destinatários de E-mail

Atualize a variável de ambiente `EMAIL_TO` na função Lambda:

```bash
aws lambda update-function-configuration \
  --function-name finops-analyzer \
  --environment "Variables={S3_BUCKET_NAME=finops-reports-123456789012,DYNAMODB_TABLE_NAME=finops-recommendations,EMAIL_FROM=no-reply@exemplo.com,EMAIL_TO=admin1@exemplo.com,admin2@exemplo.com}"
```

---

## Custos Estimados

A solução é altamente econômica e opera dentro do nível gratuito da AWS para a maioria dos casos de uso:

| Serviço | Custo Estimado |
|---------|----------------|
| Lambda (1 execução/dia, 2 min) | ~$0.01/mês |
| S3 (90 dias de histórico) | ~$0.05/mês |
| DynamoDB (On-Demand) | ~$0.01/mês |
| SES (100 e-mails/mês) | Gratuito |
| EventBridge | Gratuito |
| **Total Estimado** | **~$0.10/mês** |

---

## Troubleshooting

### Erro: "AccessDeniedException" ao chamar APIs

**Causa**: A role da Lambda não tem as permissões necessárias.

**Solução**: Verifique se a política IAM inclui todas as permissões listadas no `README.md`.

### Erro: "MessageRejected" ao enviar e-mail

**Causa**: O endereço de e-mail não está verificado no SES ou a conta está em sandbox.

**Solução**: 
1. Verifique o e-mail no SES
2. Se estiver em sandbox, solicite a saída do sandbox no console do SES

### Nenhuma recomendação do Compute Optimizer

**Causa**: O Compute Optimizer precisa de pelo menos 12 horas de dados.

**Solução**: Aguarde e execute novamente após 24 horas.

### Erro: "ResourceNotFoundException" para Trusted Advisor

**Causa**: Você não tem um plano de suporte Business ou Enterprise.

**Solução**: Comente ou remova a chamada para `get_trusted_advisor_checks()` no código da Lambda.

---

## Desinstalação

Para remover completamente a solução:

### Usando CloudFormation:

```bash
# Esvaziar o bucket S3 primeiro
aws s3 rm s3://finops-reports-$(aws sts get-caller-identity --query Account --output text) --recursive

# Deletar a stack
aws cloudformation delete-stack --stack-name finops-automation
```

### Manual:

1. Deletar a regra do EventBridge
2. Deletar a função Lambda
3. Esvaziar e deletar o bucket S3
4. Deletar a tabela do DynamoDB
5. Deletar a role e política do IAM

---

## Suporte e Contribuições

Para dúvidas, sugestões ou melhorias, abra uma issue ou contribua com o projeto.

**Desenvolvido por**: Manus AI  
**Versão**: 1.0  
**Data**: Novembro 2025
