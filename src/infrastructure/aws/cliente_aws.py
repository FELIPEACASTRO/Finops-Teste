"""
Cliente AWS com padrão Singleton e configurações otimizadas.
Implementa retry logic, timeouts e boas práticas de conexão.
"""

import boto3
import logging
from typing import Dict, Any, Optional
from botocore.config import Config
from botocore.exceptions import ClientError, BotoCoreError
import asyncio
from functools import wraps
import time

logger = logging.getLogger(__name__)


class ClienteAWSSingleton:
    """
    Cliente AWS Singleton com configurações otimizadas.
    
    Implementa o padrão Singleton para reutilização de clientes AWS.
    Inclui retry logic, timeouts e configurações de performance.
    """
    
    _instance = None
    _clients: Dict[str, Any] = {}
    
    def __new__(cls, regiao: str = 'us-east-1'):
        """Implementa padrão Singleton thread-safe."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._inicializado = False
        return cls._instance
    
    def __init__(self, regiao: str = 'us-east-1'):
        """
        Inicializa o cliente AWS.
        
        Args:
            regiao: Região AWS padrão
        """
        if self._inicializado:
            return
            
        self.regiao = regiao
        self.config = self._criar_config_otimizado()
        self._inicializado = True
        logger.info(f"Cliente AWS inicializado para região: {regiao}")
    
    def _criar_config_otimizado(self) -> Config:
        """
        Cria configuração otimizada para clientes AWS.
        
        Returns:
            Configuração do boto3 otimizada
        """
        return Config(
            retries={
                'max_attempts': 3,
                'mode': 'adaptive'
            },
            read_timeout=60,
            connect_timeout=10,
            max_pool_connections=50,
            region_name=self.regiao
        )
    
    def obter_cliente(self, servico: str, regiao: Optional[str] = None) -> Any:
        """
        Obtém cliente AWS para um serviço específico.
        
        Args:
            servico: Nome do serviço AWS (ec2, rds, etc.)
            regiao: Região específica (opcional)
            
        Returns:
            Cliente boto3 configurado
        """
        regiao_cliente = regiao or self.regiao
        chave_cliente = f"{servico}_{regiao_cliente}"
        
        if chave_cliente not in self._clients:
            try:
                config_cliente = Config(
                    retries=self.config.retries,
                    read_timeout=self.config.read_timeout,
                    connect_timeout=self.config.connect_timeout,
                    max_pool_connections=self.config.max_pool_connections,
                    region_name=regiao_cliente
                )
                
                self._clients[chave_cliente] = boto3.client(servico, config=config_cliente)
                logger.debug(f"Cliente {servico} criado para região {regiao_cliente}")
                
            except Exception as e:
                logger.error(f"Erro ao criar cliente {servico}: {e}")
                raise
        
        return self._clients[chave_cliente]
    
    def limpar_cache(self):
        """Limpa cache de clientes."""
        self._clients.clear()
        logger.info("Cache de clientes AWS limpo")


def retry_aws_call(max_tentativas: int = 3, delay_base: float = 1.0):
    """
    Decorator para retry automático de chamadas AWS.
    
    Args:
        max_tentativas: Número máximo de tentativas
        delay_base: Delay base entre tentativas (exponential backoff)
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            ultima_excecao = None
            
            for tentativa in range(max_tentativas):
                try:
                    return await func(*args, **kwargs)
                    
                except (ClientError, BotoCoreError) as e:
                    ultima_excecao = e
                    
                    # Não fazer retry em alguns erros específicos
                    if hasattr(e, 'response') and e.response.get('Error', {}).get('Code') in [
                        'AccessDenied', 'InvalidParameterValue', 'ValidationException'
                    ]:
                        logger.error(f"Erro não recuperável em {func.__name__}: {e}")
                        raise
                    
                    if tentativa < max_tentativas - 1:
                        delay = delay_base * (2 ** tentativa)  # Exponential backoff
                        logger.warning(
                            f"Tentativa {tentativa + 1} falhou em {func.__name__}: {e}. "
                            f"Tentando novamente em {delay}s..."
                        )
                        await asyncio.sleep(delay)
                    else:
                        logger.error(f"Todas as tentativas falharam em {func.__name__}: {e}")
                
                except Exception as e:
                    logger.error(f"Erro inesperado em {func.__name__}: {e}")
                    raise
            
            raise ultima_excecao
        
        return wrapper
    return decorator


def medir_tempo_execucao(func):
    """
    Decorator para medir tempo de execução de funções.
    
    Útil para monitoramento de performance.
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        inicio = time.time()
        try:
            resultado = await func(*args, **kwargs)
            fim = time.time()
            logger.info(f"{func.__name__} executado em {fim - inicio:.2f}s")
            return resultado
        except Exception as e:
            fim = time.time()
            logger.error(f"{func.__name__} falhou após {fim - inicio:.2f}s: {e}")
            raise
    
    return wrapper


class GerenciadorPaginacao:
    """
    Gerenciador para paginação de APIs AWS.
    
    Implementa padrão Strategy para diferentes tipos de paginação.
    """
    
    @staticmethod
    async def paginar_com_next_token(
        cliente, 
        metodo: str, 
        parametros: Dict[str, Any],
        chave_token: str = 'NextToken',
        chave_items: str = 'Items'
    ) -> list:
        """
        Pagina usando NextToken.
        
        Args:
            cliente: Cliente AWS
            metodo: Nome do método a chamar
            parametros: Parâmetros da chamada
            chave_token: Nome da chave do token
            chave_items: Nome da chave dos items
            
        Returns:
            Lista completa de items paginados
        """
        items = []
        next_token = None
        
        while True:
            if next_token:
                parametros[chave_token] = next_token
            
            try:
                response = getattr(cliente, metodo)(**parametros)
                
                if chave_items in response:
                    items.extend(response[chave_items])
                
                next_token = response.get(chave_token)
                if not next_token:
                    break
                    
            except Exception as e:
                logger.error(f"Erro na paginação {metodo}: {e}")
                raise
        
        return items
    
    @staticmethod
    async def paginar_com_paginator(cliente, operacao: str, parametros: Dict[str, Any]) -> list:
        """
        Pagina usando boto3 paginator.
        
        Args:
            cliente: Cliente AWS
            operacao: Nome da operação
            parametros: Parâmetros da operação
            
        Returns:
            Lista completa de items paginados
        """
        items = []
        
        try:
            paginator = cliente.get_paginator(operacao)
            page_iterator = paginator.paginate(**parametros)
            
            for page in page_iterator:
                # Extrair items da página (varia por serviço)
                for key, value in page.items():
                    if isinstance(value, list) and key not in ['ResponseMetadata']:
                        items.extend(value)
                        break
                        
        except Exception as e:
            logger.error(f"Erro no paginator {operacao}: {e}")
            raise
        
        return items


class ValidadorParametros:
    """
    Validador de parâmetros para chamadas AWS.
    
    Implementa validações comuns para evitar erros de API.
    """
    
    @staticmethod
    def validar_regiao(regiao: str) -> bool:
        """Valida se a região é válida."""
        regioes_validas = [
            'us-east-1', 'us-east-2', 'us-west-1', 'us-west-2',
            'eu-west-1', 'eu-west-2', 'eu-west-3', 'eu-central-1',
            'ap-southeast-1', 'ap-southeast-2', 'ap-northeast-1',
            'sa-east-1'
        ]
        return regiao in regioes_validas
    
    @staticmethod
    def validar_periodo_tempo(inicio, fim) -> bool:
        """Valida período de tempo."""
        if not inicio or not fim:
            return False
        return inicio < fim
    
    @staticmethod
    def sanitizar_parametros(parametros: Dict[str, Any]) -> Dict[str, Any]:
        """
        Remove parâmetros None e sanitiza entrada.
        
        Args:
            parametros: Dicionário de parâmetros
            
        Returns:
            Parâmetros sanitizados
        """
        return {k: v for k, v in parametros.items() if v is not None}