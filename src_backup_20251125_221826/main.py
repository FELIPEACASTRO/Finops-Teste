"""
Main application entry point for FinOps Analyzer v4.0.
Provides a complete, production-ready AWS cost optimization solution.
"""

import asyncio
import json
import sys
from datetime import datetime
from typing import List, Optional

from .interfaces.lambda_handler import lambda_handler
from .core.config import get_config
from .core.logger import setup_logger


class FinOpsAnalyzer:
    """
    Main application class for FinOps Analyzer.
    
    Provides a high-level interface for running cost optimization analysis.
    Follows the Facade Pattern to simplify complex subsystem interactions.
    """
    
    def __init__(self):
        self.config = get_config()
        self.logger = setup_logger(__name__)
        
    async def analyze(
        self,
        regions: Optional[List[str]] = None,
        analysis_period_days: int = 30,
        include_cost_data: bool = True,
        save_report: bool = True,
        output_format: str = "json"
    ) -> dict:
        """
        Run complete FinOps analysis.
        
        Args:
            regions: AWS regions to analyze (defaults to config region)
            analysis_period_days: Number of days to analyze (1-365)
            include_cost_data: Whether to include cost data
            save_report: Whether to save report to S3
            output_format: Output format (json, summary)
            
        Returns:
            dict: Analysis results
        """
        try:
            self.logger.info("Starting FinOps analysis")
            
            # Use default region if none specified
            if not regions:
                regions = [self.config.aws_region]
            
            # Create event for lambda handler
            event = {
                "request_type": "analysis",
                "regions": regions,
                "analysis_period_days": analysis_period_days,
                "include_cost_data": include_cost_data,
                "save_report": save_report
            }
            
            # Execute analysis
            result = lambda_handler(event, None)
            
            # Format output based on requested format
            if output_format == "summary":
                return self._format_summary(result)
            else:
                return result
                
        except Exception as e:
            self.logger.error(f"Analysis failed: {str(e)}")
            return {
                "statusCode": 500,
                "body": {
                    "success": False,
                    "error_message": str(e)
                }
            }
    
    async def get_report(self, report_id: str) -> dict:
        """
        Retrieve a saved analysis report.
        
        Args:
            report_id: ID of the report to retrieve
            
        Returns:
            dict: Report data or error
        """
        try:
            event = {
                "request_type": "get_report",
                "report_id": report_id
            }
            
            return lambda_handler(event, None)
            
        except Exception as e:
            self.logger.error(f"Failed to get report {report_id}: {str(e)}")
            return {
                "statusCode": 500,
                "body": {"error": str(e)}
            }
    
    async def list_reports(self, limit: int = 10) -> dict:
        """
        List recent analysis reports.
        
        Args:
            limit: Maximum number of reports to return
            
        Returns:
            dict: List of reports or error
        """
        try:
            event = {
                "request_type": "list_reports",
                "limit": limit
            }
            
            return lambda_handler(event, None)
            
        except Exception as e:
            self.logger.error(f"Failed to list reports: {str(e)}")
            return {
                "statusCode": 500,
                "body": {"error": str(e)}
            }
    
    def _format_summary(self, result: dict) -> dict:
        """Format result as a summary."""
        try:
            body = result.get("body", {})
            
            if not body.get("success", False):
                return {
                    "success": False,
                    "error": body.get("error_message", "Unknown error")
                }
            
            report = body.get("report", {})
            
            return {
                "success": True,
                "summary": {
                    "generated_at": report.get("generated_at"),
                    "total_resources_analyzed": report.get("total_resources_analyzed", 0),
                    "total_monthly_savings_usd": report.get("total_monthly_savings_usd", 0),
                    "total_annual_savings_usd": report.get("total_annual_savings_usd", 0),
                    "high_priority_actions": report.get("high_priority_actions", 0),
                    "medium_priority_actions": report.get("medium_priority_actions", 0),
                    "low_priority_actions": report.get("low_priority_actions", 0),
                    "report_location": body.get("report_location"),
                    "execution_time_seconds": body.get("execution_time_seconds", 0)
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to format summary: {str(e)}"
            }


def main():
    """
    Command-line interface for FinOps Analyzer.
    
    Usage:
        python -m src.main analyze --regions us-east-1,us-west-2 --days 30
        python -m src.main get-report --report-id finops-analysis-20241124-120000
        python -m src.main list-reports --limit 5
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="AWS FinOps Analyzer v4.0")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Run cost optimization analysis")
    analyze_parser.add_argument(
        "--regions", 
        type=str, 
        help="Comma-separated list of AWS regions (default: from config)"
    )
    analyze_parser.add_argument(
        "--days", 
        type=int, 
        default=30, 
        help="Number of days to analyze (default: 30)"
    )
    analyze_parser.add_argument(
        "--no-cost-data", 
        action="store_true", 
        help="Skip cost data collection"
    )
    analyze_parser.add_argument(
        "--no-save", 
        action="store_true", 
        help="Don't save report to S3"
    )
    analyze_parser.add_argument(
        "--format", 
        choices=["json", "summary"], 
        default="json", 
        help="Output format"
    )
    
    # Get report command
    get_parser = subparsers.add_parser("get-report", help="Retrieve a saved report")
    get_parser.add_argument("--report-id", required=True, help="Report ID to retrieve")
    
    # List reports command
    list_parser = subparsers.add_parser("list-reports", help="List recent reports")
    list_parser.add_argument("--limit", type=int, default=10, help="Number of reports to list")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Create analyzer
    analyzer = FinOpsAnalyzer()
    
    async def run_command():
        if args.command == "analyze":
            regions = args.regions.split(",") if args.regions else None
            result = await analyzer.analyze(
                regions=regions,
                analysis_period_days=args.days,
                include_cost_data=not args.no_cost_data,
                save_report=not args.no_save,
                output_format=args.format
            )
            
        elif args.command == "get-report":
            result = await analyzer.get_report(args.report_id)
            
        elif args.command == "list-reports":
            result = await analyzer.list_reports(args.limit)
            
        else:
            result = {"error": f"Unknown command: {args.command}"}
        
        # Print result
        print(json.dumps(result, indent=2, default=str))
    
    # Run async command
    try:
        asyncio.run(run_command())
    except KeyboardInterrupt:
        print("\nAnalysis interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()