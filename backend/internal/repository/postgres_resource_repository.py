"""
PostgreSQL Resource Repository Implementation

This module implements the ResourceRepository interface using PostgreSQL
as the persistence layer. Follows Clean Architecture principles by
implementing the repository interface defined in the domain layer.

Features:
- Full CRUD operations for cloud resources
- Efficient querying with proper indexing
- Transaction support for data consistency
- Error handling and logging
- Connection pooling for performance
"""

from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID

import asyncpg
from asyncpg import Record

from ..domain.entities import CloudResource, ResourceRepository, ResourceType
from ..infra.database import DatabaseManager, DatabaseRepository
from ..observability.logger import get_logger


class PostgresResourceRepository(DatabaseRepository, ResourceRepository):
    """PostgreSQL implementation of ResourceRepository"""
    
    def __init__(self, db_manager: DatabaseManager):
        super().__init__(db_manager)
        self.logger = get_logger(__name__)
    
    async def save(self, resource: CloudResource) -> None:
        """Save a cloud resource to the database"""
        try:
            query = """
                INSERT INTO cloud_resources (
                    id, resource_id, resource_type, name, region, 
                    account_id, tags, created_at, updated_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                ON CONFLICT (resource_id, account_id) 
                DO UPDATE SET
                    resource_type = EXCLUDED.resource_type,
                    name = EXCLUDED.name,
                    region = EXCLUDED.region,
                    tags = EXCLUDED.tags,
                    updated_at = EXCLUDED.updated_at
            """
            
            await self.execute_query(
                query,
                resource.id,
                resource.resource_id,
                resource.resource_type.value,
                resource.name,
                resource.region,
                resource.account_id,
                resource.tags,
                resource.created_at,
                resource.updated_at
            )
            
            self.logger.debug(f"Resource saved successfully: {resource.id}")
            
        except Exception as e:
            self.logger.error(f"Failed to save resource {resource.id}: {e}")
            raise
    
    async def find_by_id(self, resource_id: UUID) -> Optional[CloudResource]:
        """Find resource by ID"""
        try:
            query = """
                SELECT id, resource_id, resource_type, name, region,
                       account_id, tags, created_at, updated_at
                FROM cloud_resources
                WHERE id = $1
            """
            
            record = await self.execute_query(query, resource_id, fetch_one=True)
            
            if record:
                return self._record_to_resource(record)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to find resource by ID {resource_id}: {e}")
            raise
    
    async def find_by_resource_id(self, resource_id: str, account_id: str) -> Optional[CloudResource]:
        """Find resource by cloud resource ID and account ID"""
        try:
            query = """
                SELECT id, resource_id, resource_type, name, region,
                       account_id, tags, created_at, updated_at
                FROM cloud_resources
                WHERE resource_id = $1 AND account_id = $2
            """
            
            record = await self.execute_query(query, resource_id, account_id, fetch_one=True)
            
            if record:
                return self._record_to_resource(record)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to find resource by resource_id {resource_id}: {e}")
            raise
    
    async def find_by_type(self, resource_type: ResourceType) -> List[CloudResource]:
        """Find resources by type"""
        try:
            query = """
                SELECT id, resource_id, resource_type, name, region,
                       account_id, tags, created_at, updated_at
                FROM cloud_resources
                WHERE resource_type = $1
                ORDER BY created_at DESC
            """
            
            records = await self.execute_query(query, resource_type.value, fetch_all=True)
            
            return [self._record_to_resource(record) for record in records]
            
        except Exception as e:
            self.logger.error(f"Failed to find resources by type {resource_type}: {e}")
            raise
    
    async def find_by_cost_center(self, cost_center: str) -> List[CloudResource]:
        """Find resources by cost center"""
        try:
            query = """
                SELECT id, resource_id, resource_type, name, region,
                       account_id, tags, created_at, updated_at
                FROM cloud_resources
                WHERE tags->>'CostCenter' = $1
                ORDER BY created_at DESC
            """
            
            records = await self.execute_query(query, cost_center, fetch_all=True)
            
            return [self._record_to_resource(record) for record in records]
            
        except Exception as e:
            self.logger.error(f"Failed to find resources by cost center {cost_center}: {e}")
            raise
    
    async def find_by_account(self, account_id: str) -> List[CloudResource]:
        """Find resources by account ID"""
        try:
            query = """
                SELECT id, resource_id, resource_type, name, region,
                       account_id, tags, created_at, updated_at
                FROM cloud_resources
                WHERE account_id = $1
                ORDER BY created_at DESC
            """
            
            records = await self.execute_query(query, account_id, fetch_all=True)
            
            return [self._record_to_resource(record) for record in records]
            
        except Exception as e:
            self.logger.error(f"Failed to find resources by account {account_id}: {e}")
            raise
    
    async def find_by_region(self, region: str) -> List[CloudResource]:
        """Find resources by region"""
        try:
            query = """
                SELECT id, resource_id, resource_type, name, region,
                       account_id, tags, created_at, updated_at
                FROM cloud_resources
                WHERE region = $1
                ORDER BY created_at DESC
            """
            
            records = await self.execute_query(query, region, fetch_all=True)
            
            return [self._record_to_resource(record) for record in records]
            
        except Exception as e:
            self.logger.error(f"Failed to find resources by region {region}: {e}")
            raise
    
    async def find_by_tags(self, tags: Dict[str, str]) -> List[CloudResource]:
        """Find resources by tags"""
        try:
            # Build dynamic query for tag matching
            conditions = []
            params = []
            param_count = 1
            
            for key, value in tags.items():
                conditions.append(f"tags->>%{param_count} = ${param_count + 1}")
                params.extend([key, value])
                param_count += 2
            
            where_clause = " AND ".join(conditions)
            
            query = f"""
                SELECT id, resource_id, resource_type, name, region,
                       account_id, tags, created_at, updated_at
                FROM cloud_resources
                WHERE {where_clause}
                ORDER BY created_at DESC
            """
            
            records = await self.execute_query(query, *params, fetch_all=True)
            
            return [self._record_to_resource(record) for record in records]
            
        except Exception as e:
            self.logger.error(f"Failed to find resources by tags {tags}: {e}")
            raise
    
    async def find_production_resources(self) -> List[CloudResource]:
        """Find all production resources"""
        try:
            query = """
                SELECT id, resource_id, resource_type, name, region,
                       account_id, tags, created_at, updated_at
                FROM cloud_resources
                WHERE LOWER(tags->>'Environment') IN ('prod', 'production')
                ORDER BY created_at DESC
            """
            
            records = await self.execute_query(query, fetch_all=True)
            
            return [self._record_to_resource(record) for record in records]
            
        except Exception as e:
            self.logger.error(f"Failed to find production resources: {e}")
            raise
    
    async def search_resources(
        self,
        search_term: str,
        resource_type: Optional[ResourceType] = None,
        account_id: Optional[str] = None,
        limit: int = 100
    ) -> List[CloudResource]:
        """Search resources by name or resource_id"""
        try:
            conditions = ["(name ILIKE $1 OR resource_id ILIKE $1)"]
            params = [f"%{search_term}%"]
            param_count = 2
            
            if resource_type:
                conditions.append(f"resource_type = ${param_count}")
                params.append(resource_type.value)
                param_count += 1
            
            if account_id:
                conditions.append(f"account_id = ${param_count}")
                params.append(account_id)
                param_count += 1
            
            where_clause = " AND ".join(conditions)
            
            query = f"""
                SELECT id, resource_id, resource_type, name, region,
                       account_id, tags, created_at, updated_at
                FROM cloud_resources
                WHERE {where_clause}
                ORDER BY 
                    CASE WHEN name ILIKE $1 THEN 1 ELSE 2 END,
                    created_at DESC
                LIMIT ${param_count}
            """
            
            params.append(limit)
            records = await self.execute_query(query, *params, fetch_all=True)
            
            return [self._record_to_resource(record) for record in records]
            
        except Exception as e:
            self.logger.error(f"Failed to search resources with term '{search_term}': {e}")
            raise
    
    async def count_by_type(self) -> Dict[ResourceType, int]:
        """Count resources by type"""
        try:
            query = """
                SELECT resource_type, COUNT(*) as count
                FROM cloud_resources
                GROUP BY resource_type
            """
            
            records = await self.execute_query(query, fetch_all=True)
            
            result = {}
            for record in records:
                resource_type = ResourceType(record['resource_type'])
                result[resource_type] = record['count']
            
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to count resources by type: {e}")
            raise
    
    async def count_by_cost_center(self) -> Dict[str, int]:
        """Count resources by cost center"""
        try:
            query = """
                SELECT tags->>'CostCenter' as cost_center, COUNT(*) as count
                FROM cloud_resources
                WHERE tags->>'CostCenter' IS NOT NULL
                GROUP BY tags->>'CostCenter'
                ORDER BY count DESC
            """
            
            records = await self.execute_query(query, fetch_all=True)
            
            result = {}
            for record in records:
                cost_center = record['cost_center']
                result[cost_center] = record['count']
            
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to count resources by cost center: {e}")
            raise
    
    async def delete(self, resource_id: UUID) -> bool:
        """Delete a resource"""
        try:
            query = "DELETE FROM cloud_resources WHERE id = $1"
            result = await self.execute_query(query, resource_id)
            
            # Check if any rows were affected
            deleted = result.split()[-1] == "1" if result else False
            
            if deleted:
                self.logger.debug(f"Resource deleted successfully: {resource_id}")
            else:
                self.logger.warning(f"Resource not found for deletion: {resource_id}")
            
            return deleted
            
        except Exception as e:
            self.logger.error(f"Failed to delete resource {resource_id}: {e}")
            raise
    
    async def bulk_save(self, resources: List[CloudResource]) -> None:
        """Bulk save multiple resources in a transaction"""
        if not resources:
            return
        
        try:
            operations = []
            
            for resource in resources:
                operations.append({
                    "query": """
                        INSERT INTO cloud_resources (
                            id, resource_id, resource_type, name, region, 
                            account_id, tags, created_at, updated_at
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                        ON CONFLICT (resource_id, account_id) 
                        DO UPDATE SET
                            resource_type = EXCLUDED.resource_type,
                            name = EXCLUDED.name,
                            region = EXCLUDED.region,
                            tags = EXCLUDED.tags,
                            updated_at = EXCLUDED.updated_at
                    """,
                    "args": [
                        resource.id,
                        resource.resource_id,
                        resource.resource_type.value,
                        resource.name,
                        resource.region,
                        resource.account_id,
                        resource.tags,
                        resource.created_at,
                        resource.updated_at
                    ]
                })
            
            await self.execute_transaction(operations)
            
            self.logger.info(f"Bulk saved {len(resources)} resources successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to bulk save {len(resources)} resources: {e}")
            raise
    
    async def get_resource_stats(self) -> Dict[str, any]:
        """Get resource statistics"""
        try:
            query = """
                SELECT 
                    COUNT(*) as total_resources,
                    COUNT(DISTINCT account_id) as total_accounts,
                    COUNT(DISTINCT region) as total_regions,
                    COUNT(DISTINCT tags->>'CostCenter') as total_cost_centers,
                    MIN(created_at) as oldest_resource,
                    MAX(created_at) as newest_resource
                FROM cloud_resources
            """
            
            record = await self.execute_query(query, fetch_one=True)
            
            if record:
                return {
                    "total_resources": record['total_resources'],
                    "total_accounts": record['total_accounts'],
                    "total_regions": record['total_regions'],
                    "total_cost_centers": record['total_cost_centers'],
                    "oldest_resource": record['oldest_resource'],
                    "newest_resource": record['newest_resource']
                }
            
            return {}
            
        except Exception as e:
            self.logger.error(f"Failed to get resource stats: {e}")
            raise
    
    def _record_to_resource(self, record: Record) -> CloudResource:
        """Convert database record to CloudResource entity"""
        return CloudResource(
            id=record['id'],
            resource_id=record['resource_id'],
            resource_type=ResourceType(record['resource_type']),
            name=record['name'],
            region=record['region'],
            account_id=record['account_id'],
            tags=record['tags'] or {},
            created_at=record['created_at'],
            updated_at=record['updated_at']
        )