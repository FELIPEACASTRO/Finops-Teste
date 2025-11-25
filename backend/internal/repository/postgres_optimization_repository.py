"""
PostgreSQL Optimization Repository Implementation

This module implements the OptimizationRepository interface using PostgreSQL
as the persistence layer. Handles optimization recommendations with
efficient querying and status management.

Features:
- CRUD operations for optimization recommendations
- Status-based querying and filtering
- Bulk operations for performance
- Expiration handling and cleanup
- Analytics and reporting functions
"""

from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional
from uuid import UUID

from asyncpg import Record

from ..domain.entities import (
    Money,
    OptimizationRecommendation,
    OptimizationRepository,
    OptimizationStatus,
)
from ..infra.database import DatabaseManager, DatabaseRepository
from ..observability.logger import get_logger


class PostgresOptimizationRepository(DatabaseRepository, OptimizationRepository):
    """PostgreSQL implementation of OptimizationRepository"""
    
    def __init__(self, db_manager: DatabaseManager):
        super().__init__(db_manager)
        self.logger = get_logger(__name__)
    
    async def save(self, recommendation: OptimizationRecommendation) -> None:
        """Save an optimization recommendation to the database"""
        try:
            query = """
                INSERT INTO optimization_recommendations (
                    id, resource_id, title, description, potential_savings_amount,
                    potential_savings_currency, confidence_score, status,
                    created_at, expires_at, applied_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                ON CONFLICT (id) 
                DO UPDATE SET
                    title = EXCLUDED.title,
                    description = EXCLUDED.description,
                    potential_savings_amount = EXCLUDED.potential_savings_amount,
                    potential_savings_currency = EXCLUDED.potential_savings_currency,
                    confidence_score = EXCLUDED.confidence_score,
                    status = EXCLUDED.status,
                    expires_at = EXCLUDED.expires_at,
                    applied_at = EXCLUDED.applied_at
            """
            
            applied_at = None
            if recommendation.status == OptimizationStatus.APPLIED:
                applied_at = datetime.utcnow()
            
            await self.execute_query(
                query,
                recommendation.id,
                recommendation.resource_id,
                recommendation.title,
                recommendation.description,
                recommendation.potential_savings.amount,
                recommendation.potential_savings.currency,
                recommendation.confidence_score,
                recommendation.status.value,
                recommendation.created_at,
                recommendation.expires_at,
                applied_at
            )
            
            self.logger.debug(f"Optimization recommendation saved successfully: {recommendation.id}")
            
        except Exception as e:
            self.logger.error(f"Failed to save optimization recommendation {recommendation.id}: {e}")
            raise
    
    async def find_by_id(self, recommendation_id: UUID) -> Optional[OptimizationRecommendation]:
        """Find optimization recommendation by ID"""
        try:
            query = """
                SELECT id, resource_id, title, description, potential_savings_amount,
                       potential_savings_currency, confidence_score, status,
                       created_at, expires_at, applied_at
                FROM optimization_recommendations
                WHERE id = $1
            """
            
            record = await self.execute_query(query, recommendation_id, fetch_one=True)
            
            if record:
                return self._record_to_recommendation(record)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to find optimization recommendation by ID {recommendation_id}: {e}")
            raise
    
    async def find_pending(self) -> List[OptimizationRecommendation]:
        """Find all pending recommendations"""
        try:
            query = """
                SELECT id, resource_id, title, description, potential_savings_amount,
                       potential_savings_currency, confidence_score, status,
                       created_at, expires_at, applied_at
                FROM optimization_recommendations
                WHERE status = 'pending'
                  AND (expires_at IS NULL OR expires_at > NOW())
                ORDER BY potential_savings_amount DESC, created_at DESC
            """
            
            records = await self.execute_query(query, fetch_all=True)
            
            return [self._record_to_recommendation(record) for record in records]
            
        except Exception as e:
            self.logger.error(f"Failed to find pending recommendations: {e}")
            raise
    
    async def find_by_resource(self, resource_id: UUID) -> List[OptimizationRecommendation]:
        """Find recommendations for a resource"""
        try:
            query = """
                SELECT id, resource_id, title, description, potential_savings_amount,
                       potential_savings_currency, confidence_score, status,
                       created_at, expires_at, applied_at
                FROM optimization_recommendations
                WHERE resource_id = $1
                ORDER BY created_at DESC
            """
            
            records = await self.execute_query(query, resource_id, fetch_all=True)
            
            return [self._record_to_recommendation(record) for record in records]
            
        except Exception as e:
            self.logger.error(f"Failed to find recommendations for resource {resource_id}: {e}")
            raise
    
    async def find_by_status(self, status: OptimizationStatus) -> List[OptimizationRecommendation]:
        """Find recommendations by status"""
        try:
            query = """
                SELECT id, resource_id, title, description, potential_savings_amount,
                       potential_savings_currency, confidence_score, status,
                       created_at, expires_at, applied_at
                FROM optimization_recommendations
                WHERE status = $1
                ORDER BY created_at DESC
            """
            
            records = await self.execute_query(query, status.value, fetch_all=True)
            
            return [self._record_to_recommendation(record) for record in records]
            
        except Exception as e:
            self.logger.error(f"Failed to find recommendations by status {status}: {e}")
            raise
    
    async def find_by_cost_center(self, cost_center: str) -> List[OptimizationRecommendation]:
        """Find recommendations by cost center"""
        try:
            query = """
                SELECT or.id, or.resource_id, or.title, or.description, 
                       or.potential_savings_amount, or.potential_savings_currency,
                       or.confidence_score, or.status, or.created_at, 
                       or.expires_at, or.applied_at
                FROM optimization_recommendations or
                JOIN cloud_resources cr ON or.resource_id = cr.id
                WHERE cr.tags->>'CostCenter' = $1
                ORDER BY or.potential_savings_amount DESC, or.created_at DESC
            """
            
            records = await self.execute_query(query, cost_center, fetch_all=True)
            
            return [self._record_to_recommendation(record) for record in records]
            
        except Exception as e:
            self.logger.error(f"Failed to find recommendations by cost center {cost_center}: {e}")
            raise
    
    async def find_high_impact(self, min_savings: Money) -> List[OptimizationRecommendation]:
        """Find high impact recommendations above savings threshold"""
        try:
            query = """
                SELECT id, resource_id, title, description, potential_savings_amount,
                       potential_savings_currency, confidence_score, status,
                       created_at, expires_at, applied_at
                FROM optimization_recommendations
                WHERE potential_savings_amount >= $1
                  AND potential_savings_currency = $2
                  AND status = 'pending'
                  AND (expires_at IS NULL OR expires_at > NOW())
                ORDER BY potential_savings_amount DESC, confidence_score DESC
            """
            
            records = await self.execute_query(
                query, min_savings.amount, min_savings.currency, fetch_all=True
            )
            
            return [self._record_to_recommendation(record) for record in records]
            
        except Exception as e:
            self.logger.error(f"Failed to find high impact recommendations: {e}")
            raise
    
    async def find_expiring_soon(self, hours: int = 24) -> List[OptimizationRecommendation]:
        """Find recommendations expiring within specified hours"""
        try:
            query = """
                SELECT id, resource_id, title, description, potential_savings_amount,
                       potential_savings_currency, confidence_score, status,
                       created_at, expires_at, applied_at
                FROM optimization_recommendations
                WHERE status = 'pending'
                  AND expires_at IS NOT NULL
                  AND expires_at <= NOW() + INTERVAL '%s hours'
                  AND expires_at > NOW()
                ORDER BY expires_at ASC
            """ % hours
            
            records = await self.execute_query(query, fetch_all=True)
            
            return [self._record_to_recommendation(record) for record in records]
            
        except Exception as e:
            self.logger.error(f"Failed to find expiring recommendations: {e}")
            raise
    
    async def mark_as_applied(self, recommendation_id: UUID) -> bool:
        """Mark recommendation as applied"""
        try:
            query = """
                UPDATE optimization_recommendations
                SET status = 'applied', applied_at = NOW()
                WHERE id = $1 AND status = 'pending'
            """
            
            result = await self.execute_query(query, recommendation_id)
            
            # Check if any rows were updated
            updated = result.split()[-1] == "1" if result else False
            
            if updated:
                self.logger.debug(f"Recommendation marked as applied: {recommendation_id}")
            else:
                self.logger.warning(f"Recommendation not found or not pending: {recommendation_id}")
            
            return updated
            
        except Exception as e:
            self.logger.error(f"Failed to mark recommendation as applied {recommendation_id}: {e}")
            raise
    
    async def mark_as_rejected(self, recommendation_id: UUID, reason: Optional[str] = None) -> bool:
        """Mark recommendation as rejected"""
        try:
            query = """
                UPDATE optimization_recommendations
                SET status = 'rejected'
                WHERE id = $1 AND status = 'pending'
            """
            
            result = await self.execute_query(query, recommendation_id)
            
            updated = result.split()[-1] == "1" if result else False
            
            if updated:
                self.logger.debug(f"Recommendation marked as rejected: {recommendation_id}")
                # Could store rejection reason in a separate table or field
            else:
                self.logger.warning(f"Recommendation not found or not pending: {recommendation_id}")
            
            return updated
            
        except Exception as e:
            self.logger.error(f"Failed to mark recommendation as rejected {recommendation_id}: {e}")
            raise
    
    async def expire_old_recommendations(self) -> int:
        """Mark expired recommendations as expired"""
        try:
            query = """
                UPDATE optimization_recommendations
                SET status = 'expired'
                WHERE status = 'pending'
                  AND expires_at IS NOT NULL
                  AND expires_at <= NOW()
            """
            
            result = await self.execute_query(query)
            
            expired_count = int(result.split()[-1]) if result else 0
            
            if expired_count > 0:
                self.logger.info(f"Marked {expired_count} recommendations as expired")
            
            return expired_count
            
        except Exception as e:
            self.logger.error(f"Failed to expire old recommendations: {e}")
            raise
    
    async def get_recommendations_summary(
        self,
        cost_center: Optional[str] = None
    ) -> Dict[str, any]:
        """Get summary statistics for recommendations"""
        try:
            conditions = []
            params = []
            param_count = 1
            
            if cost_center:
                conditions.append(f"cr.tags->>'CostCenter' = ${param_count}")
                params.append(cost_center)
                param_count += 1
            
            join_clause = "LEFT JOIN cloud_resources cr ON or.resource_id = cr.id" if cost_center else ""
            where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
            
            query = f"""
                SELECT 
                    COUNT(*) as total_recommendations,
                    COUNT(CASE WHEN or.status = 'pending' THEN 1 END) as pending_count,
                    COUNT(CASE WHEN or.status = 'applied' THEN 1 END) as applied_count,
                    COUNT(CASE WHEN or.status = 'rejected' THEN 1 END) as rejected_count,
                    COUNT(CASE WHEN or.status = 'expired' THEN 1 END) as expired_count,
                    SUM(CASE WHEN or.status = 'pending' THEN or.potential_savings_amount ELSE 0 END) as pending_savings,
                    SUM(CASE WHEN or.status = 'applied' THEN or.potential_savings_amount ELSE 0 END) as realized_savings,
                    AVG(or.confidence_score) as avg_confidence,
                    or.potential_savings_currency
                FROM optimization_recommendations or
                {join_clause}
                {where_clause}
                GROUP BY or.potential_savings_currency
            """
            
            records = await self.execute_query(query, *params, fetch_all=True)
            
            if records:
                record = records[0]  # Assuming single currency
                return {
                    "total_recommendations": record['total_recommendations'],
                    "pending_count": record['pending_count'],
                    "applied_count": record['applied_count'],
                    "rejected_count": record['rejected_count'],
                    "expired_count": record['expired_count'],
                    "pending_savings": float(record['pending_savings']) if record['pending_savings'] else 0,
                    "realized_savings": float(record['realized_savings']) if record['realized_savings'] else 0,
                    "avg_confidence": float(record['avg_confidence']) if record['avg_confidence'] else 0,
                    "currency": record['potential_savings_currency'],
                    "application_rate": (
                        record['applied_count'] / record['total_recommendations'] * 100
                        if record['total_recommendations'] > 0 else 0
                    )
                }
            
            return {}
            
        except Exception as e:
            self.logger.error(f"Failed to get recommendations summary: {e}")
            raise
    
    async def get_top_recommendations_by_savings(
        self,
        limit: int = 10,
        status: Optional[OptimizationStatus] = None
    ) -> List[Dict]:
        """Get top recommendations by potential savings"""
        try:
            conditions = []
            params = []
            param_count = 1
            
            if status:
                conditions.append(f"or.status = ${param_count}")
                params.append(status.value)
                param_count += 1
            
            where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
            
            query = f"""
                SELECT 
                    or.id,
                    or.resource_id,
                    cr.name as resource_name,
                    cr.resource_type,
                    or.title,
                    or.potential_savings_amount,
                    or.potential_savings_currency,
                    or.confidence_score,
                    or.status,
                    or.created_at
                FROM optimization_recommendations or
                JOIN cloud_resources cr ON or.resource_id = cr.id
                {where_clause}
                ORDER BY or.potential_savings_amount DESC
                LIMIT ${param_count}
            """
            
            params.append(limit)
            records = await self.execute_query(query, *params, fetch_all=True)
            
            return [
                {
                    "id": record['id'],
                    "resource_id": record['resource_id'],
                    "resource_name": record['resource_name'],
                    "resource_type": record['resource_type'],
                    "title": record['title'],
                    "potential_savings": float(record['potential_savings_amount']),
                    "currency": record['potential_savings_currency'],
                    "confidence_score": float(record['confidence_score']),
                    "status": record['status'],
                    "created_at": record['created_at']
                }
                for record in records
            ]
            
        except Exception as e:
            self.logger.error(f"Failed to get top recommendations by savings: {e}")
            raise
    
    async def bulk_save(self, recommendations: List[OptimizationRecommendation]) -> None:
        """Bulk save multiple recommendations in a transaction"""
        if not recommendations:
            return
        
        try:
            operations = []
            
            for recommendation in recommendations:
                applied_at = None
                if recommendation.status == OptimizationStatus.APPLIED:
                    applied_at = datetime.utcnow()
                
                operations.append({
                    "query": """
                        INSERT INTO optimization_recommendations (
                            id, resource_id, title, description, potential_savings_amount,
                            potential_savings_currency, confidence_score, status,
                            created_at, expires_at, applied_at
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                        ON CONFLICT (id) 
                        DO UPDATE SET
                            title = EXCLUDED.title,
                            description = EXCLUDED.description,
                            potential_savings_amount = EXCLUDED.potential_savings_amount,
                            potential_savings_currency = EXCLUDED.potential_savings_currency,
                            confidence_score = EXCLUDED.confidence_score,
                            status = EXCLUDED.status,
                            expires_at = EXCLUDED.expires_at,
                            applied_at = EXCLUDED.applied_at
                    """,
                    "args": [
                        recommendation.id,
                        recommendation.resource_id,
                        recommendation.title,
                        recommendation.description,
                        recommendation.potential_savings.amount,
                        recommendation.potential_savings.currency,
                        recommendation.confidence_score,
                        recommendation.status.value,
                        recommendation.created_at,
                        recommendation.expires_at,
                        applied_at
                    ]
                })
            
            await self.execute_transaction(operations)
            
            self.logger.info(f"Bulk saved {len(recommendations)} optimization recommendations successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to bulk save {len(recommendations)} recommendations: {e}")
            raise
    
    async def delete_by_resource(self, resource_id: UUID) -> int:
        """Delete all recommendations for a resource"""
        try:
            query = "DELETE FROM optimization_recommendations WHERE resource_id = $1"
            result = await self.execute_query(query, resource_id)
            
            deleted_count = int(result.split()[-1]) if result else 0
            
            self.logger.debug(f"Deleted {deleted_count} recommendations for resource {resource_id}")
            
            return deleted_count
            
        except Exception as e:
            self.logger.error(f"Failed to delete recommendations for resource {resource_id}: {e}")
            raise
    
    async def cleanup_old_recommendations(self, days: int = 90) -> int:
        """Delete old recommendations beyond specified days"""
        try:
            query = """
                DELETE FROM optimization_recommendations
                WHERE created_at < NOW() - INTERVAL '%s days'
                  AND status IN ('applied', 'rejected', 'expired')
            """ % days
            
            result = await self.execute_query(query)
            
            deleted_count = int(result.split()[-1]) if result else 0
            
            if deleted_count > 0:
                self.logger.info(f"Cleaned up {deleted_count} old recommendations")
            
            return deleted_count
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup old recommendations: {e}")
            raise
    
    def _record_to_recommendation(self, record: Record) -> OptimizationRecommendation:
        """Convert database record to OptimizationRecommendation entity"""
        return OptimizationRecommendation(
            id=record['id'],
            resource_id=record['resource_id'],
            title=record['title'],
            description=record['description'],
            potential_savings=Money(
                record['potential_savings_amount'],
                record['potential_savings_currency']
            ),
            confidence_score=float(record['confidence_score']),
            status=OptimizationStatus(record['status']),
            created_at=record['created_at'],
            expires_at=record['expires_at']
        )