"""
Core Exceptions
Exceções customizadas do domínio da aplicação
"""

from typing import Optional, Dict, Any


class FinOpsException(Exception):
    """Exceção base para todas as exceções do FinOps"""
    
    def __init__(
        self, 
        message: str, 
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}


class ValidationError(FinOpsException):
    """Erro de validação de dados"""
    pass


class ResourceNotFoundError(FinOpsException):
    """Recurso não encontrado"""
    
    def __init__(self, resource_id: str, resource_type: Optional[str] = None):
        message = f"Recurso '{resource_id}' não encontrado"
        if resource_type:
            message += f" (tipo: {resource_type})"
        
        super().__init__(
            message=message,
            error_code="RESOURCE_NOT_FOUND",
            details={'resource_id': resource_id, 'resource_type': resource_type}
        )


class AnalysisError(FinOpsException):
    """Erro durante análise de recursos"""
    pass


class RecommendationError(FinOpsException):
    """Erro na geração de recomendações"""
    pass


class RepositoryError(FinOpsException):
    """Erro de repositório/persistência"""
    pass


class ExternalServiceError(FinOpsException):
    """Erro em serviços externos (AWS, Bedrock, etc.)"""
    
    def __init__(
        self, 
        service_name: str, 
        message: str, 
        status_code: Optional[int] = None
    ):
        super().__init__(
            message=f"Erro no serviço {service_name}: {message}",
            error_code="EXTERNAL_SERVICE_ERROR",
            details={'service_name': service_name, 'status_code': status_code}
        )


class ConfigurationError(FinOpsException):
    """Erro de configuração"""
    pass


class AuthenticationError(FinOpsException):
    """Erro de autenticação"""
    pass


class AuthorizationError(FinOpsException):
    """Erro de autorização"""
    pass


class RateLimitError(FinOpsException):
    """Erro de limite de taxa"""
    
    def __init__(self, service_name: str, retry_after: Optional[int] = None):
        message = f"Limite de taxa excedido para {service_name}"
        if retry_after:
            message += f". Tente novamente em {retry_after} segundos"
        
        super().__init__(
            message=message,
            error_code="RATE_LIMIT_EXCEEDED",
            details={'service_name': service_name, 'retry_after': retry_after}
        )


class TimeoutError(FinOpsException):
    """Erro de timeout"""
    
    def __init__(self, operation: str, timeout_seconds: int):
        super().__init__(
            message=f"Timeout na operação '{operation}' após {timeout_seconds}s",
            error_code="OPERATION_TIMEOUT",
            details={'operation': operation, 'timeout_seconds': timeout_seconds}
        )