"""
Infrastructure: Bedrock Client
Cliente para integração com Amazon Bedrock
"""

import json
import boto3
from typing import Dict, Any, Optional, List
from decimal import Decimal
import asyncio
from concurrent.futures import ThreadPoolExecutor

from ...core.exceptions import ExternalServiceError, RateLimitError, TimeoutError
from ...core.logging import get_logger, log_execution_time


class BedrockClient:
    """
    Cliente para Amazon Bedrock com padrões de resiliência
    
    Implementa:
    - Retry com backoff exponencial
    - Circuit breaker pattern
    - Rate limiting
    - Timeout handling
    - Logging estruturado
    """
    
    def __init__(
        self,
        region_name: str = 'us-east-1',
        model_id: str = 'anthropic.claude-3-sonnet-20240229-v1:0',
        max_retries: int = 3,
        timeout_seconds: int = 60,
        max_tokens: int = 4096
    ):
        self.region_name = region_name
        self.model_id = model_id
        self.max_retries = max_retries
        self.timeout_seconds = timeout_seconds
        self.max_tokens = max_tokens
        
        self.client = boto3.client('bedrock-runtime', region_name=region_name)
        self.executor = ThreadPoolExecutor(max_workers=5)
        self.logger = get_logger(self.__class__.__name__)
        
        # Circuit breaker state
        self._failure_count = 0
        self._last_failure_time = None
        self._circuit_open = False
        self._circuit_timeout = 60  # seconds
    
    @log_execution_time()
    async def analyze_resources(
        self,
        resources_data: List[Dict[str, Any]],
        cost_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analisa recursos usando Bedrock
        
        Args:
            resources_data: Lista de dados dos recursos
            cost_data: Dados de custo
        
        Returns:
            Análise estruturada do Bedrock
        
        Raises:
            ExternalServiceError: Erro na chamada do Bedrock
            TimeoutError: Timeout na operação
            RateLimitError: Limite de taxa excedido
        """
        if self._is_circuit_open():
            raise ExternalServiceError(
                'Bedrock', 
                'Circuit breaker aberto - muitas falhas recentes'
            )
        
        prompt = self._build_analysis_prompt(resources_data, cost_data)
        
        try:
            # Executar chamada de forma assíncrona
            response = await asyncio.wait_for(
                self._invoke_model_async(prompt),
                timeout=self.timeout_seconds
            )
            
            # Reset circuit breaker em caso de sucesso
            self._reset_circuit_breaker()
            
            return self._parse_response(response)
            
        except asyncio.TimeoutError:
            self._record_failure()
            raise TimeoutError('Bedrock analysis', self.timeout_seconds)
        
        except Exception as e:
            self._record_failure()
            
            if 'ThrottlingException' in str(e):
                raise RateLimitError('Bedrock', retry_after=60)
            
            raise ExternalServiceError('Bedrock', str(e))
    
    async def _invoke_model_async(self, prompt: str) -> Dict[str, Any]:
        """Invoca modelo de forma assíncrona"""
        loop = asyncio.get_event_loop()
        
        return await loop.run_in_executor(
            self.executor,
            self._invoke_model_sync,
            prompt
        )
    
    def _invoke_model_sync(self, prompt: str) -> Dict[str, Any]:
        """Invoca modelo de forma síncrona com retry"""
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": self.max_tokens,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1,
            "top_p": 0.9
        }
        
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                self.logger.debug(f"Tentativa {attempt + 1} de chamada ao Bedrock")
                
                response = self.client.invoke_model(
                    modelId=self.model_id,
                    body=json.dumps(request_body)
                )
                
                self.logger.info("Chamada ao Bedrock bem-sucedida")
                return response
                
            except Exception as e:
                last_exception = e
                self.logger.warning(f"Tentativa {attempt + 1} falhou: {str(e)}")
                
                if attempt < self.max_retries:
                    # Backoff exponencial
                    wait_time = (2 ** attempt) * 1
                    asyncio.sleep(wait_time)
        
        raise last_exception
    
    def _build_analysis_prompt(
        self,
        resources_data: List[Dict[str, Any]],
        cost_data: Dict[str, Any]
    ) -> str:
        """Constrói prompt para análise"""
        prompt = f"""Você é um especialista SÊNIOR em FinOps da AWS com 15 anos de experiência. 
Analise PROFUNDAMENTE todos os recursos AWS abaixo e forneça recomendações PRECISAS e ACIONÁVEIS.

## DADOS COLETADOS

### CUSTOS (Últimos 30 dias)
```json
{json.dumps(cost_data, indent=2, cls=DecimalEncoder)}
```

### RECURSOS AWS ({len(resources_data)} recursos)

"""
        
        # Adicionar recursos (limitado para não exceder token limit)
        for i, resource in enumerate(resources_data[:50]):
            prompt += f"\n**Recurso #{i+1}**: {resource.get('resource_type')} - {resource.get('resource_id')}\n"
            prompt += f"```json\n{json.dumps(resource, indent=2, cls=DecimalEncoder)}\n```\n"
        
        prompt += f"""

## SUA TAREFA

Analise CADA recurso e forneça:

1. **Padrão de uso** (steady/variable/batch/idle)
2. **Estatísticas** (média, p95, p99)
3. **Desperdício identificado** (%)
4. **Recomendação específica** (downsize/upsize/delete/optimize)
5. **Economia estimada** (USD/mês)
6. **Risco** (low/medium/high)
7. **Prioridade** (high/medium/low)

## FORMATO DE RESPOSTA (JSON ESTRITO)

```json
{{
  "summary": {{
    "total_resources_analyzed": {len(resources_data)},
    "total_monthly_savings_usd": 0.00,
    "total_annual_savings_usd": 0.00,
    "high_priority_actions": 0,
    "medium_priority_actions": 0,
    "low_priority_actions": 0
  }},
  "recommendations": [
    {{
      "resource_type": "EC2|RDS|ELB|Lambda|EBS",
      "resource_id": "id-do-recurso",
      "current_config": "t3a.large, 2 vCPU, 8GB RAM",
      "analysis": {{
        "pattern": "steady|variable|batch|idle",
        "cpu_mean": 21.3,
        "cpu_p95": 31.2,
        "waste_percentage": 70
      }},
      "recommendation": {{
        "action": "downsize|upsize|delete|optimize|no_change",
        "details": "Downsize de t3a.large para t3a.medium",
        "reasoning": "CPU p95 é 31%, indicando 70% de desperdício. Padrão steady permite downsize seguro."
      }},
      "savings": {{
        "monthly_usd": 27.37,
        "annual_usd": 328.44,
        "percentage": 50
      }},
      "risk_level": "low|medium|high",
      "priority": "high|medium|low",
      "implementation_steps": [
        "1. Criar snapshot/AMI",
        "2. Agendar janela de manutenção",
        "3. Modificar tipo de instância"
      ]
    }}
  ]
}}
```

IMPORTANTE: Responda APENAS com JSON válido, sem markdown, sem explicações adicionais."""
        
        return prompt
    
    def _parse_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Parse da resposta do Bedrock"""
        try:
            response_body = json.loads(response['body'].read())
            ai_response = response_body['content'][0]['text']
            
            # Limpar e parsear JSON
            clean_response = ai_response.strip()
            if clean_response.startswith('```json'):
                clean_response = clean_response[7:]
            if clean_response.startswith('```'):
                clean_response = clean_response[3:]
            if clean_response.endswith('```'):
                clean_response = clean_response[:-3]
            clean_response = clean_response.strip()
            
            analysis = json.loads(clean_response)
            
            return {
                'status': 'success',
                'model_used': self.model_id,
                'analysis': analysis
            }
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Erro ao parsear resposta do Bedrock: {str(e)}")
            raise ExternalServiceError('Bedrock', f'Resposta inválida: {str(e)}')
    
    def _is_circuit_open(self) -> bool:
        """Verifica se circuit breaker está aberto"""
        if not self._circuit_open:
            return False
        
        if self._last_failure_time is None:
            return False
        
        import time
        if time.time() - self._last_failure_time > self._circuit_timeout:
            self._circuit_open = False
            self._failure_count = 0
            self.logger.info("Circuit breaker fechado - tentando novamente")
            return False
        
        return True
    
    def _record_failure(self):
        """Registra falha para circuit breaker"""
        import time
        self._failure_count += 1
        self._last_failure_time = time.time()
        
        if self._failure_count >= 3:
            self._circuit_open = True
            self.logger.warning("Circuit breaker aberto devido a múltiplas falhas")
    
    def _reset_circuit_breaker(self):
        """Reset circuit breaker após sucesso"""
        self._failure_count = 0
        self._last_failure_time = None
        self._circuit_open = False


class DecimalEncoder(json.JSONEncoder):
    """Encoder para serializar Decimal em JSON"""
    
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)