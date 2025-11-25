#!/usr/bin/env python3
"""
FinOps-Teste Main Application Entry Point

This is the main entry point for the FinOps-Teste application following Clean Architecture principles.
The application is designed as a modular monolith with clear bounded contexts and dependency inversion.

Architecture:
- Clean Architecture / Hexagonal Architecture (Ports and Adapters)
- Domain-Driven Design (DDD) with bounded contexts
- SOLID principles throughout
- Event-driven architecture for inter-module communication
- CQRS for read/write separation where appropriate

Performance Targets (SLOs):
- P95 < 200ms for reads, < 500ms for writes
- 2000 TPS throughput
- 99.9% availability
- 10,000 concurrent users support

Author: Manus AI
Date: November 25, 2025
Version: 1.0.0
"""

import asyncio
import logging
import signal
import sys
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import make_asgi_app

# Internal imports following Clean Architecture dependency rule
from backend.internal.infra.config import Settings, get_settings
from backend.internal.infra.database import DatabaseManager
from backend.internal.infra.logging_config import setup_logging
from backend.internal.infra.metrics import MetricsManager
from backend.internal.infra.health import HealthChecker
from backend.internal.controller.http.routes import setup_routes
from backend.internal.middleware.auth import AuthMiddleware
from backend.internal.middleware.rate_limiting import RateLimitingMiddleware
from backend.internal.middleware.request_id import RequestIDMiddleware
from backend.internal.middleware.error_handler import ErrorHandlerMiddleware
from backend.internal.observability.tracing import setup_tracing
from backend.internal.observability.monitoring import setup_monitoring


class FinOpsApplication:
    """
    Main application class following the Application Service pattern.
    
    Responsibilities:
    - Application lifecycle management
    - Dependency injection setup
    - Middleware configuration
    - Graceful shutdown handling
    """
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.db_manager: DatabaseManager | None = None
        self.metrics_manager: MetricsManager | None = None
        self.health_checker: HealthChecker | None = None
        self.logger = logging.getLogger(__name__)
        
    async def startup(self) -> None:
        """Initialize application dependencies and resources."""
        try:
            self.logger.info("🚀 Starting FinOps-Teste application...")
            
            # Initialize core infrastructure
            self.db_manager = DatabaseManager(self.settings.database_url)
            await self.db_manager.initialize()
            
            # Initialize metrics and monitoring
            self.metrics_manager = MetricsManager()
            await self.metrics_manager.initialize()
            
            # Initialize health checker
            self.health_checker = HealthChecker(
                db_manager=self.db_manager,
                metrics_manager=self.metrics_manager
            )
            
            # Setup distributed tracing
            setup_tracing(self.settings)
            
            # Setup monitoring and observability
            setup_monitoring(self.settings)
            
            self.logger.info("✅ Application startup completed successfully")
            
        except Exception as e:
            self.logger.error(f"❌ Application startup failed: {e}")
            raise
    
    async def shutdown(self) -> None:
        """Gracefully shutdown application resources."""
        try:
            self.logger.info("🛑 Shutting down FinOps-Teste application...")
            
            if self.db_manager:
                await self.db_manager.close()
            
            if self.metrics_manager:
                await self.metrics_manager.close()
            
            self.logger.info("✅ Application shutdown completed successfully")
            
        except Exception as e:
            self.logger.error(f"❌ Application shutdown failed: {e}")
            raise


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    FastAPI lifespan context manager for startup/shutdown events.
    
    This replaces the deprecated startup/shutdown event handlers and provides
    better error handling and resource management.
    """
    settings = get_settings()
    finops_app = FinOpsApplication(settings)
    
    # Store in app state for access in routes
    app.state.finops_app = finops_app
    
    try:
        # Startup
        await finops_app.startup()
        yield
    finally:
        # Shutdown
        await finops_app.shutdown()


def create_app() -> FastAPI:
    """
    Application factory following the Factory pattern.
    
    Creates and configures the FastAPI application with all necessary
    middleware, routes, and error handlers.
    
    Returns:
        FastAPI: Configured application instance
    """
    settings = get_settings()
    
    # Create FastAPI app with comprehensive configuration
    app = FastAPI(
        title="FinOps-Teste API",
        description="Enterprise-grade FinOps platform for cloud cost optimization",
        version="1.0.0",
        docs_url="/docs" if settings.environment != "production" else None,
        redoc_url="/redoc" if settings.environment != "production" else None,
        openapi_url="/openapi.json" if settings.environment != "production" else None,
        lifespan=lifespan,
        # Performance optimizations
        generate_unique_id_function=lambda route: f"{route.tags[0]}-{route.name}" if route.tags else route.name,
    )
    
    # Add middleware in reverse order (last added = first executed)
    
    # Error handling middleware (outermost)
    app.add_middleware(ErrorHandlerMiddleware)
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "X-Response-Time"],
    )
    
    # Compression middleware
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    
    # Rate limiting middleware
    app.add_middleware(RateLimitingMiddleware, settings=settings)
    
    # Authentication middleware
    app.add_middleware(AuthMiddleware, settings=settings)
    
    # Request ID middleware (innermost - adds correlation ID)
    app.add_middleware(RequestIDMiddleware)
    
    # Setup API routes
    setup_routes(app)
    
    # Add Prometheus metrics endpoint
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)
    
    return app


def setup_signal_handlers(app: FastAPI) -> None:
    """Setup graceful shutdown signal handlers."""
    def signal_handler(signum: int, frame) -> None:
        logging.info(f"Received signal {signum}, initiating graceful shutdown...")
        sys.exit(0)
    
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)


def main() -> None:
    """
    Main entry point for the application.
    
    This function:
    1. Sets up logging
    2. Loads configuration
    3. Creates the FastAPI app
    4. Configures signal handlers
    5. Starts the Uvicorn server
    """
    # Setup logging first
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # Load settings
        settings = get_settings()
        logger.info(f"🔧 Starting FinOps-Teste in {settings.environment} mode")
        
        # Create application
        app = create_app()
        
        # Setup signal handlers for graceful shutdown
        setup_signal_handlers(app)
        
        # Configure Uvicorn server
        uvicorn_config = {
            "app": app,
            "host": settings.host,
            "port": settings.port,
            "log_config": None,  # Use our custom logging
            "access_log": False,  # We handle access logs in middleware
            "server_header": False,  # Security: don't expose server info
            "date_header": False,  # Performance: reduce header size
        }
        
        # Production-specific optimizations
        if settings.environment == "production":
            uvicorn_config.update({
                "workers": settings.workers,
                "loop": "uvloop",  # High-performance event loop
                "http": "httptools",  # High-performance HTTP parser
                "lifespan": "on",
                "backlog": 2048,  # TCP backlog size
                "limit_concurrency": 10000,  # Max concurrent connections
                "limit_max_requests": 1000000,  # Max requests per worker
                "timeout_keep_alive": 5,  # Keep-alive timeout
            })
        else:
            # Development mode
            uvicorn_config.update({
                "reload": True,
                "reload_dirs": ["backend"],
                "log_level": "debug",
            })
        
        # Start server
        logger.info(f"🌐 Starting server on {settings.host}:{settings.port}")
        uvicorn.run(**uvicorn_config)
        
    except Exception as e:
        logger.error(f"❌ Failed to start application: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()