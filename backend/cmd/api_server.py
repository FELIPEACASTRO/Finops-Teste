"""
FastAPI Application Factory

This module creates and configures the FastAPI application with all
necessary middleware, routes, and dependencies following Clean Architecture.

Features:
- Dependency injection container
- Middleware setup (CORS, Auth, Rate limiting, Logging)
- Route registration
- Error handling
- Health checks
- OpenAPI documentation
"""

from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from internal.infra.config import get_settings
from internal.infra.database import get_database_manager, close_database_manager
from internal.observability.logger import get_logger
from internal.observability.metrics import get_finops_metrics, export_prometheus_metrics
from internal.controller.cost_controller import create_cost_router
from internal.controller.optimization_controller import create_optimization_router
from internal.controller.budget_controller import create_budget_router
from internal.usecase.cost_analysis import UseCaseFactory
from internal.repository.postgres_resource_repository import PostgresResourceRepository
from internal.repository.postgres_cost_repository import PostgresCostRepository
from internal.repository.postgres_optimization_repository import PostgresOptimizationRepository
from internal.repository.postgres_budget_repository import PostgresBudgetRepository


class DependencyContainer:
    """Dependency injection container"""
    
    def __init__(self):
        self.settings = get_settings()
        self.logger = get_logger(__name__)
        self._db_manager = None
        self._repositories = {}
        self._use_case_factory = None
    
    async def initialize(self):
        """Initialize all dependencies"""
        self.logger.info("Initializing dependency container")
        
        # Initialize database
        self._db_manager = await get_database_manager()
        
        # Initialize repositories
        self._repositories = {
            'resource': PostgresResourceRepository(self._db_manager),
            'cost': PostgresCostRepository(self._db_manager),
            'optimization': PostgresOptimizationRepository(self._db_manager),
            'budget': PostgresBudgetRepository(self._db_manager),
        }
        
        # Initialize use case factory (would need to implement external services)
        # For now, we'll create a mock factory
        self._use_case_factory = MockUseCaseFactory(self._repositories)
        
        self.logger.info("Dependency container initialized successfully")
    
    async def cleanup(self):
        """Cleanup resources"""
        self.logger.info("Cleaning up dependency container")
        
        if self._db_manager:
            await close_database_manager()
        
        self.logger.info("Dependency container cleanup complete")
    
    @property
    def use_case_factory(self) -> UseCaseFactory:
        """Get use case factory"""
        return self._use_case_factory


class MockUseCaseFactory(UseCaseFactory):
    """Mock use case factory for development"""
    
    def __init__(self, repositories: Dict[str, Any]):
        self.repositories = repositories
        # In a real implementation, you would inject external services here
        # (CloudMetricsService, MLPredictionService, NotificationService)
    
    def create_cost_analysis_use_case(self):
        """Create cost analysis use case with mock services"""
        from internal.usecase.cost_analysis import CostAnalysisUseCase
        
        # Mock services - in production these would be real implementations
        class MockMetricsService:
            async def get_resource_metrics(self, resource_id: str, time_range):
                return {"cpu_utilization": 25.0, "memory_utilization": 40.0}
            
            async def get_cost_data(self, resource_id: str, time_range):
                return [{"cost": 100.0, "currency": "USD"}]
        
        return CostAnalysisUseCase(
            self.repositories['cost'],
            self.repositories['resource'],
            MockMetricsService()
        )
    
    def create_optimization_use_case(self):
        """Create optimization use case with mock services"""
        from internal.usecase.cost_analysis import OptimizationUseCase
        
        # Mock services
        class MockMetricsService:
            async def get_resource_metrics(self, resource_id: str, time_range):
                return {"cpu_utilization": 25.0}
        
        class MockMLService:
            async def generate_optimization_recommendations(self, resource, metrics):
                return []
        
        class MockNotificationService:
            async def send_optimization_report(self, recommendations):
                pass
        
        return OptimizationUseCase(
            self.repositories['optimization'],
            self.repositories['resource'],
            self.repositories['cost'],
            MockMetricsService(),
            MockMLService(),
            MockNotificationService()
        )
    
    def create_budget_management_use_case(self):
        """Create budget management use case with mock services"""
        from internal.usecase.cost_analysis import BudgetManagementUseCase
        
        class MockNotificationService:
            async def send_budget_alert(self, budget, threshold):
                pass
        
        return BudgetManagementUseCase(
            self.repositories['budget'],
            self.repositories['cost'],
            MockNotificationService()
        )


# Global dependency container
_container: DependencyContainer = None


async def get_container() -> DependencyContainer:
    """Get dependency container"""
    global _container
    if _container is None:
        _container = DependencyContainer()
        await _container.initialize()
    return _container


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger = get_logger(__name__)
    
    # Startup
    logger.info("Application startup")
    container = await get_container()
    app.state.container = container
    
    yield
    
    # Shutdown
    logger.info("Application shutdown")
    if hasattr(app.state, 'container'):
        await app.state.container.cleanup()


async def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    settings = get_settings()
    logger = get_logger(__name__)
    
    # Create FastAPI app
    app = FastAPI(
        title=settings.app.app_name,
        description=settings.app.app_description,
        version=settings.app.app_version,
        docs_url=settings.api.docs_url if settings.api.docs_enabled else None,
        redoc_url=settings.api.redoc_url if settings.api.docs_enabled else None,
        lifespan=lifespan
    )
    
    # Add middleware
    await setup_middleware(app, settings)
    
    # Add routes
    await setup_routes(app)
    
    # Add error handlers
    setup_error_handlers(app)
    
    logger.info("FastAPI application created successfully")
    return app


async def setup_middleware(app: FastAPI, settings):
    """Setup application middleware"""
    logger = get_logger(__name__)
    
    # Trusted hosts
    if not settings.app.debug:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=["*"]  # Configure properly in production
        )
    
    # CORS
    cors_config = settings.get_cors_config()
    app.add_middleware(
        CORSMiddleware,
        **cors_config
    )
    
    # Request logging middleware
    @app.middleware("http")
    async def logging_middleware(request: Request, call_next):
        import time
        
        start_time = time.time()
        
        # Process request
        response = await call_next(request)
        
        # Log request
        duration = time.time() - start_time
        metrics = get_finops_metrics()
        metrics.record_http_request(
            method=request.method,
            endpoint=str(request.url.path),
            status_code=response.status_code,
            duration_seconds=duration
        )
        
        logger.info(
            f"{request.method} {request.url.path} - {response.status_code}",
            extra={
                "method": request.method,
                "path": str(request.url.path),
                "status_code": response.status_code,
                "duration_ms": duration * 1000,
                "user_agent": request.headers.get("user-agent"),
                "remote_addr": request.client.host if request.client else None
            }
        )
        
        return response
    
    logger.info("Middleware setup complete")


async def setup_routes(app: FastAPI):
    """Setup application routes"""
    logger = get_logger(__name__)
    
    # Get container for dependency injection
    container = await get_container()
    
    # Health check
    @app.get("/health", tags=["Health"])
    async def health_check():
        """Application health check"""
        return {
            "status": "healthy",
            "version": get_settings().app.app_version,
            "environment": get_settings().app.environment.value,
            "timestamp": "2024-11-25T22:00:00Z"
        }
    
    # Metrics endpoint
    @app.get("/metrics", tags=["Monitoring"])
    async def metrics():
        """Prometheus metrics endpoint"""
        return export_prometheus_metrics()
    
    # API routes
    app.include_router(
        create_cost_router(container.use_case_factory),
        prefix="/api/v1"
    )
    
    app.include_router(
        create_optimization_router(container.use_case_factory),
        prefix="/api/v1"
    )
    
    app.include_router(
        create_budget_router(container.use_case_factory),
        prefix="/api/v1"
    )
    
    logger.info("Routes setup complete")


def setup_error_handlers(app: FastAPI):
    """Setup error handlers"""
    logger = get_logger(__name__)
    
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        """Handle HTTP exceptions"""
        logger.warning(
            f"HTTP exception: {exc.status_code} - {exc.detail}",
            extra={
                "status_code": exc.status_code,
                "detail": exc.detail,
                "path": str(request.url.path),
                "method": request.method
            }
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.detail,
                "status_code": exc.status_code,
                "path": str(request.url.path)
            }
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Handle validation errors"""
        logger.warning(
            f"Validation error: {exc.errors()}",
            extra={
                "errors": exc.errors(),
                "path": str(request.url.path),
                "method": request.method
            }
        )
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": "Validation error",
                "details": exc.errors(),
                "status_code": 422
            }
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Handle general exceptions"""
        logger.error(
            f"Unhandled exception: {str(exc)}",
            extra={
                "exception_type": type(exc).__name__,
                "path": str(request.url.path),
                "method": request.method
            },
            exc_info=exc
        )
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Internal server error",
                "status_code": 500
            }
        )
    
    logger.info("Error handlers setup complete")