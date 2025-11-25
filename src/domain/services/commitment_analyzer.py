"""
Commitment Analyzer Service
Analyzes Savings Plans and Reserved Instances opportunities
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class SavingsPlanRecommendation:
    """Recommendation for Savings Plans purchase"""
    commitment_type: str  # "Compute" or "EC2 Instance"
    payment_option: str  # "All Upfront", "Partial Upfront", "No Upfront"
    term_years: int  # 1 or 3
    hourly_commitment_usd: float
    estimated_savings_monthly: float
    estimated_savings_annual: float
    estimated_savings_percentage: float
    coverage_percentage: float
    current_on_demand_spend: float
    recommended_commitment_spend: float
    payback_months: float
    risk_level: str  # "LOW", "MEDIUM", "HIGH"
    priority: str  # "HIGH", "MEDIUM", "LOW"


@dataclass
class ReservedInstanceRecommendation:
    """Recommendation for Reserved Instance purchase"""
    instance_type: str
    region: str
    platform: str  # "Linux/UNIX", "Windows", etc.
    tenancy: str  # "default", "dedicated"
    offering_class: str  # "standard", "convertible"
    payment_option: str
    term_years: int
    instance_count: int
    upfront_cost: float
    monthly_cost: float
    estimated_savings_monthly: float
    estimated_savings_annual: float
    estimated_savings_percentage: float
    current_on_demand_cost: float
    payback_months: float
    utilization_expected: float  # 0.0 to 1.0
    risk_level: str
    priority: str


class CommitmentAnalyzer:
    """Analyzes commitment-based savings opportunities"""
    
    def __init__(self, ce_client, ec2_client):
        """
        Initialize Commitment Analyzer
        
        Args:
            ce_client: AWS Cost Explorer client
            ec2_client: AWS EC2 client
        """
        self.ce_client = ce_client
        self.ec2_client = ec2_client
        
    def analyze_savings_plans_opportunities(
        self,
        lookback_days: int = 30,
        min_savings_percentage: float = 10.0
    ) -> List[SavingsPlanRecommendation]:
        """
        Analyze Savings Plans purchase opportunities
        
        Args:
            lookback_days: Historical period to analyze
            min_savings_percentage: Minimum savings % to recommend
            
        Returns:
            List of Savings Plans recommendations
        """
        logger.info("Analyzing Savings Plans opportunities...")
        
        try:
            # Get Savings Plans recommendations from Cost Explorer
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=lookback_days)
            
            response = self.ce_client.get_savings_plans_purchase_recommendation(
                SavingsPlansType='COMPUTE_SP',  # or 'EC2_INSTANCE_SP'
                TermInYears='ONE_YEAR',
                PaymentOption='NO_UPFRONT',
                LookbackPeriodInDays=str(lookback_days)
            )
            
            recommendations = []
            
            for rec in response.get('SavingsPlansPurchaseRecommendation', {}).get('SavingsPlansPurchaseRecommendationDetails', []):
                savings_percentage = float(rec.get('EstimatedSavingsPercentage', 0))
                
                if savings_percentage < min_savings_percentage:
                    continue
                
                hourly_commitment = float(rec.get('HourlyCommitmentToPurchase', 0))
                monthly_savings = float(rec.get('EstimatedMonthlySavingsAmount', 0))
                annual_savings = monthly_savings * 12
                
                current_spend = float(rec.get('CurrentAverageHourlyOnDemandSpend', 0)) * 730  # hours/month
                commitment_spend = hourly_commitment * 730
                
                payback_months = (commitment_spend - current_spend) / monthly_savings if monthly_savings > 0 else 0
                
                # Determine risk level
                if savings_percentage > 30 and payback_months < 6:
                    risk_level = "LOW"
                    priority = "HIGH"
                elif savings_percentage > 20:
                    risk_level = "MEDIUM"
                    priority = "MEDIUM"
                else:
                    risk_level = "HIGH"
                    priority = "LOW"
                
                recommendation = SavingsPlanRecommendation(
                    commitment_type="Compute Savings Plan",
                    payment_option="No Upfront",
                    term_years=1,
                    hourly_commitment_usd=hourly_commitment,
                    estimated_savings_monthly=monthly_savings,
                    estimated_savings_annual=annual_savings,
                    estimated_savings_percentage=savings_percentage,
                    coverage_percentage=float(rec.get('EstimatedSPCost', 0)) / current_spend * 100 if current_spend > 0 else 0,
                    current_on_demand_spend=current_spend,
                    recommended_commitment_spend=commitment_spend,
                    payback_months=payback_months,
                    risk_level=risk_level,
                    priority=priority
                )
                
                recommendations.append(recommendation)
            
            logger.info(f"Found {len(recommendations)} Savings Plans opportunities")
            return recommendations
            
        except Exception as e:
            logger.error(f"Error analyzing Savings Plans: {e}")
            return []
    
    def analyze_reserved_instances_opportunities(
        self,
        region: str,
        lookback_days: int = 30,
        min_savings_percentage: float = 10.0
    ) -> List[ReservedInstanceRecommendation]:
        """
        Analyze Reserved Instance purchase opportunities
        
        Args:
            region: AWS region to analyze
            lookback_days: Historical period to analyze
            min_savings_percentage: Minimum savings % to recommend
            
        Returns:
            List of RI recommendations
        """
        logger.info(f"Analyzing Reserved Instance opportunities in {region}...")
        
        try:
            # Get RI recommendations from Cost Explorer
            response = self.ce_client.get_reservation_purchase_recommendation(
                Service='Amazon Elastic Compute Cloud - Compute',
                LookbackPeriodInDays=str(lookback_days),
                TermInYears='ONE_YEAR',
                PaymentOption='NO_UPFRONT'
            )
            
            recommendations = []
            
            for rec in response.get('Recommendations', []):
                details = rec.get('RecommendationDetails', [])
                
                for detail in details:
                    instance_details = detail.get('InstanceDetails', {}).get('EC2InstanceDetails', {})
                    
                    savings_percentage = float(detail.get('EstimatedSavingsPercentage', 0))
                    
                    if savings_percentage < min_savings_percentage:
                        continue
                    
                    monthly_savings = float(detail.get('EstimatedMonthlySavingsAmount', 0))
                    annual_savings = monthly_savings * 12
                    
                    upfront_cost = float(detail.get('UpfrontCost', 0))
                    monthly_cost = float(detail.get('EstimatedMonthlyOnDemandCost', 0))
                    
                    instance_count = int(detail.get('RecommendedNumberOfInstancesToPurchase', 1))
                    
                    payback_months = upfront_cost / monthly_savings if monthly_savings > 0 else 0
                    
                    # Determine risk and priority
                    if savings_percentage > 30 and payback_months < 6:
                        risk_level = "LOW"
                        priority = "HIGH"
                    elif savings_percentage > 20:
                        risk_level = "MEDIUM"
                        priority = "MEDIUM"
                    else:
                        risk_level = "HIGH"
                        priority = "LOW"
                    
                    recommendation = ReservedInstanceRecommendation(
                        instance_type=instance_details.get('InstanceType', 'unknown'),
                        region=instance_details.get('Region', region),
                        platform=instance_details.get('Platform', 'Linux/UNIX'),
                        tenancy=instance_details.get('Tenancy', 'default'),
                        offering_class='standard',
                        payment_option='No Upfront',
                        term_years=1,
                        instance_count=instance_count,
                        upfront_cost=upfront_cost,
                        monthly_cost=monthly_cost,
                        estimated_savings_monthly=monthly_savings,
                        estimated_savings_annual=annual_savings,
                        estimated_savings_percentage=savings_percentage,
                        current_on_demand_cost=monthly_cost + monthly_savings,
                        payback_months=payback_months,
                        utilization_expected=0.8,  # Assume 80% utilization
                        risk_level=risk_level,
                        priority=priority
                    )
                    
                    recommendations.append(recommendation)
            
            logger.info(f"Found {len(recommendations)} Reserved Instance opportunities")
            return recommendations
            
        except Exception as e:
            logger.error(f"Error analyzing Reserved Instances: {e}")
            return []
    
    def get_savings_plans_coverage(self, period_days: int = 30) -> Dict[str, Any]:
        """
        Get current Savings Plans coverage
        
        Args:
            period_days: Period to analyze
            
        Returns:
            Coverage metrics
        """
        try:
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=period_days)
            
            response = self.ce_client.get_savings_plans_coverage(
                TimePeriod={
                    'Start': start_date.isoformat(),
                    'End': end_date.isoformat()
                },
                Granularity='MONTHLY'
            )
            
            total_coverage = 0.0
            total_spend = 0.0
            
            for period in response.get('SavingsPlansCoverages', []):
                coverage = period.get('Coverage', {})
                coverage_pct = float(coverage.get('CoveragePercentage', 0))
                spend = float(coverage.get('SpendCoveredBySavingsPlans', 0))
                
                total_coverage += coverage_pct
                total_spend += spend
            
            periods = len(response.get('SavingsPlansCoverages', []))
            avg_coverage = total_coverage / periods if periods > 0 else 0.0
            
            return {
                'average_coverage_percentage': avg_coverage,
                'total_spend_covered': total_spend,
                'periods_analyzed': periods,
                'recommendation': 'INCREASE_COVERAGE' if avg_coverage < 70 else 'MAINTAIN'
            }
            
        except Exception as e:
            logger.error(f"Error getting Savings Plans coverage: {e}")
            return {
                'average_coverage_percentage': 0.0,
                'total_spend_covered': 0.0,
                'periods_analyzed': 0,
                'recommendation': 'UNKNOWN'
            }
    
    def get_reservation_utilization(self, period_days: int = 30) -> Dict[str, Any]:
        """
        Get Reserved Instance utilization
        
        Args:
            period_days: Period to analyze
            
        Returns:
            Utilization metrics
        """
        try:
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=period_days)
            
            response = self.ce_client.get_reservation_utilization(
                TimePeriod={
                    'Start': start_date.isoformat(),
                    'End': end_date.isoformat()
                },
                Granularity='MONTHLY'
            )
            
            total_utilization = 0.0
            periods = 0
            
            for period in response.get('UtilizationsByTime', []):
                utilization = period.get('Total', {}).get('UtilizationPercentage', 0)
                total_utilization += float(utilization)
                periods += 1
            
            avg_utilization = total_utilization / periods if periods > 0 else 0.0
            
            return {
                'average_utilization_percentage': avg_utilization,
                'periods_analyzed': periods,
                'recommendation': 'UNDERUTILIZED' if avg_utilization < 70 else 'WELL_UTILIZED'
            }
            
        except Exception as e:
            logger.error(f"Error getting reservation utilization: {e}")
            return {
                'average_utilization_percentage': 0.0,
                'periods_analyzed': 0,
                'recommendation': 'UNKNOWN'
            }
