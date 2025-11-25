"""
PostgreSQL Budget Repository Implementation

This module implements the BudgetRepository interface using PostgreSQL
as the persistence layer. Handles budget management with efficient
querying and alert management.

Features:
- CRUD operations for budgets
- Time-based querying and filtering
- Budget utilization calculations
- Alert threshold management
- Bulk operations for performance
"""

from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional
from uuid import UUID

from asyncpg import Record

from ..domain.entities import Budget, BudgetRepository, Money, TimeRange
from ..infra.database import DatabaseManager, DatabaseRepository
from ..observability.logger import get_logger


class PostgresBudgetRepository(DatabaseRepository, BudgetRepository):
    """PostgreSQL implementation of BudgetRepository"""
    
    def __init__(self, db_manager: DatabaseManager):
        super().__init__(db_manager)
        self.logger = get_logger(__name__)
    
    async def save(self, budget: Budget) -> None:
        """Save a budget to the database"""
        try:
            query = """
                INSERT INTO budgets (
                    id, name, amount, currency, spent, cost_center,
                    time_start, time_end, alert_thresholds, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                ON CONFLICT (id) 
                DO UPDATE SET
                    name = EXCLUDED.name,
                    amount = EXCLUDED.amount,
                    currency = EXCLUDED.currency,
                    spent = EXCLUDED.spent,
                    cost_center = EXCLUDED.cost_center,
                    time_start = EXCLUDED.time_start,
                    time_end = EXCLUDED.time_end,
                    alert_thresholds = EXCLUDED.alert_thresholds
            """
            
            await self.execute_query(
                query,
                budget.id,
                budget.name,
                budget.amount.amount,
                budget.amount.currency,
                budget.spent.amount,
                budget.cost_center,
                budget.time_range.start,
                budget.time_range.end,
                budget.alert_thresholds,
                budget.created_at
            )
            
            self.logger.debug(f"Budget saved successfully: {budget.id}")
            
        except Exception as e:
            self.logger.error(f"Failed to save budget {budget.id}: {e}")
            raise
    
    async def find_by_id(self, budget_id: UUID) -> Optional[Budget]:
        """Find budget by ID"""
        try:
            query = """
                SELECT id, name, amount, currency, spent, cost_center,
                       time_start, time_end, alert_thresholds, created_at
                FROM budgets
                WHERE id = $1
            """
            
            record = await self.execute_query(query, budget_id, fetch_one=True)
            
            if record:
                return self._record_to_budget(record)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to find budget by ID {budget_id}: {e}")
            raise
    
    async def find_by_cost_center(self, cost_center: str) -> List[Budget]:
        """Find budgets by cost center"""
        try:
            query = """
                SELECT id, name, amount, currency, spent, cost_center,
                       time_start, time_end, alert_thresholds, created_at
                FROM budgets
                WHERE cost_center = $1
                ORDER BY created_at DESC
            """
            
            records = await self.execute_query(query, cost_center, fetch_all=True)
            
            return [self._record_to_budget(record) for record in records]
            
        except Exception as e:
            self.logger.error(f"Failed to find budgets by cost center {cost_center}: {e}")
            raise
    
    async def find_active(self, current_time: Optional[datetime] = None) -> List[Budget]:
        """Find all active budgets"""
        if current_time is None:
            current_time = datetime.utcnow()
        
        try:
            query = """
                SELECT id, name, amount, currency, spent, cost_center,
                       time_start, time_end, alert_thresholds, created_at
                FROM budgets
                WHERE time_start <= $1 AND time_end >= $1
                ORDER BY created_at DESC
            """
            
            records = await self.execute_query(query, current_time, fetch_all=True)
            
            return [self._record_to_budget(record) for record in records]
            
        except Exception as e:
            self.logger.error(f"Failed to find active budgets: {e}")
            raise
    
    async def find_by_time_range(self, time_range: TimeRange) -> List[Budget]:
        """Find budgets that overlap with given time range"""
        try:
            query = """
                SELECT id, name, amount, currency, spent, cost_center,
                       time_start, time_end, alert_thresholds, created_at
                FROM budgets
                WHERE (time_start <= $2 AND time_end >= $1)
                ORDER BY created_at DESC
            """
            
            records = await self.execute_query(
                query, time_range.start, time_range.end, fetch_all=True
            )
            
            return [self._record_to_budget(record) for record in records]
            
        except Exception as e:
            self.logger.error(f"Failed to find budgets by time range: {e}")
            raise
    
    async def find_over_threshold(self, threshold: float) -> List[Budget]:
        """Find budgets that exceed utilization threshold"""
        try:
            query = """
                SELECT id, name, amount, currency, spent, cost_center,
                       time_start, time_end, alert_thresholds, created_at
                FROM budgets
                WHERE (spent / NULLIF(amount, 0)) >= $1
                ORDER BY (spent / NULLIF(amount, 0)) DESC
            """
            
            records = await self.execute_query(query, threshold, fetch_all=True)
            
            return [self._record_to_budget(record) for record in records]
            
        except Exception as e:
            self.logger.error(f"Failed to find budgets over threshold {threshold}: {e}")
            raise
    
    async def find_expiring_soon(self, days: int = 7) -> List[Budget]:
        """Find budgets expiring within specified days"""
        try:
            query = """
                SELECT id, name, amount, currency, spent, cost_center,
                       time_start, time_end, alert_thresholds, created_at
                FROM budgets
                WHERE time_end <= NOW() + INTERVAL '%s days'
                  AND time_end > NOW()
                ORDER BY time_end ASC
            """ % days
            
            records = await self.execute_query(query, fetch_all=True)
            
            return [self._record_to_budget(record) for record in records]
            
        except Exception as e:
            self.logger.error(f"Failed to find expiring budgets: {e}")
            raise
    
    async def update_spent_amount(self, budget_id: UUID, spent_amount: Money) -> bool:
        """Update spent amount for a budget"""
        try:
            query = """
                UPDATE budgets
                SET spent = $2, currency = $3
                WHERE id = $1
            """
            
            result = await self.execute_query(
                query, budget_id, spent_amount.amount, spent_amount.currency
            )
            
            updated = result.split()[-1] == "1" if result else False
            
            if updated:
                self.logger.debug(f"Budget spent amount updated: {budget_id}")
            else:
                self.logger.warning(f"Budget not found for spent update: {budget_id}")
            
            return updated
            
        except Exception as e:
            self.logger.error(f"Failed to update spent amount for budget {budget_id}: {e}")
            raise
    
    async def get_budget_utilization_stats(
        self,
        cost_center: Optional[str] = None
    ) -> Dict[str, any]:
        """Get budget utilization statistics"""
        try:
            conditions = []
            params = []
            param_count = 1
            
            if cost_center:
                conditions.append(f"cost_center = ${param_count}")
                params.append(cost_center)
                param_count += 1
            
            where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
            
            query = f"""
                SELECT 
                    COUNT(*) as total_budgets,
                    SUM(amount) as total_allocated,
                    SUM(spent) as total_spent,
                    AVG(spent / NULLIF(amount, 0)) as avg_utilization,
                    COUNT(CASE WHEN (spent / NULLIF(amount, 0)) >= 1.0 THEN 1 END) as over_budget_count,
                    COUNT(CASE WHEN (spent / NULLIF(amount, 0)) >= 0.8 THEN 1 END) as warning_count,
                    currency
                FROM budgets
                {where_clause}
                GROUP BY currency
            """
            
            records = await self.execute_query(query, *params, fetch_all=True)
            
            if records:
                record = records[0]  # Assuming single currency
                return {
                    "total_budgets": record['total_budgets'],
                    "total_allocated": float(record['total_allocated']) if record['total_allocated'] else 0,
                    "total_spent": float(record['total_spent']) if record['total_spent'] else 0,
                    "avg_utilization": float(record['avg_utilization']) if record['avg_utilization'] else 0,
                    "over_budget_count": record['over_budget_count'],
                    "warning_count": record['warning_count'],
                    "currency": record['currency'],
                    "utilization_percentage": (
                        float(record['total_spent']) / float(record['total_allocated']) * 100
                        if record['total_allocated'] and record['total_allocated'] > 0 else 0
                    )
                }
            
            return {}
            
        except Exception as e:
            self.logger.error(f"Failed to get budget utilization stats: {e}")
            raise
    
    async def get_budget_alerts(self) -> List[Dict]:
        """Get budgets that have exceeded their alert thresholds"""
        try:
            query = """
                SELECT 
                    id,
                    name,
                    cost_center,
                    amount,
                    spent,
                    currency,
                    alert_thresholds,
                    (spent / NULLIF(amount, 0)) as utilization_ratio
                FROM budgets
                WHERE spent / NULLIF(amount, 0) >= ANY(alert_thresholds)
                  AND time_end >= NOW()
                ORDER BY utilization_ratio DESC
            """
            
            records = await self.execute_query(query, fetch_all=True)
            
            alerts = []
            for record in records:
                utilization_ratio = float(record['utilization_ratio']) if record['utilization_ratio'] else 0
                
                # Find which thresholds have been exceeded
                exceeded_thresholds = [
                    threshold for threshold in record['alert_thresholds']
                    if utilization_ratio >= threshold
                ]
                
                for threshold in exceeded_thresholds:
                    severity = self._get_alert_severity(threshold)
                    
                    alerts.append({
                        "budget_id": record['id'],
                        "budget_name": record['name'],
                        "cost_center": record['cost_center'],
                        "threshold": threshold,
                        "utilization": utilization_ratio * 100,
                        "severity": severity,
                        "amount": float(record['amount']),
                        "spent": float(record['spent']),
                        "currency": record['currency']
                    })
            
            return alerts
            
        except Exception as e:
            self.logger.error(f"Failed to get budget alerts: {e}")
            raise
    
    async def get_budget_forecast(
        self,
        budget_id: UUID,
        days_ahead: int = 30
    ) -> Optional[Dict]:
        """Get budget forecast based on current spending trend"""
        try:
            # Get budget details
            budget = await self.find_by_id(budget_id)
            if not budget:
                return None
            
            # Calculate spending rate (amount per day)
            elapsed_days = (datetime.utcnow() - budget.time_range.start).days
            if elapsed_days <= 0:
                return None
            
            daily_spend_rate = budget.spent.amount / elapsed_days
            
            # Project future spending
            projected_spend = daily_spend_rate * days_ahead
            projected_total = budget.spent.amount + projected_spend
            
            # Calculate end-of-period projection
            total_days = (budget.time_range.end - budget.time_range.start).days
            remaining_days = (budget.time_range.end - datetime.utcnow()).days
            
            if remaining_days > 0:
                projected_end_total = budget.spent.amount + (daily_spend_rate * remaining_days)
            else:
                projected_end_total = budget.spent.amount
            
            return {
                "budget_id": budget_id,
                "current_spent": float(budget.spent.amount),
                "budget_amount": float(budget.amount.amount),
                "current_utilization": budget.utilization_percentage,
                "daily_spend_rate": float(daily_spend_rate),
                "projected_spend_next_period": float(projected_spend),
                "projected_total_next_period": float(projected_total),
                "projected_end_total": float(projected_end_total),
                "projected_end_utilization": (
                    float(projected_end_total) / float(budget.amount.amount) * 100
                    if budget.amount.amount > 0 else 0
                ),
                "days_ahead": days_ahead,
                "remaining_days": max(0, remaining_days),
                "currency": budget.amount.currency
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get budget forecast for {budget_id}: {e}")
            raise
    
    async def bulk_update_spent_amounts(self, updates: List[Dict]) -> int:
        """Bulk update spent amounts for multiple budgets"""
        if not updates:
            return 0
        
        try:
            operations = []
            
            for update in updates:
                operations.append({
                    "query": """
                        UPDATE budgets
                        SET spent = $2
                        WHERE id = $1
                    """,
                    "args": [update["budget_id"], update["spent_amount"]]
                })
            
            await self.execute_transaction(operations)
            
            self.logger.info(f"Bulk updated spent amounts for {len(updates)} budgets")
            
            return len(updates)
            
        except Exception as e:
            self.logger.error(f"Failed to bulk update spent amounts: {e}")
            raise
    
    async def delete(self, budget_id: UUID) -> bool:
        """Delete a budget"""
        try:
            query = "DELETE FROM budgets WHERE id = $1"
            result = await self.execute_query(query, budget_id)
            
            deleted = result.split()[-1] == "1" if result else False
            
            if deleted:
                self.logger.debug(f"Budget deleted successfully: {budget_id}")
            else:
                self.logger.warning(f"Budget not found for deletion: {budget_id}")
            
            return deleted
            
        except Exception as e:
            self.logger.error(f"Failed to delete budget {budget_id}: {e}")
            raise
    
    async def cleanup_expired_budgets(self, days: int = 365) -> int:
        """Delete expired budgets older than specified days"""
        try:
            query = """
                DELETE FROM budgets
                WHERE time_end < NOW() - INTERVAL '%s days'
            """ % days
            
            result = await self.execute_query(query)
            
            deleted_count = int(result.split()[-1]) if result else 0
            
            if deleted_count > 0:
                self.logger.info(f"Cleaned up {deleted_count} expired budgets")
            
            return deleted_count
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup expired budgets: {e}")
            raise
    
    async def get_cost_center_summary(self) -> List[Dict]:
        """Get budget summary by cost center"""
        try:
            query = """
                SELECT 
                    cost_center,
                    COUNT(*) as budget_count,
                    SUM(amount) as total_allocated,
                    SUM(spent) as total_spent,
                    AVG(spent / NULLIF(amount, 0)) as avg_utilization,
                    currency
                FROM budgets
                WHERE time_end >= NOW()
                GROUP BY cost_center, currency
                ORDER BY total_allocated DESC
            """
            
            records = await self.execute_query(query, fetch_all=True)
            
            return [
                {
                    "cost_center": record['cost_center'],
                    "budget_count": record['budget_count'],
                    "total_allocated": float(record['total_allocated']),
                    "total_spent": float(record['total_spent']),
                    "avg_utilization": float(record['avg_utilization']) if record['avg_utilization'] else 0,
                    "utilization_percentage": (
                        float(record['total_spent']) / float(record['total_allocated']) * 100
                        if record['total_allocated'] and record['total_allocated'] > 0 else 0
                    ),
                    "currency": record['currency']
                }
                for record in records
            ]
            
        except Exception as e:
            self.logger.error(f"Failed to get cost center summary: {e}")
            raise
    
    def _record_to_budget(self, record: Record) -> Budget:
        """Convert database record to Budget entity"""
        return Budget(
            id=record['id'],
            name=record['name'],
            amount=Money(record['amount'], record['currency']),
            spent=Money(record['spent'], record['currency']),
            time_range=TimeRange(record['time_start'], record['time_end']),
            cost_center=record['cost_center'],
            alert_thresholds=list(record['alert_thresholds']) if record['alert_thresholds'] else [0.8, 0.9, 1.0],
            created_at=record['created_at']
        )
    
    def _get_alert_severity(self, threshold: float) -> str:
        """Get alert severity based on threshold"""
        if threshold >= 1.0:
            return "critical"
        elif threshold >= 0.9:
            return "high"
        elif threshold >= 0.8:
            return "medium"
        else:
            return "low"