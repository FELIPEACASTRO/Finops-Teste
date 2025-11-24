# Solução de FinOps Automatizada para AWS

## 1. Visão Geral

Esta solução fornece uma estrutura automatizada para monitorar, analisar e otimizar os custos da sua conta AWS. Um job diário, executado por uma função Lambda, coleta dados de diversos serviços da AWS, gera um relatório consolidado com insights e recomendações de FinOps, e o envia por e-mail.

**Principais Funcionalidades:**

- **Análise Diária de Custos**: Acompanhe os gastos por serviço e o custo total.
- **Previsão de Custos**: Tenha uma estimativa dos custos para o próximo mês.
- **Recomendações de *Right-Sizing***: Receba sugestões do AWS Compute Optimizer para otimizar EC2, EBS, Lambda e ECS.
- **Alertas do Trusted Advisor**: Integre as verificações de otimização de custos do Trusted Advisor.
- **Identificação de Recursos Ociosos**: Encontre instâncias EC2 subutilizadas.
- **Relatórios por E-mail**: Receba um relatório diário formatado em HTML.
- **Histórico e Rastreamento**: Armazene relatórios no S3 e rastreie recomendações no DynamoDB.

---

## 2. Arquitetura

A solução é totalmente *serverless* e utiliza os seguintes serviços da AWS:

![Arquitetura da Solução de FinOps](finops_architecture.png)

- **Amazon EventBridge**: Agenda a execução diária da função Lambda.
- **AWS Lambda**: Orquestra todo o processo de coleta, análise e geração de relatórios.
- **AWS Cost Explorer**: Fornece os dados de custo e uso.
- **AWS Compute Optimizer**: Gera recomendações de otimização de recursos.
- **AWS Trusted Advisor**: Fornece verificações de melhores práticas, incluindo otimização de custos.
- **Amazon CloudWatch**: Coleta métricas de utilização dos recursos.
- **Amazon S3**: Armazena os relatórios gerados (HTML e JSON).
- **Amazon DynamoDB**: Rastreia o estado das recomendações geradas (pendente, aplicada, ignorada).
- **Amazon SES**: Envia os relatórios por e-mail.

---

## 3. Guia de Implementação

Siga os passos abaixo para implantar a solução em sua conta AWS.

### Pré-requisitos

1.  **Conta AWS**: Acesso a uma conta AWS com permissões para criar os recursos listados acima.
2.  **AWS CLI**: AWS CLI configurado em sua máquina local (opcional, para facilitar a criação de recursos).
3.  **Amazon SES Verificado**: Um endereço de e-mail ou domínio verificado no Amazon SES para enviar os relatórios.
4.  **Ativar o Compute Optimizer**: O AWS Compute Optimizer deve ser ativado na conta, pois ele pode levar até 12 horas para gerar as primeiras recomendações.

### Passo 1: Criar a Política e Role do IAM

A função Lambda precisa de permissões para acessar os outros serviços da AWS. Crie uma política do IAM (`FinOpsLambdaPolicy`) com as seguintes permissões e anexe-a a uma nova role (`FinOpsLambdaRole`).

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "ce:GetCostAndUsage",
                "ce:GetCostForecast",
                "compute-optimizer:GetEC2InstanceRecommendations",
                "compute-optimizer:GetEBSVolumeRecommendations",
                "compute-optimizer:GetLambdaFunctionRecommendations",
                "compute-optimizer:GetECSServiceRecommendations",
                "support:DescribeTrustedAdvisorChecks",
                "support:DescribeTrustedAdvisorCheckResult",
                "cloudwatch:GetMetricStatistics",
                "ec2:DescribeInstances",
                "s3:PutObject",
                "dynamodb:PutItem",
                "ses:SendEmail",
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ],
            "Resource": "*"
        }
    ]
}
```

### Passo 2: Criar o Bucket S3

Crie um bucket S3 para armazenar os relatórios. Substitua `seu-nome-de-bucket-finops` por um nome único.

```bash
aws s3 mb s3://seu-nome-de-bucket-finops
```

### Passo 3: Criar a Tabela do DynamoDB

Crie uma tabela no DynamoDB para rastrear as recomendações. A chave primária será `recommendation_id`.

```bash
aws dynamodb create-table \
    --table-name finops-recommendations \
    --attribute-definitions AttributeName=recommendation_id,AttributeType=S \
    --key-schema AttributeName=recommendation_id,KeyType=HASH \
    --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5
```

### Passo 4: Criar e Configurar a Função Lambda

1.  **Crie a Função**: No console da AWS, vá para o serviço Lambda e crie uma nova função.
    - **Nome da Função**: `finops-analyzer`
    - **Runtime**: Python 3.9 ou superior
    - **Arquitetura**: x86_64
    - **Role de Execução**: Escolha "Use an existing role" e selecione a `FinOpsLambdaRole` criada no Passo 1.

2.  **Adicione o Código**: Copie o conteúdo do arquivo `lambda_finops_analyzer.py` e cole no editor de código da função Lambda.

3.  **Configure as Variáveis de Ambiente**:
    - `S3_BUCKET_NAME`: `seu-nome-de-bucket-finops`
    - `DYNAMODB_TABLE_NAME`: `finops-recommendations`
    - `EMAIL_FROM`: Seu e-mail verificado no SES (ex: `no-reply@seudominio.com`)
    - `EMAIL_TO`: Lista de e-mails para receber o relatório, separados por vírgula (ex: `seuemail@exemplo.com,outro@exemplo.com`)

4.  **Ajuste o Timeout**: A função pode levar alguns minutos para executar. Aumente o timeout da Lambda para **5 minutos** nas configurações gerais.

### Passo 5: Criar a Regra do EventBridge

1.  Vá para o Amazon EventBridge e crie uma nova regra.
2.  **Nome**: `daily-finops-report-trigger`
3.  **Padrão de Evento**: Escolha "Schedule".
4.  **Expressão Cron**: Para executar todo dia às 8h da manhã (UTC), use `cron(0 8 * * ? *)`.
5.  **Selecione o Alvo (Target)**: Escolha "Lambda function" e selecione a função `finops-analyzer`.
6.  Ative a regra.

---

## 4. Como Usar e Personalizar

- **Execução**: A função será executada automaticamente todos os dias no horário configurado. Você também pode acioná-la manualmente no console da Lambda para testes.
- **Relatórios**: Os relatórios serão enviados para os e-mails configurados e armazenados no bucket S3.
- **Rastreamento**: As recomendações podem ser visualizadas na tabela do DynamoDB. Você pode criar uma pequena aplicação ou usar o console para atualizar o status de cada recomendação (`pending`, `implemented`, `ignored`).
- **Personalização**: O código Python na função Lambda é modular. Você pode facilmente:
    - Adicionar novas verificações (ex: procurar snapshots de EBS antigos, IPs elásticos não associados).
    - Alterar os limiares de utilização (ex: CPU média abaixo de 5% em vez de 10%).
    - Modificar o layout do relatório HTML.

---

## 5. Arquivos da Solução

- `README.md`: Este guia de implementação.
- `finops_architecture.png`: Diagrama da arquitetura.
- `finops_architecture_design.md`: Documento de design detalhado.
- `lambda_finops_analyzer.py`: O código-fonte da função Lambda.
