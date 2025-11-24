"""
Serviço de Análise com Amazon Bedrock.
Implementa análise inteligente usando Claude 3 Sonnet.
"""

import json
import logging
from typing import List, Dict, Any
from decimal import Decimal
import asyncio

from ...domain.services.servico_analise import IServicoAnaliseIA
from ...domain.entities.recurso import (
    RecursoAWS, RecomendacaoOtimizacao, DadosCusto,
    TipoRecurso, Prioridade, NivelRisco, PadraoUso
)
from ..aws.cliente_aws import ClienteAWSSingleton, retry_aws_call, medir_tempo_execucao

logger = logging.getLogger(__name__)


class ServicoBedrock(IServicoAnaliseIA):
    """
    Implementação do serviço de análise usando Amazon Bedrock.
    
    Utiliza Claude 3 Sonnet para análise inteligente de recursos AWS.
    Implementa padrão Strategy para diferentes tipos de análise.
    """
    
    def __init__(
        self, 
        modelo_id: str = "anthropic.claude-3-sonnet-20240229-v1:0",
        regiao: str = "us-east-1",
        max_recursos_por_analise: int = 50
    ):
        """
        Inicializa o serviço Bedrock.
        
        Args:
            modelo_id: ID do modelo Bedrock
            regiao: Região AWS
            max_recursos_por_analise: Máximo de recursos por análise
        """
        self.modelo_id = modelo_id
        self.regiao = regiao
        self.max_recursos_por_analise = max_recursos_por_analise
        self.cliente_aws = ClienteAWSSingleton(regiao)
        logger.info(f"Serviço Bedrock inicializado com modelo: {modelo_id}")
    
    @retry_aws_call(max_tentativas=2)
    @medir_tempo_execucao
    async def analisar_recursos(
        self, 
        recursos: List[RecursoAWS], 
        dados_custo: DadosCusto
    ) -> List[RecomendacaoOtimizacao]:
        """
        Analisa recursos usando Amazon Bedrock.
        
        Args:
            recursos: Lista de recursos para análise
            dados_custo: Dados de custo dos recursos
            
        Returns:
            Lista de recomendações de otimização
        """
        logger.info(f"Iniciando análise de {len(recursos)} recursos com Bedrock")
        
        # Dividir recursos em lotes para não exceder limite de tokens
        lotes_recursos = self._dividir_em_lotes(recursos, self.max_recursos_por_analise)
        todas_recomendacoes = []
        
        for i, lote in enumerate(lotes_recursos):
            logger.info(f"Analisando lote {i+1}/{len(lotes_recursos)} ({len(lote)} recursos)")
            
            try:
                recomendacoes_lote = await self._analisar_lote_recursos(lote, dados_custo)
                todas_recomendacoes.extend(recomendacoes_lote)
                
                # Pequeno delay entre lotes para evitar throttling
                if i < len(lotes_recursos) - 1:
                    await asyncio.sleep(1)
                    
            except Exception as e:
                logger.error(f"Erro ao analisar lote {i+1}: {e}")
                continue
        
        logger.info(f"✓ Análise concluída: {len(todas_recomendacoes)} recomendações geradas")
        return todas_recomendacoes
    
    async def _analisar_lote_recursos(
        self, 
        recursos: List[RecursoAWS], 
        dados_custo: DadosCusto
    ) -> List[RecomendacaoOtimizacao]:
        """Analisa um lote de recursos."""
        prompt = self._construir_prompt_analise(recursos, dados_custo)
        
        try:
            resposta_ia = await self._chamar_bedrock(prompt)
            recomendacoes = self._processar_resposta_bedrock(resposta_ia)
            
            return recomendacoes
            
        except Exception as e:
            logger.error(f"Erro na análise do lote: {e}")
            return []
    
    def _construir_prompt_analise(
        self, 
        recursos: List[RecursoAWS], 
        dados_custo: DadosCusto
    ) -> str:
        """
        Constrói prompt otimizado para análise de FinOps.
        
        O prompt é estruturado para maximizar a qualidade das recomendações.
        """
        prompt = f"""Você é um especialista SÊNIOR em FinOps da AWS com 15 anos de experiência. 

Analise PROFUNDAMENTE os recursos AWS abaixo e forneça recomendações PRECISAS e ACIONÁVEIS para otimização de custos.

## CONTEXTO DE CUSTOS

Custo total (últimos {dados_custo.periodo_dias} dias): ${dados_custo.custo_total_usd:.2f} USD
Custo médio diário: ${dados_custo.calcular_custo_medio_diario():.2f} USD

Principais serviços por custo:
"""
        
        for servico in dados_custo.obter_principais_servicos(5):
            prompt += f"- {servico['servico']}: ${servico['custo_usd']:.2f} ({servico['percentual']:.1f}%)\n"
        
        prompt += f"\n## RECURSOS PARA ANÁLISE ({len(recursos)} recursos)\n\n"
        
        for i, recurso in enumerate(recursos):
            prompt += f"### Recurso #{i+1}: {recurso.tipo_recurso.value} - {recurso.id_recurso}\n"
            
            # Informações básicas
            prompt += f"**Configuração:** {json.dumps(recurso.configuracao, indent=2)}\n"
            prompt += f"**Tags:** {json.dumps(recurso.tags, indent=2)}\n"
            prompt += f"**Região:** {recurso.regiao}\n"
            prompt += f"**Produção:** {'Sim' if recurso.eh_producao() else 'Não'}\n"
            prompt += f"**Criticidade:** {recurso.obter_criticidade()}\n"
            
            # Métricas de performance
            if recurso.metricas.utilizacao_cpu:
                stats_cpu = recurso.metricas.obter_estatisticas_cpu()
                prompt += f"**CPU:** Média: {stats_cpu['media']:.1f}%, P95: {stats_cpu['p95']:.1f}%, Máximo: {stats_cpu['maximo']:.1f}%\n"
            
            if recurso.metricas.utilizacao_memoria:
                stats_mem = recurso.metricas.obter_estatisticas_memoria()
                prompt += f"**Memória:** Média: {stats_mem['media']:.1f}%, P95: {stats_mem['p95']:.1f}%, Máximo: {stats_mem['maximo']:.1f}%\n"
            
            prompt += f"**Score Utilização:** {recurso.calcular_score_utilizacao():.1f}%\n\n"
        
        prompt += """
## SUA TAREFA

Para CADA recurso, analise e forneça:

1. **Padrão de uso** (constante/variavel/lote/ocioso)
2. **Estatísticas de utilização** (média, p95, desperdício %)
3. **Recomendação específica** (downsize/upsize/delete/optimize/no_change)
4. **Justificativa técnica detalhada**
5. **Economia estimada** (USD/mês e /ano)
6. **Nível de risco** (baixo/medio/alto)
7. **Prioridade** (alta/media/baixa)
8. **Passos de implementação**

## CRITÉRIOS DE ANÁLISE

- **Recursos com CPU < 20% (P95)**: Candidatos a downsize
- **Recursos com CPU > 80% (P95)**: Candidatos a upsize
- **Recursos ociosos (CPU < 5%)**: Candidatos a deleção
- **Recursos de produção**: Risco aumentado
- **Recursos críticos**: Prioridade aumentada

## FORMATO DE RESPOSTA (JSON ESTRITO)

```json
{
  "resumo": {
    "total_recursos_analisados": {len(recursos)},
    "economia_mensal_total_usd": 0.00,
    "economia_anual_total_usd": 0.00,
    "acoes_alta_prioridade": 0,
    "acoes_media_prioridade": 0,
    "acoes_baixa_prioridade": 0
  },
  "recomendacoes": [
    {
      "id_recurso": "string",
      "tipo_recurso": "EC2|RDS|ELB|Lambda|EBS|S3|DynamoDB|ElastiCache",
      "configuracao_atual": "string descritiva",
      "analise": {
        "padrao_uso": "constante|variavel|lote|ocioso",
        "cpu_media": 0.0,
        "cpu_p95": 0.0,
        "percentual_desperdicio": 0.0,
        "score_confianca": 0.0
      },
      "recomendacao": {
        "acao": "downsize|upsize|delete|optimize|no_change",
        "detalhes": "string específica",
        "justificativa": "string técnica detalhada"
      },
      "economia": {
        "mensal_usd": 0.00,
        "anual_usd": 0.00,
        "percentual": 0.0
      },
      "nivel_risco": "baixo|medio|alto",
      "prioridade": "alta|media|baixa",
      "passos_implementacao": [
        "string passo 1",
        "string passo 2"
      ]
    }
  ]
}
```

IMPORTANTE: 
- Responda APENAS com JSON válido
- Seja ESPECÍFICO nas recomendações
- Calcule economias REALISTAS
- Considere ambiente de produção
- Justifique TECNICAMENTE cada decisão

Analise agora:"""
        
        return prompt
    
    async def _chamar_bedrock(self, prompt: str) -> str:
        """
        Chama o Amazon Bedrock para análise.
        
        Args:
            prompt: Prompt para análise
            
        Returns:
            Resposta do modelo de IA
        """
        try:
            bedrock_client = self.cliente_aws.obter_cliente('bedrock-runtime', self.regiao)
            
            corpo_requisicao = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 4096,
                "messages": [
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                "temperature": 0.1,
                "top_p": 0.9
            }
            
            logger.debug(f"Enviando prompt para Bedrock ({len(prompt)} caracteres)")
            
            response = bedrock_client.invoke_model(
                modelId=self.modelo_id,
                body=json.dumps(corpo_requisicao)
            )
            
            response_body = json.loads(response['body'].read())
            resposta_ia = response_body['content'][0]['text']
            
            logger.debug(f"Resposta recebida do Bedrock ({len(resposta_ia)} caracteres)")
            return resposta_ia
            
        except Exception as e:
            logger.error(f"Erro ao chamar Bedrock: {e}")
            raise
    
    def _processar_resposta_bedrock(self, resposta_ia: str) -> List[RecomendacaoOtimizacao]:
        """
        Processa a resposta do Bedrock e converte em entidades de domínio.
        
        Args:
            resposta_ia: Resposta JSON do Bedrock
            
        Returns:
            Lista de recomendações de otimização
        """
        try:
            # Limpar resposta (remover markdown se houver)
            resposta_limpa = resposta_ia.strip()
            if resposta_limpa.startswith('```json'):
                resposta_limpa = resposta_limpa[7:]
            if resposta_limpa.startswith('```'):
                resposta_limpa = resposta_limpa[3:]
            if resposta_limpa.endswith('```'):
                resposta_limpa = resposta_limpa[:-3]
            resposta_limpa = resposta_limpa.strip()
            
            # Parsear JSON
            dados_analise = json.loads(resposta_limpa)
            
            recomendacoes = []
            for rec_data in dados_analise.get('recomendacoes', []):
                try:
                    recomendacao = self._converter_para_recomendacao(rec_data)
                    recomendacoes.append(recomendacao)
                except Exception as e:
                    logger.warning(f"Erro ao converter recomendação: {e}")
                    continue
            
            logger.info(f"✓ {len(recomendacoes)} recomendações processadas com sucesso")
            return recomendacoes
            
        except json.JSONDecodeError as e:
            logger.error(f"Erro ao parsear JSON do Bedrock: {e}")
            logger.debug(f"Resposta problemática: {resposta_ia[:500]}...")
            return []
        except Exception as e:
            logger.error(f"Erro ao processar resposta do Bedrock: {e}")
            return []
    
    def _converter_para_recomendacao(self, dados: Dict[str, Any]) -> RecomendacaoOtimizacao:
        """
        Converte dados JSON em entidade RecomendacaoOtimizacao.
        
        Args:
            dados: Dados da recomendação em formato dict
            
        Returns:
            Entidade RecomendacaoOtimizacao
        """
        # Mapear strings para enums
        tipo_recurso = TipoRecurso(dados['tipo_recurso'])
        
        prioridade_map = {
            'alta': Prioridade.ALTA,
            'media': Prioridade.MEDIA,
            'baixa': Prioridade.BAIXA
        }
        prioridade = prioridade_map.get(dados['prioridade'], Prioridade.MEDIA)
        
        risco_map = {
            'baixo': NivelRisco.BAIXO,
            'medio': NivelRisco.MEDIO,
            'alto': NivelRisco.ALTO
        }
        nivel_risco = risco_map.get(dados['nivel_risco'], NivelRisco.MEDIO)
        
        padrao_map = {
            'constante': PadraoUso.CONSTANTE,
            'variavel': PadraoUso.VARIAVEL,
            'lote': PadraoUso.LOTE,
            'ocioso': PadraoUso.OCIOSO
        }
        padrao_uso = padrao_map.get(
            dados.get('analise', {}).get('padrao_uso', 'desconhecido'), 
            PadraoUso.DESCONHECIDO
        )
        
        return RecomendacaoOtimizacao(
            id_recurso=dados['id_recurso'],
            tipo_recurso=tipo_recurso,
            configuracao_atual=dados['configuracao_atual'],
            acao_recomendada=dados['recomendacao']['acao'],
            detalhes_recomendacao=dados['recomendacao']['detalhes'],
            justificativa=dados['recomendacao']['justificativa'],
            economia_mensal_usd=Decimal(str(dados['economia']['mensal_usd'])),
            economia_anual_usd=Decimal(str(dados['economia']['anual_usd'])),
            percentual_economia=float(dados['economia']['percentual']),
            nivel_risco=nivel_risco,
            prioridade=prioridade,
            passos_implementacao=dados.get('passos_implementacao', []),
            padrao_uso=padrao_uso,
            score_confianca=float(dados.get('analise', {}).get('score_confianca', 0.5))
        )
    
    def _dividir_em_lotes(self, recursos: List[RecursoAWS], tamanho_lote: int) -> List[List[RecursoAWS]]:
        """
        Divide lista de recursos em lotes menores.
        
        Args:
            recursos: Lista completa de recursos
            tamanho_lote: Tamanho máximo de cada lote
            
        Returns:
            Lista de lotes de recursos
        """
        lotes = []
        for i in range(0, len(recursos), tamanho_lote):
            lote = recursos[i:i + tamanho_lote]
            lotes.append(lote)
        
        return lotes
    
    def obter_estatisticas_uso(self) -> Dict[str, Any]:
        """Obtém estatísticas de uso do serviço."""
        return {
            'modelo_id': self.modelo_id,
            'regiao': self.regiao,
            'max_recursos_por_analise': self.max_recursos_por_analise
        }