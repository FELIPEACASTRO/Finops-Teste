"""
Core Logging
Sistema de logging estruturado para a aplicação
"""

import logging
import json
import sys
from datetime import datetime
from typing import Any, Dict, Optional
from functools import wraps
import traceback


class StructuredFormatter(logging.Formatter):
    """Formatter para logs estruturados em JSON"""
    
    def format(self, record: logging.LogRecord) -> str:
        """Formata log record como JSON estruturado"""
        log_data = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Adicionar contexto extra se disponível
        if hasattr(record, 'extra') and record.extra:
            log_data['context'] = record.extra
        
        # Adicionar exception info se disponível
        if record.exc_info:
            log_data['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': traceback.format_exception(*record.exc_info)
            }
        
        # Adicionar stack info se disponível
        if record.stack_info:
            log_data['stack_info'] = record.stack_info
        
        return json.dumps(log_data, ensure_ascii=False)


def setup_logging(
    level: str = "INFO",
    format_type: str = "structured"  # "structured" ou "simple"
) -> None:
    """
    Configura sistema de logging da aplicação
    
    Args:
        level: Nível de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_type: Tipo de formatação ("structured" para JSON, "simple" para texto)
    """
    # Converter string para nível
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    
    # Configurar handler
    handler = logging.StreamHandler(sys.stdout)
    
    if format_type == "structured":
        formatter = StructuredFormatter()
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    handler.setFormatter(formatter)
    
    # Configurar logger raiz
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    
    # Configurar loggers específicos
    logging.getLogger('boto3').setLevel(logging.WARNING)
    logging.getLogger('botocore').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Obtém logger configurado para um módulo
    
    Args:
        name: Nome do logger (geralmente __name__)
    
    Returns:
        Logger configurado
    """
    return logging.getLogger(name)


class LoggerAdapter(logging.LoggerAdapter):
    """Adapter para adicionar contexto consistente aos logs"""
    
    def __init__(self, logger: logging.Logger, extra: Dict[str, Any]):
        super().__init__(logger, extra)
    
    def process(self, msg: str, kwargs: Dict[str, Any]) -> tuple:
        """Processa mensagem adicionando contexto extra"""
        if 'extra' in kwargs:
            kwargs['extra'].update(self.extra)
        else:
            kwargs['extra'] = self.extra.copy()
        
        return msg, kwargs


def log_execution_time(logger: Optional[logging.Logger] = None):
    """
    Decorator para logar tempo de execução de funções
    
    Args:
        logger: Logger a usar (se None, usa logger do módulo)
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = datetime.now()
            func_logger = logger or get_logger(func.__module__)
            
            func_logger.info(f"Iniciando execução de {func.__name__}")
            
            try:
                result = await func(*args, **kwargs)
                execution_time = (datetime.now() - start_time).total_seconds()
                
                func_logger.info(
                    f"Execução de {func.__name__} concluída",
                    extra={
                        'function': func.__name__,
                        'execution_time_seconds': round(execution_time, 3),
                        'status': 'success'
                    }
                )
                
                return result
                
            except Exception as e:
                execution_time = (datetime.now() - start_time).total_seconds()
                
                func_logger.error(
                    f"Erro na execução de {func.__name__}: {str(e)}",
                    extra={
                        'function': func.__name__,
                        'execution_time_seconds': round(execution_time, 3),
                        'status': 'error',
                        'error_type': type(e).__name__
                    },
                    exc_info=True
                )
                
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = datetime.now()
            func_logger = logger or get_logger(func.__module__)
            
            func_logger.info(f"Iniciando execução de {func.__name__}")
            
            try:
                result = func(*args, **kwargs)
                execution_time = (datetime.now() - start_time).total_seconds()
                
                func_logger.info(
                    f"Execução de {func.__name__} concluída",
                    extra={
                        'function': func.__name__,
                        'execution_time_seconds': round(execution_time, 3),
                        'status': 'success'
                    }
                )
                
                return result
                
            except Exception as e:
                execution_time = (datetime.now() - start_time).total_seconds()
                
                func_logger.error(
                    f"Erro na execução de {func.__name__}: {str(e)}",
                    extra={
                        'function': func.__name__,
                        'execution_time_seconds': round(execution_time, 3),
                        'status': 'error',
                        'error_type': type(e).__name__
                    },
                    exc_info=True
                )
                
                raise
        
        # Retornar wrapper apropriado baseado se a função é async
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def log_method_calls(logger: Optional[logging.Logger] = None):
    """
    Decorator para logar chamadas de métodos com parâmetros
    
    Args:
        logger: Logger a usar (se None, usa logger do módulo)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            func_logger = logger or get_logger(func.__module__)
            
            # Preparar informações dos parâmetros (sem valores sensíveis)
            safe_args = []
            for i, arg in enumerate(args[1:], 1):  # Skip self
                if isinstance(arg, (str, int, float, bool)):
                    safe_args.append(f"arg{i}={arg}")
                else:
                    safe_args.append(f"arg{i}={type(arg).__name__}")
            
            safe_kwargs = {}
            for k, v in kwargs.items():
                if k.lower() in ['password', 'token', 'secret', 'key']:
                    safe_kwargs[k] = "***"
                elif isinstance(v, (str, int, float, bool)):
                    safe_kwargs[k] = v
                else:
                    safe_kwargs[k] = type(v).__name__
            
            func_logger.debug(
                f"Chamando {func.__name__}",
                extra={
                    'function': func.__name__,
                    'args': safe_args,
                    'kwargs': safe_kwargs
                }
            )
            
            return func(*args, **kwargs)
        
        return wrapper
    
    return decorator