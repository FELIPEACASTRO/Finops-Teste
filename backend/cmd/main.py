#!/usr/bin/env python3
"""
FinOps-Teste Main Application Entry Point

This is the main entry point for the FinOps-Teste application.
It initializes the FastAPI application with all dependencies,
middleware, and routes following Clean Architecture principles.

Usage:
    python backend/cmd/main.py
    
Environment Variables:
    See .env.example for all configuration options
"""

import asyncio
import sys
from pathlib import Path

# Add backend to Python path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from api_server import create_app
from internal.infra.config import get_settings
from internal.observability.logger import get_logger, setup_logging
from internal.observability.metrics import setup_metrics
from internal.observability.tracer import setup_tracing


async def main():
    """Main application entry point"""
    
    # Load configuration
    settings = get_settings()
    
    # Setup observability
    setup_logging()
    setup_metrics()
    setup_tracing()
    
    logger = get_logger(__name__)
    logger.info("Starting FinOps-Teste application", extra={
        "version": settings.app.app_version,
        "environment": settings.app.environment.value
    })
    
    # Create FastAPI application
    app = await create_app()
    
    # Start server
    import uvicorn
    
    config = uvicorn.Config(
        app,
        host=settings.api.host,
        port=settings.api.port,
        workers=settings.api.workers if not settings.app.debug else 1,
        log_level=settings.monitoring.log_level.lower(),
        reload=settings.app.debug,
        access_log=True,
        use_colors=True,
    )
    
    server = uvicorn.Server(config)
    
    logger.info(f"Server starting on {settings.api.host}:{settings.api.port}")
    
    try:
        await server.serve()
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)
    finally:
        logger.info("Server shutdown complete")


if __name__ == "__main__":
    asyncio.run(main())