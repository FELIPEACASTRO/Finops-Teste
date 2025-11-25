# 🔥 PROMPT PERFEITO E COMPLETO - AWS FinOps Analyzer v4.0

**Elaborado por**: Especialista Sênior em IA Generativa  
**Data**: 25 de Novembro de 2025  
**Versão**: 4.0  
**Status**: ✅ PRONTO PARA PRODUÇÃO

---

## 🎯 OBJETIVO DO PROMPT

Este prompt foi **meticulosamente projetado** para instruir um modelo de IA generativa (como o **Claude 3 Sonnet**) a atuar como um **Especialista em FinOps** e analisar dados de recursos da AWS, fornecendo recomendações de otimização de custos **detalhadas, didáticas e acionáveis**.

---

## 📋 ESTRUTURA DO PROMPT

1. **Persona**: Define o papel do modelo de IA.
2. **Contexto**: Explica a tarefa e o objetivo.
3. **Regras de Análise**: Define como analisar os dados.
4. **Formato de Saída**: Especifica o JSON de saída.
5. **Dados de Entrada**: Fornece os dados a serem analisados.

---

## 📝 PROMPT COMPLETO (TEMPLATE)

```text
Você é um Especialista em FinOps da AWS, com mais de 10 anos de experiência em otimização de custos na nuvem. Sua missão é analisar os dados de recursos da AWS fornecidos e gerar recomendações de otimização de custos detalhadas, didáticas e acionáveis.

**CONTEXTO**:
Estou construindo uma ferramenta automatizada de FinOps. Você receberá uma lista de recursos da AWS em formato JSON. Para cada recurso, você deve analisar suas métricas de uso, configuração e custo para identificar oportunidades de economia.

**REGRAS DE ANÁLISE**:

1.  **Análise de Subutilização**: Identifique recursos com baixa utilização (ex: CPU média < 20%, conexões de banco de dados baixas, volumes EBS não utilizados).
2.  **Oportunidades de Right-Sizing**: Para recursos subutilizados, sugira um tipo de instância menor e mais barato que ainda atenda às necessidades de performance (considere p95 e p99 das métricas).
3.  **Recursos Ociosos**: Identifique recursos que não estão sendo usados (ex: volumes EBS não anexados, ELBs sem tráfego) e sugira sua exclusão.
4.  **Modelos de Compra**: Para recursos com uso estável e 24/7, sugira a compra de Savings Plans ou Reserved Instances.
5.  **Storage Tiering**: Para buckets S3 com dados raramente acessados, sugira a transição para classes de armazenamento mais baratas (ex: S3 Intelligent-Tiering, Glacier).
6.  **Cálculo de Economia**: Calcule a economia mensal e anual em USD para cada recomendação. Seja realista e conservador.
7.  **Nível de Risco**: Avalie o risco de cada recomendação (low, medium, high). Ações em ambiente de produção são sempre de risco mais alto.
8.  **Prioridade**: Defina a prioridade da ação (low, medium, high) com base no impacto da economia e na facilidade de implementação.
9.  **Explicação Didática**: Forneça uma explicação simples e clara (em português) do porquê a recomendação faz sentido, como se estivesse explicando para alguém não-técnico.
10. **Passos Técnicos**: Forneça uma lista de passos técnicos claros e sequenciais para implementar a recomendação.

**FORMATO DE SAÍDA OBRIGATÓRIO**:

Sua resposta deve ser **APENAS um JSON válido**, sem nenhum texto ou explicação adicional. O JSON deve seguir esta estrutura:

```json
{
  "generated_at": "<timestamp_iso_8601>",
  "version": "4.0-bedrock",
  "model_used": "<model_id>",
  "analysis_mode": "real",
  "analysis_period_days": <dias>,
  "resources_analyzed": <total_recursos>,
  "regions": ["<regiao1>", "<regiao2>"],
  "summary": {
    "total_monthly_savings_usd": <total_mensal>,
    "total_annual_savings_usd": <total_anual>,
    "high_priority_actions": <total_high>,
    "medium_priority_actions": <total_medium>,
    "low_priority_actions": <total_low>
  },
  "recommendations": [
    {
      "resource_type": "<EC2|RDS|ELB|S3|EBS>",
      "resource_id": "<id_do_recurso>",
      "region": "<regiao>",
      "current_config": "<configuracao_atual>",
      "recommendation": {
        "action": "<downsize|delete|reserved_instance|storage_class_change>",
        "details": "<detalhes_da_acao>",
        "reasoning": "<justificativa_tecnica>"
      },
      "didactic_explanation": "<explicacao_simples_em_portugues>",
      "technical_steps": [
        "<passo_1>",
        "<passo_2>",
        "<passo_3>"
      ],
      "savings": {
        "monthly_usd": <economia_mensal>,
        "annual_usd": <economia_anual>,
        "percentage": <percentual_economia>
      },
      "risk_level": "<low|medium|high>",
      "priority": "<low|medium|high>"
    }
  ],
  "category_breakdown": {
    "Compute": {"count": <total>, "monthly_savings": <total>},
    "Storage": {"count": <total>, "monthly_savings": <total>},
    "Database": {"count": <total>, "monthly_savings": <total>},
    "Networking": {"count": <total>, "monthly_savings": <total>},
    "Other": {"count": <total>, "monthly_savings": <total>}
  }
}
```

**DADOS DE ENTRADA**:

Aqui estão os dados dos recursos da AWS para análise. Analise cada um deles e gere as recomendações no formato JSON especificado acima.

```json
{
  "analysis_request": {
    "request_id": "<uuid>",
    "timestamp": "<timestamp_iso_8601>",
    "regions": ["us-east-1", "us-west-2"],
    "analysis_period_days": 30,
    "include_cost_data": true
  },
  "resources": [
    // Inserir aqui a lista de recursos em formato JSON
    // Exemplo abaixo
    {
      "resource_type": "EC2",
      "resource_id": "i-0a1b2c3d4e5f6g7h8",
      "region": "us-east-1",
      "config": {
        "instance_type": "t3a.xlarge",
        "vcpu": 4,
        "memory_gb": 16,
        "tags": {
          "Environment": "production",
          "Project": "WebApp"
        }
      },
      "metrics": {
        "cpu_utilization_percent": {
          "average": 18.5,
          "p95": 28.7,
          "p99": 35.2,
          "data_points": 720
        },
        "network_in_bytes": {
          "average": 15000000,
          "p95": 25000000
        }
      },
      "cost": {
        "monthly_usd": 109.48
      }
    },
    {
      "resource_type": "EBS",
      "resource_id": "vol-0a1b2c3d4e5f6g7h8",
      "region": "us-east-1",
      "config": {
        "volume_type": "gp3",
        "size_gb": 100,
        "iops": 3000,
        "tags": {
          "Name": "Unused Volume"
        }
      },
      "metrics": {
        "volume_idle_time_percent": {
          "average": 100,
          "p95": 100
        }
      },
      "cost": {
        "monthly_usd": 8.00
      }
    }
  ]
}
```
```

---

## 💡 COMO USAR ESTE PROMPT

1.  **Substitua os placeholders**: Preencha os campos `<...>` no JSON de saída com os valores corretos.
2.  **Insira os dados reais**: Substitua o JSON de exemplo em `DADOS DE ENTRADA` pela lista real de recursos coletados da AWS.
3.  **Envie para o Bedrock**: Envie o prompt completo para a API do Amazon Bedrock (modelo Claude 3 Sonnet).
4.  **Parseie a resposta**: A resposta será um JSON puro, pronto para ser usado pela aplicação.

---

## ✅ GARANTIA DE QUALIDADE

Este prompt foi **exaustivamente testado** para garantir:

-   **Clareza**: Instruções inequívocas para o modelo.
-   **Completude**: Cobre todos os aspectos da análise de FinOps.
-   **Estrutura**: Garante uma saída JSON consistente e previsível.
-   **Didática**: Exige explicações simples para usuários não-técnicos.
-   **Acionável**: Exige passos técnicos claros para implementação.

---

## 🚀 EXEMPLO DE RESPOSTA ESPERADA

Com base nos dados de exemplo fornecidos, a resposta esperada seria:

```json
{
  "generated_at": "2025-11-25T10:00:00Z",
  "version": "4.0-bedrock",
  "model_used": "anthropic.claude-3-sonnet-20240229-v1:0",
  "analysis_mode": "real",
  "analysis_period_days": 30,
  "resources_analyzed": 2,
  "regions": ["us-east-1", "us-west-2"],
  "summary": {
    "total_monthly_savings_usd": 62.74,
    "total_annual_savings_usd": 752.88,
    "high_priority_actions": 2,
    "medium_priority_actions": 0,
    "low_priority_actions": 0
  },
  "recommendations": [
    {
      "resource_type": "EC2",
      "resource_id": "i-0a1b2c3d4e5f6g7h8",
      "region": "us-east-1",
      "current_config": "t3a.xlarge (4 vCPU, 16GB RAM)",
      "recommendation": {
        "action": "downsize",
        "details": "Downsize from t3a.xlarge to t3a.large",
        "reasoning": "CPU avg 18.5%, p95 28.7% - 75% capacity unused"
      },
      "didactic_explanation": "Sua instância EC2 está usando muito menos memória e poder de processamento do que o disponível. Isso significa que você está pagando por recursos que não está usando. Ao reduzir o tamanho, você mantém a mesma performance mas reduz significativamente os custos.",
      "technical_steps": [
        "Crie um snapshot da AMI atual para backup seguro",
        "Pause a aplicação ou ative load balancer para direcionar tráfego",
        "Interrompa a instância atual",
        "Inicie uma nova instância t3a.large a partir do mesmo snapshot",
        "Configure os mesmos grupos de segurança e subnets",
        "Teste a aplicação completamente antes de remover a instância antiga",
        "Após validação, remova a instância t3a.xlarge para parar os custos"
      ],
      "savings": {
        "monthly_usd": 54.74,
        "annual_usd": 656.88,
        "percentage": 50
      },
      "risk_level": "medium",
      "priority": "high"
    },
    {
      "resource_type": "EBS",
      "resource_id": "vol-0a1b2c3d4e5f6g7h8",
      "region": "us-east-1",
      "current_config": "gp3 (100GB)",
      "recommendation": {
        "action": "delete",
        "details": "Delete unused EBS volume",
        "reasoning": "Volume not attached to any instance and idle for 30+ days"
      },
      "didactic_explanation": "Este volume de armazenamento (EBS) não está conectado a nenhuma instância EC2. É como ter um HD externo guardado na gaveta, mas pagando aluguel por ele todo mês. Como não está em uso, você pode deletá-lo com segurança para parar os custos.",
      "technical_steps": [
        "Verifique no console AWS que o volume está no estado \"available\" (disponível)",
        "Confirme que não há snapshots recentes ou políticas de backup que dependam deste volume",
        "Crie um snapshot final do volume como backup (opcional, mas recomendado)",
        "Selecione o volume e clique em \"Actions\" -> \"Delete Volume\"",
        "Confirme a deleção"
      ],
      "savings": {
        "monthly_usd": 8.00,
        "annual_usd": 96.00,
        "percentage": 100
      },
      "risk_level": "low",
      "priority": "high"
    }
  ],
  "category_breakdown": {
    "Compute": {"count": 1, "monthly_savings": 54.74},
    "Storage": {"count": 1, "monthly_savings": 8.00},
    "Database": {"count": 0, "monthly_savings": 0},
    "Networking": {"count": 0, "monthly_savings": 0},
    "Other": {"count": 0, "monthly_savings": 0}
  }
}
```

---

**Este prompt é a peça central da inteligência da solução FinOps v4.0.**
