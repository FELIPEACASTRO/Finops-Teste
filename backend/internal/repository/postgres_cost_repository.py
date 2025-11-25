"""
PostgreSQL Cost Repository Implementation

This module implements the CostRepository interface using PostgreSQL
as the persistence layer. Handles cost entries with efficient querying
and aggregation capabilities.

Features:
- CRUD operations for cost entries
- Time-based querying with proper indexing
- Aggregation functions for cost analysis
- Bulk operations for performance
- Transaction support for data consistency
"""

from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional
from uuid import UUID

from asyncpg import Record

from ..domain.entities import (
    CostCategory,
    CostEntry,
    CostRepository,
    Money,
    ResourceMetrics,
    TimeRange,
)
from ..infra.database import DatabaseManager, DatabaseRepository
from ..observability.logger import get_logger


class PostgresCostRepository(DatabaseRepository, CostRepository):
    """PostgreSQL implementation of CostRepository"""
    
    def __init__(self, db_manager: DatabaseManager):
        super().__init__(db_manager)
        self.logger = get_logger(__name__)
    
    async def save(self, cost_entry: CostEntry) -> None:
        """Save a cost entry to the database"""
        try:
            query = """
                INSERT INTO cost_entries (
                    id, resource_id, cost_amount, cost_currency, category,
                    time_start, time_end, usage_metrics, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                ON CONFLICT (id) 
                DO UPDATE SET
                    cost_amount = EXCLUDED.cost_amount,
                    cost_currency = EXCLUDED.cost_currency,
                    category = EXCLUDED.category,
                    time_start = EXCLUDED.time_start,
                    time_end = EXCLUDED.time_end,
                    usage_metrics = EXCLUDED.usage_metrics
            """
            
            usage_metrics_json = None
            if cost_entry.usage_metrics:
                usage_metrics_json = {
                    "cpu_utilization": cost_entry.usage_metrics.cpu_utilization,
                    "memory_utilization": cost_entry.usage_metrics.memory_utilization,
                    "network_in": cost_entry.usage_metrics.network_in,
                    "network_out": cost_entry.usage_metrics.network_out,
                    "storage_utilization": cost_entry.usage_metrics.storage_utilization
                }
            
            await self.execute_query(
                query,
                cost_entry.id,
                cost_entry.resource_id,
                cost_entry.cost.amount,
                cost_entry.cost.currency,
                cost_entry.category.value,
                cost_entry.time_range.start,
                cost_entry.time_range.end,
                usage_metrics_json,
                cost_entry.created_at
            )
            
            self.logger.debug(f"Cost entry saved successfully: {cost_entry.id}")
            
        except Exception as e:
            self.logger.error(f"Failed to save cost entry {cost_entry.id}: {e}")
            raise
    
    async def find_by_id(self, cost_entry_id: UUID) -> Optional[CostEntry]:
        """Find cost entry by ID"""
        try:
            query = """
                SELECT id, resource_id, cost_amount, cost_currency, category,
                       time_start, time_end, usage_metrics, created_at
                FROM cost_entries
                WHERE id = $1
            """
            
            record = await self.execute_query(query, cost_entry_id, fetch_one=True)
            
            if record:
                return self._record_to_cost_entry(record)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to find cost entry by ID {cost_entry_id}: {e}")
            raise
    
    async def find_by_resource(self, resource_id: UUID) -> List[CostEntry]:
        """Find cost entries for a resource"""
        try:
            query = """
                SELECT id, resource_id, cost_amount, cost_currency, category,
                       time_start, time_end, usage_metrics, created_at
                FROM cost_entries
                WHERE resource_id = $1
                ORDER BY time_start DESC
            """
            
            records = await self.execute_query(query, resource_id, fetch_all=True)
            
            return [self._record_to_cost_entry(record) for record in records]
            
        except Exception as e:
            self.logger.error(f"Failed to find cost entries for resource {resource_id}: {e}")
            raise
    
    async def find_by_time_range(self, time_range: TimeRange) -> List[CostEntry]:
        """Find cost entries within time range"""
        try:
            query = """
                SELECT id, resource_id, cost_amount, cost_currency, category,
                       time_start, time_end, usage_metrics, created_at
                FROM cost_entries
                WHERE time_start >= $1 AND time_end <= $2
                ORDER BY time_start DESC
            """
            
            records = await self.execute_query(
                query, time_range.start, time_range.end, fetch_all=True
            )
            
            return [self._record_to_cost_entry(record) for record in records]
            
        except Exception as e:
            self.logger.error(f"Failed to find cost entries by time range: {e}")
            raise
    
    async def find_by_cost_center(self, cost_center: str, time_range: TimeRange) -> List[CostEntry]:
        """Find cost entries by cost center and time range"""
        try:
            query = """
                SELECT ce.id, ce.resource_id, ce.cost_amount, ce.cost_currency, ce.category,
                       ce.time_start, ce.time_end, ce.usage_metrics, ce.created_at
                FROM cost_entries ce
                JOIN cloud_resources cr ON ce.resource_id = cr.id
                WHERE cr.tags->>'CostCenter' = $1
                  AND ce.time_start >= $2 
                  AND ce.time_end <= $3
                ORDER BY ce.time_start DESC
            """
            
            records = await self.execute_query(
                query, cost_center, time_range.start, time_range.end, fetch_all=True
            )
            
            return [self._record_to_cost_entry(record) for record in records]
            
        except Exception as e:
            self.logger.error(f"Failed to find cost entries by cost center {cost_center}: {e}")
            raise
    
    async def find_by_category(self, category: CostCategory, time_range: TimeRange) -> List[CostEntry]:
        """Find cost entries by category and time range"""
        try:
            query = """
                SELECT id, resource_id, cost_amount, cost_currency, category,
                       time_start, time_end, usage_metrics, created_at
                FROM cost_entries
                WHERE category = $1
                  AND time_start >= $2 
                  AND time_end <= $3
                ORDER BY time_start DESC
            """
            
            records = await self.execute_query(
                query, category.value, time_range.start, time_range.end, fetch_all=True
            )
            
            return [self._record_to_cost_entry(record) for record in records]
            
        except Exception as e:
            self.logger.error(f"Failed to find cost entries by category {category}: {e}")
            raise
    
    async def get_total_cost_by_resource(
        self, 
        resource_ids: List[UUID], 
        time_range: TimeRange
    ) -> Dict[UUID, Money]:
        """Get total cost by resource for given time range"""
        try:
            if not resource_ids:
                return {}
            
            # Create placeholders for resource IDs
            placeholders = ",".join(f"${i+1}" for i in range(len(resource_ids)))
            
            query = f"""
                SELECT resource_id, 
                       SUM(cost_amount) as total_amount,
                       cost_currency
                FROM cost_entries
                WHERE resource_id IN ({placeholders})
                  AND time_start >= ${len(resource_ids)+1}
                  AND time_end <= ${len(resource_ids)+2}
                GROUP BY resource_id, cost_currency
            """
            
            params = list(resource_ids) + [time_range.start, time_range.end]
            records = await self.execute_query(query, *params, fetch_all=True)
            
            result = {}
            for record in records:
                resource_id = record['resource_id']
                amount = record['total_amount']
                currency = record['cost_currency']
                result[resource_id] = Money(amount, currency)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to get total cost by resource: {e}")
            raise
    
    async def get_total_cost_by_category(self, time_range: TimeRange) -> Dict[CostCategory, Money]:
        """Get total cost by category for given time range"""
        try:
            query = """
                SELECT category, 
                       SUM(cost_amount) as total_amount,
                       cost_currency
                FROM cost_entries
                WHERE time_start >= $1 AND time_end <= $2
                GROUP BY category, cost_currency
            """
            
            records = await self.execute_query(
                query, time_range.start, time_range.end, fetch_all=True
            )
            
            result = {}
            for record in records:
                category = CostCategory(record['category'])
                amount = record['total_amount']
                currency = record['cost_currency']
                
                if category in result:
                    # Add to existing amount (assuming same currency)
                    result[category] = result[category].add(Money(amount, currency))
                else:
                    result[category] = Money(amount, currency)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to get total cost by category: {e}")
            raise
    
    async def get_cost_trend_data(
        self, 
        resource_id: Optional[UUID] = None,
        cost_center: Optional[str] = None,
        time_range: Optional[TimeRange] = None,
        interval: str = "day"
    ) -> List[Dict]:
        """Get cost trend data aggregated by time interval"""
        try:
            # Build dynamic query based on parameters
            conditions = []
            params = []
            param_count = 1
            
            if resource_id:
                conditions.append(f"ce.resource_id = ${param_count}")
                params.append(resource_id)
                param_count += 1
            
            if cost_center:
                conditions.append(f"cr.tags->>'CostCenter' = ${param_count}")
                params.append(cost_center)
                param_count += 1
            
            if time_range:
                conditions.append(f"ce.time_start >= ${param_count}")
                params.append(time_range.start)
                param_count += 1
                conditions.append(f"ce.time_end <= ${param_count}")
                params.append(time_range.end)
                param_count += 1
            
            where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
            
            # Determine date truncation based on interval
            date_trunc = {
                "hour": "hour",
                "day": "day", 
                "week": "week",
                "month": "month"
            }.get(interval, "day")
            
            query = f"""
                SELECT 
                    DATE_TRUNC('{date_trunc}', ce.time_start) as period,
                    SUM(ce.cost_amount) as total_cost,
                    ce.cost_currency,
                    COUNT(*) as entry_count
                FROM cost_entries ce
                LEFT JOIN cloud_resources cr ON ce.resource_id = cr.id
                {where_clause}
                GROUP BY DATE_TRUNC('{date_trunc}', ce.time_start), ce.cost_currency
                ORDER BY period ASC
            """
            
            records = await self.execute_query(query, *params, fetch_all=True)
            
            return [
                {
                    "period": record['period'],
                    "total_cost": float(record['total_cost']),
                    "currency": record['cost_currency'],
                    "entry_count": record['entry_count']
                }
                for record in records
            ]
            
        except Exception as e:
            self.logger.error(f"Failed to get cost trend data: {e}")
            raise
    
    async def get_top_cost_resources(
        self, 
        time_range: TimeRange, 
        limit: int = 10
    ) -> List[Dict]:
        """Get top cost resources for given time range"""
        try:
            query = """
                SELECT 
                    ce.resource_id,
                    cr.name as resource_name,
                    cr.resource_type,
                    cr.tags->>'CostCenter' as cost_center,
                    SUM(ce.cost_amount) as total_cost,
                    ce.cost_currency,
                    COUNT(*) as entry_count
                FROM cost_entries ce
                JOIN cloud_resources cr ON ce.resource_id = cr.id
                WHERE ce.time_start >= $1 AND ce.time_end <= $2
                GROUP BY ce.resource_id, cr.name, cr.resource_type, 
                         cr.tags->>'CostCenter', ce.cost_currency
                ORDER BY total_cost DESC
                LIMIT $3
            """
            
            records = await self.execute_query(
                query, time_range.start, time_range.end, limit, fetch_all=True
            )
            
            return [
                {
                    "resource_id": record['resource_id'],
                    "resource_name": record['resource_name'],
                    "resource_type": record['resource_type'],
                    "cost_center": record['cost_center'],
                    "total_cost": float(record['total_cost']),
                    "currency": record['cost_currency'],
                    "entry_count": record['entry_count']
                }
                for record in records
            ]
            
        except Exception as e:
            self.logger.error(f"Failed to get top cost resources: {e}")
            raise
    
    async def bulk_save(self, cost_entries: List[CostEntry]) -> None:
        """Bulk save multiple cost entries in a transaction"""
        if not cost_entries:
            return
        
        try:
            operations = []
            
            for cost_entry in cost_entries:
                usage_metrics_json = None
                if cost_entry.usage_metrics:
                    usage_metrics_json = {
                        "cpu_utilization": cost_entry.usage_metrics.cpu_utilization,
                        "memory_utilization": cost_entry.usage_metrics.memory_utilization,
                        "network_in": cost_entry.usage_metrics.network_in,
                        "network_out": cost_entry.usage_metrics.network_out,
                        "storage_utilization": cost_entry.usage_metrics.storage_utilization
                    }
                
                operations.append({
                    "query": """
                        INSERT INTO cost_entries (
                            id, resource_id, cost_amount, cost_currency, category,
                            time_start, time_end, usage_metrics, created_at
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                        ON CONFLICT (id) 
                        DO UPDATE SET
                            cost_amount = EXCLUDED.cost_amount,
                            cost_currency = EXCLUDED.cost_currency,
                            category = EXCLUDED.category,
                            time_start = EXCLUDED.time_start,
                            time_end = EXCLUDED.time_end,
                            usage_metrics = EXCLUDED.usage_metrics
                    """,
                    "args": [
                        cost_entry.id,
                        cost_entry.resource_id,
                        cost_entry.cost.amount,
                        cost_entry.cost.currency,
                        cost_entry.category.value,
                        cost_entry.time_range.start,
                        cost_entry.time_range.end,
                        usage_metrics_json,
                        cost_entry.created_at
                    ]
                })
            
            await self.execute_transaction(operations)
            
            self.logger.info(f"Bulk saved {len(cost_entries)} cost entries successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to bulk save {len(cost_entries)} cost entries: {e}")
            raise
    
    async def delete_by_resource(self, resource_id: UUID) -> int:
        """Delete all cost entries for a resource"""
        try:
            query = "DELETE FROM cost_entries WHERE resource_id = $1"
            result = await self.execute_query(query, resource_id)
            
            # Extract number of deleted rows from result
            deleted_count = int(result.split()[-1]) if result else 0
            
            self.logger.debug(f"Deleted {deleted_count} cost entries for resource {resource_id}")
            
            return deleted_count
            
        except Exception as e:
            self.logger.error(f"Failed to delete cost entries for resource {resource_id}: {e}")
            raise
    
    async def delete_by_time_range(self, time_range: TimeRange) -> int:
        """Delete cost entries within time range"""
        try:
            query = """
                DELETE FROM cost_entries 
                WHERE time_start >= $1 AND time_end <= $2
            """
            
            result = await self.execute_query(query, time_range.start, time_range.end)
            
            deleted_count = int(result.split()[-1]) if result else 0
            
            self.logger.debug(f"Deleted {deleted_count} cost entries in time range")
            
            return deleted_count
            
        except Exception as e:
            self.logger.error(f"Failed to delete cost entries by time range: {e}")
            raise
    
    async def get_cost_statistics(self, time_range: TimeRange) -> Dict[str, any]:
        """Get cost statistics for given time range"""
        try:
            query = """
                SELECT 
                    COUNT(*) as total_entries,
                    SUM(cost_amount) as total_cost,
                    AVG(cost_amount) as average_cost,
                    MIN(cost_amount) as min_cost,
                    MAX(cost_amount) as max_cost,
                    COUNT(DISTINCT resource_id) as unique_resources,
                    COUNT(DISTINCT category) as unique_categories,
                    cost_currency
                FROM cost_entries
                WHERE time_start >= $1 AND time_end <= $2
                GROUP BY cost_currency
            """
            
            records = await self.execute_query(
                query, time_range.start, time_range.end, fetch_all=True
            )
            
            if records:
                # Assuming single currency for simplicity
                record = records[0]
                return {
                    "total_entries": record['total_entries'],
                    "total_cost": float(record['total_cost']) if record['total_cost'] else 0,
                    "average_cost": float(record['average_cost']) if record['average_cost'] else 0,
                    "min_cost": float(record['min_cost']) if record['min_cost'] else 0,
                    "max_cost": float(record['max_cost']) if record['max_cost'] else 0,
                    "unique_resources": record['unique_resources'],
                    "unique_categories": record['unique_categories'],
                    "currency": record['cost_currency']
                }
            
            return {}
            
        except Exception as e:
            self.logger.error(f"Failed to get cost statistics: {e}")
            raise
    
    def _record_to_cost_entry(self, record: Record) -> CostEntry:
        """Convert database record to CostEntry entity"""
        usage_metrics = None
        if record['usage_metrics']:
            metrics_data = record['usage_metrics']
            usage_metrics = ResourceMetrics(
                cpu_utilization=metrics_data.get('cpu_utilization', 0.0),
                memory_utilization=metrics_data.get('memory_utilization', 0.0),
                network_in=metrics_data.get('network_in', 0.0),
                network_out=metrics_data.get('network_out', 0.0),
                storage_utilization=metrics_data.get('storage_utilization', 0.0)
            )
        
        return CostEntry(
            id=record['id'],
            resource_id=record['resource_id'],
            cost=Money(record['cost_amount'], record['cost_currency']),
            category=CostCategory(record['category']),
            time_range=TimeRange(record['time_start'], record['time_end']),
            usage_metrics=usage_metrics,
            created_at=record['created_at']
        )