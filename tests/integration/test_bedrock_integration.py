"""
Testes de integração para Bedrock Client
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from decimal import Decimal
import json

from src.infrastructure.aws.bedrock_client import BedrockClient, DecimalEncoder
from src.core.exceptions import ExternalServiceError, RateLimitError, TimeoutError


class TestBedrockClient:
    """Testes de integração para BedrockClient"""
    
    @pytest.fixture
    def bedrock_client(self):
        """Fixture para cliente Bedrock"""
        return BedrockClient(
            region_name='us-east-1',
            model_id='anthropic.claude-3-sonnet-20240229-v1:0',
            max_retries=2,
            timeout_seconds=30
        )
    
    @pytest.fixture
    def sample_resources_data(self):
        """Dados de exemplo para recursos"""
        return [
            {
                'resource_type': 'EC2',
                'resource_id': 'i-1234567890abcdef0',
                'instance_type': 't3.large',
                'state': 'running',
                'metrics': {
                    'cpu_utilization': [
                        {'timestamp': '2025-01-01T00:00:00Z', 'value': 25.5},
                        {'timestamp': '2025-01-01T01:00:00Z', 'value': 30.2},
                        {'timestamp': '2025-01-01T02:00:00Z', 'value': 22.8}
                    ]
                }
            },
            {
                'resource_type': 'RDS',
                'resource_id': 'mydb-instance',
                'instance_class': 'db.t3.medium',
                'engine': 'mysql',
                'metrics': {
                    'cpu_utilization': [
                        {'timestamp': '2025-01-01T00:00:00Z', 'value': 15.0},
                        {'timestamp': '2025-01-01T01:00:00Z', 'value': 18.5},
                        {'timestamp': '2025-01-01T02:00:00Z', 'value': 12.3}
                    ]
                }
            }
        ]
    
    @pytest.fixture
    def sample_cost_data(self):
        """Dados de exemplo para custos"""
        return {
            'period_days': 30,
            'total_cost_usd': 1250.75,
            'top_10_services': [
                {'service': 'Amazon Elastic Compute Cloud', 'cost_usd': 800.50, 'percentage': 64.0},
                {'service': 'Amazon Relational Database Service', 'cost_usd': 300.25, 'percentage': 24.0},
                {'service': 'Amazon Simple Storage Service', 'cost_usd': 150.00, 'percentage': 12.0}
            ]
        }
    
    @pytest.fixture
    def mock_bedrock_response(self):
        """Resposta mock do Bedrock"""
        return {
            'body': Mock(read=Mock(return_value=json.dumps({
                'content': [{
                    'text': json.dumps({
                        'summary': {
                            'total_resources_analyzed': 2,
                            'total_monthly_savings_usd': 125.50,
                            'total_annual_savings_usd': 1506.00,
                            'high_priority_actions': 1,
                            'medium_priority_actions': 1,
                            'low_priority_actions': 0
                        },
                        'recommendations': [
                            {
                                'resource_type': 'EC2',
                                'resource_id': 'i-1234567890abcdef0',
                                'current_config': 't3.large (2 vCPU, 8GB RAM)',
                                'analysis': {
                                    'pattern': 'steady',
                                    'cpu_mean': 26.2,
                                    'cpu_p95': 30.2,
                                    'waste_percentage': 69.8
                                },
                                'recommendation': {
                                    'action': 'downsize',
                                    'details': 'Downsize de t3.large para t3.medium',
                                    'reasoning': 'CPU p95 é 30.2%, indicando 69.8% de desperdício'
                                },
                                'savings': {
                                    'monthly_usd': 75.25,
                                    'annual_usd': 903.00,
                                    'percentage': 50.0
                                },
                                'risk_level': 'low',
                                'priority': 'high',
                                'implementation_steps': [
                                    '1. Criar AMI da instância atual',
                                    '2. Parar a instância',
                                    '3. Modificar tipo para t3.medium',
                                    '4. Iniciar instância'
                                ]
                            }
                        ]
                    })
                }]
            }).encode()))
        }
    
    @pytest.mark.asyncio
    async def test_analyze_resources_success(
        self, 
        bedrock_client, 
        sample_resources_data, 
        sample_cost_data, 
        mock_bedrock_response
    ):
        """Testa análise bem-sucedida de recursos"""
        with patch.object(bedrock_client.client, 'invoke_model', return_value=mock_bedrock_response):
            result = await bedrock_client.analyze_resources(sample_resources_data, sample_cost_data)
            
            assert result['status'] == 'success'
            assert result['model_used'] == 'anthropic.claude-3-sonnet-20240229-v1:0'
            assert 'analysis' in result
            
            analysis = result['analysis']
            assert analysis['summary']['total_resources_analyzed'] == 2
            assert analysis['summary']['total_monthly_savings_usd'] == 125.50
            assert len(analysis['recommendations']) == 1
            
            recommendation = analysis['recommendations'][0]
            assert recommendation['resource_type'] == 'EC2'
            assert recommendation['recommendation']['action'] == 'downsize'
            assert recommendation['savings']['monthly_usd'] == 75.25
    
    @pytest.mark.asyncio
    async def test_analyze_resources_timeout(
        self, 
        bedrock_client, 
        sample_resources_data, 
        sample_cost_data
    ):
        """Testa timeout na análise"""
        # Configurar timeout muito baixo
        bedrock_client.timeout_seconds = 0.001
        
        with patch.object(bedrock_client.client, 'invoke_model', side_effect=lambda **kwargs: asyncio.sleep(1)):
            with pytest.raises(TimeoutError) as exc_info:
                await bedrock_client.analyze_resources(sample_resources_data, sample_cost_data)
            
            assert 'Bedrock analysis' in str(exc_info.value)
            assert bedrock_client._failure_count > 0
    
    @pytest.mark.asyncio
    async def test_analyze_resources_throttling(
        self, 
        bedrock_client, 
        sample_resources_data, 
        sample_cost_data
    ):
        """Testa throttling do Bedrock"""
        throttling_error = Exception('ThrottlingException: Rate exceeded')
        
        with patch.object(bedrock_client.client, 'invoke_model', side_effect=throttling_error):
            with pytest.raises(RateLimitError) as exc_info:
                await bedrock_client.analyze_resources(sample_resources_data, sample_cost_data)
            
            assert 'Bedrock' in str(exc_info.value)
            assert exc_info.value.details['retry_after'] == 60
    
    @pytest.mark.asyncio
    async def test_analyze_resources_circuit_breaker(
        self, 
        bedrock_client, 
        sample_resources_data, 
        sample_cost_data
    ):
        """Testa circuit breaker após múltiplas falhas"""
        generic_error = Exception('Service unavailable')
        
        with patch.object(bedrock_client.client, 'invoke_model', side_effect=generic_error):
            # Primeira falha
            with pytest.raises(ExternalServiceError):
                await bedrock_client.analyze_resources(sample_resources_data, sample_cost_data)
            
            # Segunda falha
            with pytest.raises(ExternalServiceError):
                await bedrock_client.analyze_resources(sample_resources_data, sample_cost_data)
            
            # Terceira falha - deve abrir o circuit breaker
            with pytest.raises(ExternalServiceError):
                await bedrock_client.analyze_resources(sample_resources_data, sample_cost_data)
            
            # Quarta tentativa - circuit breaker aberto
            with pytest.raises(ExternalServiceError) as exc_info:
                await bedrock_client.analyze_resources(sample_resources_data, sample_cost_data)
            
            assert 'Circuit breaker aberto' in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_analyze_resources_retry_mechanism(
        self, 
        bedrock_client, 
        sample_resources_data, 
        sample_cost_data, 
        mock_bedrock_response
    ):
        """Testa mecanismo de retry"""
        call_count = 0
        
        def mock_invoke_model(**kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise Exception('Temporary failure')
            return mock_bedrock_response
        
        with patch.object(bedrock_client.client, 'invoke_model', side_effect=mock_invoke_model):
            result = await bedrock_client.analyze_resources(sample_resources_data, sample_cost_data)
            
            assert result['status'] == 'success'
            assert call_count == 2  # Primeira falha + retry bem-sucedido
    
    def test_build_analysis_prompt(self, bedrock_client, sample_resources_data, sample_cost_data):
        """Testa construção do prompt de análise"""
        prompt = bedrock_client._build_analysis_prompt(sample_resources_data, sample_cost_data)
        
        assert 'especialista SÊNIOR em FinOps' in prompt
        assert 'DADOS COLETADOS' in prompt
        assert 'CUSTOS (Últimos 30 dias)' in prompt
        assert 'RECURSOS AWS (2 recursos)' in prompt
        assert 'EC2 - i-1234567890abcdef0' in prompt
        assert 'RDS - mydb-instance' in prompt
        assert 'FORMATO DE RESPOSTA (JSON ESTRITO)' in prompt
        assert 'total_resources_analyzed' in prompt
    
    def test_parse_response_success(self, bedrock_client, mock_bedrock_response):
        """Testa parse bem-sucedido da resposta"""
        result = bedrock_client._parse_response(mock_bedrock_response)
        
        assert result['status'] == 'success'
        assert result['model_used'] == bedrock_client.model_id
        assert 'analysis' in result
        assert result['analysis']['summary']['total_resources_analyzed'] == 2
    
    def test_parse_response_with_markdown(self, bedrock_client):
        """Testa parse de resposta com markdown"""
        response_with_markdown = {
            'body': Mock(read=Mock(return_value=json.dumps({
                'content': [{
                    'text': '```json\n{"summary": {"total_resources_analyzed": 1}}\n```'
                }]
            }).encode()))
        }
        
        result = bedrock_client._parse_response(response_with_markdown)
        
        assert result['status'] == 'success'
        assert result['analysis']['summary']['total_resources_analyzed'] == 1
    
    def test_parse_response_invalid_json(self, bedrock_client):
        """Testa parse de resposta com JSON inválido"""
        invalid_response = {
            'body': Mock(read=Mock(return_value=json.dumps({
                'content': [{
                    'text': 'Invalid JSON response'
                }]
            }).encode()))
        }
        
        with pytest.raises(ExternalServiceError) as exc_info:
            bedrock_client._parse_response(invalid_response)
        
        assert 'Resposta inválida' in str(exc_info.value)
    
    def test_circuit_breaker_reset_after_timeout(self, bedrock_client):
        """Testa reset do circuit breaker após timeout"""
        import time
        
        # Simular falhas para abrir circuit breaker
        bedrock_client._failure_count = 3
        bedrock_client._circuit_open = True
        bedrock_client._last_failure_time = time.time() - 70  # 70 segundos atrás
        
        # Circuit breaker deve estar fechado agora
        assert not bedrock_client._is_circuit_open()
        assert bedrock_client._failure_count == 0
        assert not bedrock_client._circuit_open
    
    def test_record_failure(self, bedrock_client):
        """Testa registro de falhas"""
        initial_count = bedrock_client._failure_count
        
        bedrock_client._record_failure()
        
        assert bedrock_client._failure_count == initial_count + 1
        assert bedrock_client._last_failure_time is not None
        
        # Simular múltiplas falhas
        bedrock_client._record_failure()
        bedrock_client._record_failure()
        
        assert bedrock_client._circuit_open is True
    
    def test_reset_circuit_breaker(self, bedrock_client):
        """Testa reset do circuit breaker"""
        # Configurar estado de falha
        bedrock_client._failure_count = 5
        bedrock_client._circuit_open = True
        bedrock_client._last_failure_time = 12345
        
        bedrock_client._reset_circuit_breaker()
        
        assert bedrock_client._failure_count == 0
        assert bedrock_client._last_failure_time is None
        assert bedrock_client._circuit_open is False


class TestDecimalEncoder:
    """Testes para DecimalEncoder"""
    
    def test_decimal_encoding(self):
        """Testa codificação de Decimal"""
        encoder = DecimalEncoder()
        
        data = {
            'cost': Decimal('123.45'),
            'savings': Decimal('67.89'),
            'percentage': 25.5,
            'name': 'test'
        }
        
        result = json.dumps(data, cls=DecimalEncoder)
        parsed = json.loads(result)
        
        assert parsed['cost'] == 123.45
        assert parsed['savings'] == 67.89
        assert parsed['percentage'] == 25.5
        assert parsed['name'] == 'test'
    
    def test_non_decimal_passthrough(self):
        """Testa que outros tipos passam sem modificação"""
        encoder = DecimalEncoder()
        
        # Testar tipos que não são Decimal
        assert encoder.default(123) == 123
        assert encoder.default('test') == 'test'
        assert encoder.default([1, 2, 3]) == [1, 2, 3]
        
        # Testar Decimal
        assert encoder.default(Decimal('45.67')) == 45.67


if __name__ == '__main__':
    pytest.main([__file__, '-v'])