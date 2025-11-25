"""
Multi-Account Manager Service
Manages analysis across multiple AWS accounts using AWS Organizations
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import logging
import boto3

logger = logging.getLogger(__name__)


@dataclass
class AWSAccount:
    """AWS Account information"""
    account_id: str
    account_name: str
    email: str
    status: str  # "ACTIVE", "SUSPENDED"
    organizational_unit: str
    tags: Dict[str, str]


class MultiAccountManager:
    """Manages multi-account FinOps analysis"""
    
    def __init__(self, organizations_client):
        """
        Initialize Multi-Account Manager
        
        Args:
            organizations_client: AWS Organizations client
        """
        self.organizations_client = organizations_client
    
    def list_accounts(self, include_suspended: bool = False) -> List[AWSAccount]:
        """
        List all accounts in the organization
        
        Args:
            include_suspended: Include suspended accounts
            
        Returns:
            List of AWS accounts
        """
        logger.info("Listing accounts in organization...")
        
        try:
            accounts = []
            paginator = self.organizations_client.get_paginator('list_accounts')
            
            for page in paginator.paginate():
                for account in page.get('Accounts', []):
                    status = account.get('Status')
                    
                    if not include_suspended and status != 'ACTIVE':
                        continue
                    
                    # Get account tags
                    tags = self._get_account_tags(account['Id'])
                    
                    # Get organizational unit
                    ou = self._get_account_ou(account['Id'])
                    
                    aws_account = AWSAccount(
                        account_id=account['Id'],
                        account_name=account.get('Name', ''),
                        email=account.get('Email', ''),
                        status=status,
                        organizational_unit=ou,
                        tags=tags
                    )
                    
                    accounts.append(aws_account)
            
            logger.info(f"Found {len(accounts)} accounts")
            return accounts
            
        except Exception as e:
            logger.error(f"Error listing accounts: {e}")
            return []
    
    def assume_role_in_account(
        self,
        account_id: str,
        role_name: str = "FinOpsAnalyzerRole"
    ) -> Optional[Dict[str, Any]]:
        """
        Assume role in target account for cross-account access
        
        Args:
            account_id: Target AWS account ID
            role_name: Role name to assume
            
        Returns:
            Temporary credentials or None
        """
        try:
            sts_client = boto3.client('sts')
            
            role_arn = f"arn:aws:iam::{account_id}:role/{role_name}"
            
            response = sts_client.assume_role(
                RoleArn=role_arn,
                RoleSessionName=f"finops-analyzer-{account_id}",
                DurationSeconds=3600  # 1 hour
            )
            
            credentials = response['Credentials']
            
            logger.info(f"Successfully assumed role in account {account_id}")
            
            return {
                'aws_access_key_id': credentials['AccessKeyId'],
                'aws_secret_access_key': credentials['SecretAccessKey'],
                'aws_session_token': credentials['SessionToken']
            }
            
        except Exception as e:
            logger.error(f"Error assuming role in account {account_id}: {e}")
            return None
    
    def create_cross_account_clients(
        self,
        account_id: str,
        region: str = 'us-east-1'
    ) -> Dict[str, Any]:
        """
        Create AWS clients for cross-account access
        
        Args:
            account_id: Target AWS account ID
            region: AWS region
            
        Returns:
            Dictionary of AWS clients
        """
        credentials = self.assume_role_in_account(account_id)
        
        if not credentials:
            return {}
        
        try:
            # Create clients with assumed role credentials
            session = boto3.Session(
                aws_access_key_id=credentials['aws_access_key_id'],
                aws_secret_access_key=credentials['aws_secret_access_key'],
                aws_session_token=credentials['aws_session_token'],
                region_name=region
            )
            
            clients = {
                'ec2': session.client('ec2'),
                'rds': session.client('rds'),
                'elb': session.client('elbv2'),
                'lambda': session.client('lambda'),
                's3': session.client('s3'),
                'ce': session.client('ce'),
                'cloudwatch': session.client('cloudwatch')
            }
            
            logger.info(f"Created cross-account clients for account {account_id}")
            return clients
            
        except Exception as e:
            logger.error(f"Error creating cross-account clients: {e}")
            return {}
    
    def _get_account_tags(self, account_id: str) -> Dict[str, str]:
        """Get tags for an account"""
        try:
            response = self.organizations_client.list_tags_for_resource(
                ResourceId=account_id
            )
            
            tags = {tag['Key']: tag['Value'] for tag in response.get('Tags', [])}
            return tags
            
        except Exception as e:
            logger.warning(f"Error getting tags for account {account_id}: {e}")
            return {}
    
    def _get_account_ou(self, account_id: str) -> str:
        """Get organizational unit for an account"""
        try:
            response = self.organizations_client.list_parents(
                ChildId=account_id
            )
            
            parents = response.get('Parents', [])
            if parents:
                parent_id = parents[0]['Id']
                
                # Get OU name
                if parent_id.startswith('ou-'):
                    ou_response = self.organizations_client.describe_organizational_unit(
                        OrganizationalUnitId=parent_id
                    )
                    return ou_response['OrganizationalUnit']['Name']
                else:
                    return "Root"
            
            return "Unknown"
            
        except Exception as e:
            logger.warning(f"Error getting OU for account {account_id}: {e}")
            return "Unknown"
