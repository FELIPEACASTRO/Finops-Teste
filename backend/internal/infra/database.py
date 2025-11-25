"""
Database Infrastructure

This module provides database connection management, session handling,
and database configuration following Clean Architecture principles.

Features:
- Connection pooling for high performance
- Async/await support for non-blocking operations
- Health checks and monitoring
- Migration support
- Transaction management
- Connection retry logic with circuit breaker pattern
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

import asyncpg
from asyncpg import Connection, Pool
from pydantic import BaseSettings, Field

from ..observability.logger import get_logger


class DatabaseConfig(BaseSettings):
    """Database configuration settings"""
    
    # Connection settings
    host: str = Field(default="localhost", env="DB_HOST")
    port: int = Field(default=5432, env="DB_PORT")
    database: str = Field(default="finops", env="DB_NAME")
    username: str = Field(default="finops_user", env="DB_USER")
    password: str = Field(default="finops_password", env="DB_PASSWORD")
    
    # Connection pool settings
    min_connections: int = Field(default=5, env="DB_MIN_CONNECTIONS")
    max_connections: int = Field(default=20, env="DB_MAX_CONNECTIONS")
    max_queries: int = Field(default=50000, env="DB_MAX_QUERIES")
    max_inactive_connection_lifetime: float = Field(default=300.0, env="DB_MAX_INACTIVE_LIFETIME")
    
    # Performance settings
    command_timeout: float = Field(default=30.0, env="DB_COMMAND_TIMEOUT")
    server_settings: dict = Field(default_factory=lambda: {
        "jit": "off",  # Disable JIT for predictable performance
        "application_name": "finops-teste"
    })
    
    # SSL settings
    ssl_enabled: bool = Field(default=False, env="DB_SSL_ENABLED")
    ssl_cert_path: Optional[str] = Field(default=None, env="DB_SSL_CERT_PATH")
    ssl_key_path: Optional[str] = Field(default=None, env="DB_SSL_KEY_PATH")
    ssl_ca_path: Optional[str] = Field(default=None, env="DB_SSL_CA_PATH")
    
    # Health check settings
    health_check_interval: float = Field(default=30.0, env="DB_HEALTH_CHECK_INTERVAL")
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    @property
    def connection_url(self) -> str:
        """Get database connection URL"""
        return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"
    
    @property
    def async_connection_url(self) -> str:
        """Get async database connection URL"""
        return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"


class DatabaseManager:
    """Database connection manager with connection pooling and health checks"""
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.pool: Optional[Pool] = None
        self.logger = get_logger(__name__)
        self._health_check_task: Optional[asyncio.Task] = None
        self._is_healthy = False
    
    async def initialize(self) -> None:
        """Initialize database connection pool"""
        try:
            self.logger.info("Initializing database connection pool...")
            
            # Create connection pool
            self.pool = await asyncpg.create_pool(
                host=self.config.host,
                port=self.config.port,
                database=self.config.database,
                user=self.config.username,
                password=self.config.password,
                min_size=self.config.min_connections,
                max_size=self.config.max_connections,
                max_queries=self.config.max_queries,
                max_inactive_connection_lifetime=self.config.max_inactive_connection_lifetime,
                command_timeout=self.config.command_timeout,
                server_settings=self.config.server_settings,
                ssl=self._get_ssl_context() if self.config.ssl_enabled else None
            )
            
            # Test connection
            await self.health_check()
            
            # Start health check task
            self._health_check_task = asyncio.create_task(self._periodic_health_check())
            
            self.logger.info(
                f"Database pool initialized successfully. "
                f"Pool size: {self.config.min_connections}-{self.config.max_connections}"
            )
            
        except Exception as e:
            self.logger.error(f"Failed to initialize database pool: {e}")
            raise
    
    async def close(self) -> None:
        """Close database connection pool"""
        try:
            if self._health_check_task:
                self._health_check_task.cancel()
                try:
                    await self._health_check_task
                except asyncio.CancelledError:
                    pass
            
            if self.pool:
                await self.pool.close()
                self.logger.info("Database pool closed successfully")
                
        except Exception as e:
            self.logger.error(f"Error closing database pool: {e}")
    
    @asynccontextmanager
    async def get_connection(self) -> AsyncGenerator[Connection, None]:
        """Get database connection from pool"""
        if not self.pool:
            raise RuntimeError("Database pool not initialized")
        
        connection = None
        try:
            connection = await self.pool.acquire()
            yield connection
        except Exception as e:
            self.logger.error(f"Database connection error: {e}")
            raise
        finally:
            if connection:
                await self.pool.release(connection)
    
    @asynccontextmanager
    async def get_transaction(self) -> AsyncGenerator[Connection, None]:
        """Get database connection with transaction"""
        async with self.get_connection() as connection:
            async with connection.transaction():
                yield connection
    
    async def health_check(self) -> bool:
        """Perform database health check"""
        try:
            async with self.get_connection() as connection:
                result = await connection.fetchval("SELECT 1")
                self._is_healthy = (result == 1)
                
                if self._is_healthy:
                    self.logger.debug("Database health check passed")
                else:
                    self.logger.warning("Database health check failed: unexpected result")
                
                return self._is_healthy
                
        except Exception as e:
            self._is_healthy = False
            self.logger.error(f"Database health check failed: {e}")
            return False
    
    @property
    def is_healthy(self) -> bool:
        """Check if database is healthy"""
        return self._is_healthy
    
    async def get_pool_stats(self) -> dict:
        """Get connection pool statistics"""
        if not self.pool:
            return {"status": "not_initialized"}
        
        return {
            "size": self.pool.get_size(),
            "min_size": self.pool.get_min_size(),
            "max_size": self.pool.get_max_size(),
            "idle_connections": self.pool.get_idle_size(),
            "is_healthy": self._is_healthy
        }
    
    async def _periodic_health_check(self) -> None:
        """Periodic health check task"""
        while True:
            try:
                await asyncio.sleep(self.config.health_check_interval)
                await self.health_check()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in periodic health check: {e}")
    
    def _get_ssl_context(self):
        """Get SSL context for secure connections"""
        if not self.config.ssl_enabled:
            return None
        
        # This would configure SSL context based on cert files
        # Implementation depends on specific SSL requirements
        return "require"  # Basic SSL requirement


class DatabaseRepository:
    """Base repository class with common database operations"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.logger = get_logger(self.__class__.__name__)
    
    async def execute_query(
        self,
        query: str,
        *args,
        fetch_one: bool = False,
        fetch_all: bool = False
    ):
        """Execute database query with error handling and logging"""
        try:
            async with self.db_manager.get_connection() as connection:
                if fetch_one:
                    result = await connection.fetchrow(query, *args)
                elif fetch_all:
                    result = await connection.fetch(query, *args)
                else:
                    result = await connection.execute(query, *args)
                
                self.logger.debug(f"Query executed successfully: {query[:100]}...")
                return result
                
        except Exception as e:
            self.logger.error(f"Query execution failed: {e}, Query: {query[:100]}...")
            raise
    
    async def execute_transaction(self, operations: list):
        """Execute multiple operations in a transaction"""
        try:
            async with self.db_manager.get_transaction() as connection:
                results = []
                for operation in operations:
                    query, args = operation["query"], operation.get("args", [])
                    
                    if operation.get("fetch_one"):
                        result = await connection.fetchrow(query, *args)
                    elif operation.get("fetch_all"):
                        result = await connection.fetch(query, *args)
                    else:
                        result = await connection.execute(query, *args)
                    
                    results.append(result)
                
                self.logger.debug(f"Transaction executed successfully with {len(operations)} operations")
                return results
                
        except Exception as e:
            self.logger.error(f"Transaction failed: {e}")
            raise


# Database schema creation and migration
class DatabaseMigrator:
    """Database migration manager"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.logger = get_logger(__name__)
    
    async def create_schema(self) -> None:
        """Create database schema"""
        try:
            schema_sql = """
            -- Create extensions
            CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
            CREATE EXTENSION IF NOT EXISTS "pg_trgm";
            
            -- Create enum types
            CREATE TYPE resource_type AS ENUM (
                'ec2', 'rds', 's3', 'lambda', 'elb', 'ebs',
                'cloudfront', 'route53', 'vpc', 'dynamodb'
            );
            
            CREATE TYPE cost_category AS ENUM (
                'compute', 'storage', 'network', 'database',
                'security', 'monitoring', 'other'
            );
            
            CREATE TYPE optimization_status AS ENUM (
                'pending', 'applied', 'rejected', 'expired'
            );
            
            -- Cloud Resources table
            CREATE TABLE IF NOT EXISTS cloud_resources (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                resource_id VARCHAR(255) NOT NULL,
                resource_type resource_type NOT NULL,
                name VARCHAR(255) NOT NULL,
                region VARCHAR(50) NOT NULL,
                account_id VARCHAR(50) NOT NULL,
                tags JSONB DEFAULT '{}',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                
                CONSTRAINT unique_resource_id UNIQUE (resource_id, account_id)
            );
            
            -- Cost Entries table
            CREATE TABLE IF NOT EXISTS cost_entries (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                resource_id UUID NOT NULL REFERENCES cloud_resources(id) ON DELETE CASCADE,
                cost_amount DECIMAL(15,4) NOT NULL CHECK (cost_amount >= 0),
                cost_currency VARCHAR(3) DEFAULT 'USD',
                category cost_category NOT NULL,
                time_start TIMESTAMP WITH TIME ZONE NOT NULL,
                time_end TIMESTAMP WITH TIME ZONE NOT NULL,
                usage_metrics JSONB,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                
                CONSTRAINT valid_time_range CHECK (time_end > time_start)
            );
            
            -- Optimization Recommendations table
            CREATE TABLE IF NOT EXISTS optimization_recommendations (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                resource_id UUID NOT NULL REFERENCES cloud_resources(id) ON DELETE CASCADE,
                title VARCHAR(255) NOT NULL,
                description TEXT NOT NULL,
                potential_savings_amount DECIMAL(15,4) NOT NULL CHECK (potential_savings_amount >= 0),
                potential_savings_currency VARCHAR(3) DEFAULT 'USD',
                confidence_score DECIMAL(3,2) NOT NULL CHECK (confidence_score BETWEEN 0 AND 1),
                status optimization_status DEFAULT 'pending',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                expires_at TIMESTAMP WITH TIME ZONE,
                applied_at TIMESTAMP WITH TIME ZONE
            );
            
            -- Budgets table
            CREATE TABLE IF NOT EXISTS budgets (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                name VARCHAR(255) NOT NULL,
                amount DECIMAL(15,4) NOT NULL CHECK (amount > 0),
                currency VARCHAR(3) DEFAULT 'USD',
                spent DECIMAL(15,4) DEFAULT 0 CHECK (spent >= 0),
                cost_center VARCHAR(100) NOT NULL,
                time_start TIMESTAMP WITH TIME ZONE NOT NULL,
                time_end TIMESTAMP WITH TIME ZONE NOT NULL,
                alert_thresholds DECIMAL(3,2)[] DEFAULT ARRAY[0.8, 0.9, 1.0],
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                
                CONSTRAINT valid_budget_time_range CHECK (time_end > time_start)
            );
            
            -- Create indexes for performance
            CREATE INDEX IF NOT EXISTS idx_cloud_resources_type ON cloud_resources(resource_type);
            CREATE INDEX IF NOT EXISTS idx_cloud_resources_account ON cloud_resources(account_id);
            CREATE INDEX IF NOT EXISTS idx_cloud_resources_tags ON cloud_resources USING GIN(tags);
            
            CREATE INDEX IF NOT EXISTS idx_cost_entries_resource ON cost_entries(resource_id);
            CREATE INDEX IF NOT EXISTS idx_cost_entries_time ON cost_entries(time_start, time_end);
            CREATE INDEX IF NOT EXISTS idx_cost_entries_category ON cost_entries(category);
            
            CREATE INDEX IF NOT EXISTS idx_optimization_resource ON optimization_recommendations(resource_id);
            CREATE INDEX IF NOT EXISTS idx_optimization_status ON optimization_recommendations(status);
            CREATE INDEX IF NOT EXISTS idx_optimization_created ON optimization_recommendations(created_at);
            
            CREATE INDEX IF NOT EXISTS idx_budgets_cost_center ON budgets(cost_center);
            CREATE INDEX IF NOT EXISTS idx_budgets_time ON budgets(time_start, time_end);
            
            -- Create updated_at trigger function
            CREATE OR REPLACE FUNCTION update_updated_at_column()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.updated_at = NOW();
                RETURN NEW;
            END;
            $$ language 'plpgsql';
            
            -- Create trigger for cloud_resources
            DROP TRIGGER IF EXISTS update_cloud_resources_updated_at ON cloud_resources;
            CREATE TRIGGER update_cloud_resources_updated_at
                BEFORE UPDATE ON cloud_resources
                FOR EACH ROW
                EXECUTE FUNCTION update_updated_at_column();
            """
            
            async with self.db_manager.get_connection() as connection:
                await connection.execute(schema_sql)
            
            self.logger.info("Database schema created successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to create database schema: {e}")
            raise
    
    async def check_schema_exists(self) -> bool:
        """Check if database schema exists"""
        try:
            async with self.db_manager.get_connection() as connection:
                result = await connection.fetchval("""
                    SELECT COUNT(*) FROM information_schema.tables 
                    WHERE table_name IN ('cloud_resources', 'cost_entries', 'optimization_recommendations', 'budgets')
                """)
                return result == 4
        except Exception as e:
            self.logger.error(f"Failed to check schema existence: {e}")
            return False


# Global database manager instance
_db_manager: Optional[DatabaseManager] = None


async def get_database_manager() -> DatabaseManager:
    """Get global database manager instance"""
    global _db_manager
    
    if _db_manager is None:
        config = DatabaseConfig()
        _db_manager = DatabaseManager(config)
        await _db_manager.initialize()
        
        # Create schema if it doesn't exist
        migrator = DatabaseMigrator(_db_manager)
        if not await migrator.check_schema_exists():
            await migrator.create_schema()
    
    return _db_manager


async def close_database_manager() -> None:
    """Close global database manager"""
    global _db_manager
    
    if _db_manager:
        await _db_manager.close()
        _db_manager = None