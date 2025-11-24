# Arquitetura da Solução de FinOps Automatizada para AWS

## 1. Visão Geral

Esta solução foi projetada para automatizar a análise de custos e a geração de recomendações de FinOps para uma conta AWS. O sistema executará diariamente, coletará dados de várias fontes da AWS, analisará esses dados em busca de oportunidades de otimização e enviará um relatório consolidado por e-mail.

## 2. Diagrama da Arquitetura

O diagrama a seguir ilustra o fluxo de trabalho da solução:

![Arquitetura da Solução de FinOps](finops_architecture.png)

## 3. Componentes da Arquitetura

| Componente | Descrição |
|---|---|
| **EventBridge Rule** | Um agendador (cron job) que aciona a função Lambda diariamente. |
| **Lambda Function** | O núcleo da solução, escrito em Python com Boto3. Orquestra a coleta e análise de dados. |
| **Cost Explorer API** | Fornece dados detalhados sobre custos e uso dos serviços AWS. |
| **Compute Optimizer API** | Gera recomendações de *right-sizing* para instâncias EC2, volumes EBS, funções Lambda e serviços ECS. |
| **Trusted Advisor API** | Oferece uma visão holística da conta, incluindo verificações de otimização de custos. |
| **CloudWatch API** | Coleta métricas de utilização de recursos, como CPU, memória e I/O de disco. |
| **S3 Bucket** | Armazena relatórios históricos para análise de tendências e auditoria. |
| **DynamoDB Table** | Mantém o estado das recomendações, permitindo o rastreamento de quais foram aplicadas e quais estão pendentes. |
| **Amazon SES** | Serviço de envio de e-mail usado para distribuir o relatório de FinOps. |

## 4. Fluxo de Trabalho Detalhado

1.  **Agendamento**: A regra do EventBridge é acionada no horário definido (diariamente).
2.  **Execução da Lambda**: A função Lambda é invocada.
3.  **Coleta de Dados**:
    *   A Lambda chama a **API do Cost Explorer** para obter os custos do último dia e do mês atual, detalhados por serviço.
    *   A Lambda chama a **API do Compute Optimizer** para obter recomendações de otimização de recursos.
    *   A Lambda chama a **API do Trusted Advisor** para obter as últimas verificações de otimização de custos.
    *   A Lambda utiliza a **API do CloudWatch** para coletar métricas de utilização de recursos chave (ex: EC2 com baixa utilização).
4.  **Análise e Geração de Recomendações**:
    *   O código da Lambda processa os dados coletados.
    *   Identifica instâncias EC2 subutilizadas, volumes EBS ociosos, snapshots antigos, etc.
    *   Compara as recomendações do Compute Optimizer com os dados de custo para priorizar as ações com maior impacto financeiro.
    *   Gera um conjunto de dicas de FinOps acionáveis.
5.  **Geração e Envio do Relatório**:
    *   A Lambda formata os resultados em um relatório HTML/Markdown claro e conciso.
    *   O relatório é enviado para uma lista de destinatários via **Amazon SES**.
    *   Uma cópia do relatório é salva no **bucket S3** para arquivamento.
6.  **Atualização de Estado**: As novas recomendações são salvas na tabela do **DynamoDB** para rastreamento.
