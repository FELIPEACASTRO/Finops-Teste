"""
Entidade de Domínio do Recurso AWS
Representa um recurso AWS com suas métricas e configurações.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum
from decimal import Decimal


class ResourceType(Enum):
    """Tipos de recursos AWS suportados - 200+ serviços (cobertura completa 2025)."""
    
    # ============================================================
    # COMPUTE (15 serviços)
    # ============================================================
    EC2 = "EC2"
    LAMBDA = "Lambda"
    ECS = "ECS"
    EKS = "EKS"
    FARGATE = "Fargate"
    BATCH = "Batch"
    LIGHTSAIL = "Lightsail"
    ELASTIC_BEANSTALK = "ElasticBeanstalk"
    APP_RUNNER = "AppRunner"
    OUTPOSTS = "Outposts"
    LOCAL_ZONES = "LocalZones"
    WAVELENGTH = "Wavelength"
    SERVERLESS_APPLICATION_REPOSITORY = "ServerlessApplicationRepository"
    VMWARE_CLOUD = "VMwareCloud"
    PARALLEL_CLUSTER = "ParallelCluster"
    
    # ============================================================
    # STORAGE (15 serviços)
    # ============================================================
    S3 = "S3"
    S3_GLACIER = "S3Glacier"
    S3_GLACIER_DEEP_ARCHIVE = "S3GlacierDeepArchive"
    S3_INTELLIGENT_TIERING = "S3IntelligentTiering"
    EBS = "EBS"
    EFS = "EFS"
    FSX = "FSx"
    FSX_WINDOWS = "FSxWindows"
    FSX_LUSTRE = "FSxLustre"
    FSX_NETAPP_ONTAP = "FSxNetAppONTAP"
    FSX_OPENZFS = "FSxOpenZFS"
    STORAGE_GATEWAY = "StorageGateway"
    BACKUP = "Backup"
    ELASTIC_DISASTER_RECOVERY = "ElasticDisasterRecovery"
    FILE_CACHE = "FileCache"
    
    # ============================================================
    # DATABASE (17 serviços)
    # ============================================================
    RDS = "RDS"
    AURORA = "Aurora"
    AURORA_SERVERLESS = "AuroraServerless"
    AURORA_DSQL = "AuroraDS QL"
    DYNAMODB = "DynamoDB"
    ELASTICACHE = "ElastiCache"
    ELASTICACHE_SERVERLESS = "ElastiCacheServerless"
    MEMORYDB = "MemoryDB"
    REDSHIFT = "Redshift"
    REDSHIFT_SERVERLESS = "RedshiftServerless"
    DOCUMENTDB = "DocumentDB"
    NEPTUNE = "Neptune"
    QLDB = "QLDB"
    TIMESTREAM = "Timestream"
    KEYSPACES = "Keyspaces"
    DAX = "DAX"
    RDS_PROXY = "RDSProxy"
    
    # ============================================================
    # NETWORKING & CONTENT DELIVERY (20 serviços)
    # ============================================================
    VPC = "VPC"
    CLOUDFRONT = "CloudFront"
    ROUTE53 = "Route53"
    API_GATEWAY = "APIGateway"
    DIRECT_CONNECT = "DirectConnect"
    APP_MESH = "AppMesh"
    CLOUD_MAP = "CloudMap"
    GLOBAL_ACCELERATOR = "GlobalAccelerator"
    ELB = "ELB"
    ALB = "ALB"
    NLB = "NLB"
    GATEWAY_LOAD_BALANCER = "GatewayLoadBalancer"
    PRIVATE_LINK = "PrivateLink"
    TRANSIT_GATEWAY = "TransitGateway"
    CLIENT_VPN = "ClientVPN"
    SITE_TO_SITE_VPN = "SiteToSiteVPN"
    CLOUD_WAN = "CloudWAN"
    PRIVATE_5G = "Private5G"
    VPC_LATTICE = "VPCLattice"
    VERIFIED_ACCESS = "VerifiedAccess"
    
    # ============================================================
    # ANALYTICS (18 serviços)
    # ============================================================
    ATHENA = "Athena"
    EMR = "EMR"
    EMR_SERVERLESS = "EMRServerless"
    KINESIS = "Kinesis"
    KINESIS_DATA_STREAMS = "KinesisDataStreams"
    KINESIS_DATA_FIREHOSE = "KinesisDataFirehose"
    KINESIS_DATA_ANALYTICS = "KinesisDataAnalytics"
    KINESIS_VIDEO_STREAMS = "KinesisVideoStreams"
    MSK = "MSK"
    MSK_SERVERLESS = "MSKServerless"
    GLUE = "Glue"
    GLUE_DATABREW = "GlueDataBrew"
    DATA_PIPELINE = "DataPipeline"
    LAKE_FORMATION = "LakeFormation"
    QUICKSIGHT = "QuickSight"
    OPENSEARCH_SERVICE = "OpenSearchService"
    DATA_EXCHANGE = "DataExchange"
    CLEAN_ROOMS = "CleanRooms"
    FINSPACE = "FinSpace"
    
    # ============================================================
    # APPLICATION INTEGRATION (13 serviços)
    # ============================================================
    SQS = "SQS"
    SNS = "SNS"
    SES = "SES"
    APPSYNC = "AppSync"
    EVENTBRIDGE = "EventBridge"
    EVENTBRIDGE_PIPES = "EventBridgePipes"
    STEP_FUNCTIONS = "StepFunctions"
    STEP_FUNCTIONS_EXPRESS = "StepFunctionsExpress"
    SWF = "SWF"
    MQ = "MQ"
    MANAGED_APACHE_AIRFLOW = "ManagedApacheAirflow"
    APPFLOW = "AppFlow"
    B2BI = "B2BI"
    
    # ============================================================
    # MACHINE LEARNING & AI (25 serviços)
    # ============================================================
    SAGEMAKER = "SageMaker"
    SAGEMAKER_STUDIO = "SageMakerStudio"
    SAGEMAKER_CANVAS = "SageMakerCanvas"
    BEDROCK = "Bedrock"
    AMAZON_Q = "AmazonQ"
    AMAZON_Q_BUSINESS = "AmazonQBusiness"
    CODEWHISPERER = "CodeWhisperer"
    TEXTRACT = "Textract"
    REKOGNITION = "Rekognition"
    COMPREHEND = "Comprehend"
    TRANSLATE = "Translate"
    TRANSCRIBE = "Transcribe"
    POLLY = "Polly"
    LEX = "Lex"
    FORECAST = "Forecast"
    PERSONALIZE = "Personalize"
    FRAUD_DETECTOR = "FraudDetector"
    LOOKOUT_METRICS = "LookoutMetrics"
    LOOKOUT_VISION = "LookoutVision"
    LOOKOUT_EQUIPMENT = "LookoutEquipment"
    MONITRON = "Monitron"
    HEALTHLAKE = "HealthLake"
    KENDRA = "Kendra"
    AUGMENTED_AI = "AugmentedAI"
    DEVOPS_GURU = "DevOpsGuru"
    
    # ============================================================
    # DEVELOPER TOOLS (18 serviços)
    # ============================================================
    CODECOMMIT = "CodeCommit"
    CODEBUILD = "CodeBuild"
    CODEDEPLOY = "CodeDeploy"
    CODEPIPELINE = "CodePipeline"
    CODESTAR = "CodeStar"
    CODECATALYST = "CodeCatalyst"
    CODEGURU = "CodeGuru"
    CODEGURU_REVIEWER = "CodeGuruReviewer"
    CODEGURU_PROFILER = "CodeGuruProfiler"
    CODEARTIFACT = "CodeArtifact"
    CLOUD9 = "Cloud9"
    CLOUDSHELL = "CloudShell"
    X_RAY = "XRay"
    APPLICATION_COMPOSER = "ApplicationComposer"
    FAULT_INJECTION_SIMULATOR = "FaultInjectionSimulator"
    MICROSERVICE_EXTRACTOR = "MicroserviceExtractor"
    PROTON = "Proton"
    COPILOT_CLI = "CopilotCLI"
    
    # ============================================================
    # SECURITY, IDENTITY & COMPLIANCE (25 serviços)
    # ============================================================
    IAM = "IAM"
    IAM_IDENTITY_CENTER = "IAMIdentityCenter"
    COGNITO = "Cognito"
    VERIFIED_PERMISSIONS = "VerifiedPermissions"
    SECRETS_MANAGER = "SecretsManager"
    KMS = "KMS"
    CLOUDHSM = "CloudHSM"
    CERTIFICATE_MANAGER = "CertificateManager"
    PRIVATE_CERTIFICATE_AUTHORITY = "PrivateCertificateAuthority"
    WAF = "WAF"
    SHIELD = "Shield"
    FIREWALL_MANAGER = "FirewallManager"
    NETWORK_FIREWALL = "NetworkFirewall"
    GUARDDUTY = "GuardDuty"
    MACIE = "Macie"
    INSPECTOR = "Inspector"
    DETECTIVE = "Detective"
    SECURITY_HUB = "SecurityHub"
    AUDIT_MANAGER = "AuditManager"
    ARTIFACT = "Artifact"
    RESOURCE_ACCESS_MANAGER = "RAM"
    DIRECTORY_SERVICE = "DirectoryService"
    PAYMENT_CRYPTOGRAPHY = "PaymentCryptography"
    SIGNER = "Signer"
    SECURITY_LAKE = "SecurityLake"
    
    # ============================================================
    # MANAGEMENT & GOVERNANCE (25 serviços)
    # ============================================================
    CLOUDWATCH = "CloudWatch"
    CLOUDWATCH_LOGS = "CloudWatchLogs"
    CLOUDWATCH_LOGS_INSIGHTS = "CloudWatchLogsInsights"
    CLOUDTRAIL = "CloudTrail"
    CONFIG = "Config"
    SYSTEMS_MANAGER = "SystemsManager"
    SYSTEMS_MANAGER_PARAMETER_STORE = "SystemsManagerParameterStore"
    CLOUDFORMATION = "CloudFormation"
    SERVICE_CATALOG = "ServiceCatalog"
    TRUSTED_ADVISOR = "TrustedAdvisor"
    CONTROL_TOWER = "ControlTower"
    LICENSE_MANAGER = "LicenseManager"
    ORGANIZATIONS = "Organizations"
    RESOURCE_GROUPS = "ResourceGroups"
    TAG_EDITOR = "TagEditor"
    MANAGED_GRAFANA = "ManagedGrafana"
    MANAGED_PROMETHEUS = "ManagedPrometheus"
    OPSWORKS = "OpsWorks"
    OPSWORKS_CM = "OpsWorksCM"
    CHATBOT = "Chatbot"
    LAUNCH_WIZARD = "LaunchWizard"
    RESILIENCE_HUB = "ResilienceHub"
    INCIDENT_MANAGER = "IncidentManager"
    SERVICE_MANAGEMENT_CONNECTOR = "ServiceManagementConnector"
    APP_CONFIG = "AppConfig"
    
    # ============================================================
    # MIGRATION & TRANSFER (12 serviços)
    # ============================================================
    MIGRATION_HUB = "MigrationHub"
    APPLICATION_MIGRATION_SERVICE = "ApplicationMigrationService"
    DATABASE_MIGRATION_SERVICE = "DatabaseMigrationService"
    DMS_FLEET_ADVISOR = "DMSFleetAdvisor"
    DATASYNC = "DataSync"
    TRANSFER_FAMILY = "TransferFamily"
    MIGRATION_EVALUATOR = "MigrationEvaluator"
    MIGRATION_HUB_REFACTOR_SPACES = "MigrationHubRefactorSpaces"
    MIGRATION_HUB_ORCHESTRATOR = "MigrationHubOrchestrator"
    MAINFRAME_MODERNIZATION = "MainframeModernization"
    SNOW_FAMILY = "SnowFamily"
    SNOWCONE = "Snowcone"
    
    # ============================================================
    # BUSINESS APPLICATIONS (12 serviços)
    # ============================================================
    CONNECT = "Connect"
    CONNECT_CUSTOMER_PROFILES = "ConnectCustomerProfiles"
    PINPOINT = "Pinpoint"
    CHIME = "Chime"
    CHIME_SDK = "ChimeSDK"
    WORKMAIL = "WorkMail"
    WORKDOCS = "WorkDocs"
    ALEXA_FOR_BUSINESS = "AlexaForBusiness"
    AMPLIFY = "Amplify"
    AMPLIFY_UI_BUILDER = "AmplifyUIBuilder"
    SUPPLY_CHAIN = "SupplyChain"
    WICKR = "Wickr"
    
    # ============================================================
    # END USER COMPUTING (5 serviços)
    # ============================================================
    WORKSPACES = "WorkSpaces"
    WORKSPACES_WEB = "WorkSpacesWeb"
    WORKSPACES_THIN_CLIENT = "WorkSpacesThinClient"
    APPSTREAM = "AppStream"
    APPSTREAM_2 = "AppStream2.0"
    
    # ============================================================
    # IOT (15 serviços)
    # ============================================================
    IOT_CORE = "IoTCore"
    IOT_GREENGRASS = "IoTGreengrass"
    IOT_ANALYTICS = "IoTAnalytics"
    IOT_DEVICE_MANAGEMENT = "IoTDeviceManagement"
    IOT_DEVICE_DEFENDER = "IoTDeviceDefender"
    IOT_EVENTS = "IoTEvents"
    IOT_SITEWISE = "IoTSiteWise"
    IOT_TWINMAKER = "IoTTwinMaker"
    IOT_FLEETWISE = "IoTFleetWise"
    IOT_ROBORUNNER = "IoTRoboRunner"
    IOT_1CLICK = "IoT1Click"
    IOT_BUTTON = "IoTButton"
    IOT_EDUKIT = "IoTEduKit"
    IOT_EXPRESSLINK = "IoTExpressLink"
    FREERTOS = "FreeRTOS"
    
    # ============================================================
    # ROBOTICS (2 serviços)
    # ============================================================
    ROBOMAKER = "RoboMaker"
    IOT_ROBORUNNER = "IoTRoboRunner"
    
    # ============================================================
    # MEDIA SERVICES (12 serviços)
    # ============================================================
    ELASTIC_TRANSCODER = "ElasticTranscoder"
    ELEMENTAL_MEDIACONVERT = "ElementalMediaConvert"
    ELEMENTAL_MEDIALIVE = "ElementalMediaLive"
    ELEMENTAL_MEDIAPACKAGE = "ElementalMediaPackage"
    ELEMENTAL_MEDIASTORE = "ElementalMediaStore"
    ELEMENTAL_MEDIATAILOR = "ElementalMediaTailor"
    ELEMENTAL_MEDIACONNECT = "ElementalMediaConnect"
    KINESIS_VIDEO_STREAMS = "KinesisVideoStreams"
    INTERACTIVE_VIDEO_SERVICE = "InteractiveVideoService"
    NIMBLE_STUDIO = "NimbleStudio"
    THINKBOX_DEADLINE = "ThinkboxDeadline"
    ELASTIC_TRANSCODER_PIPELINE = "ElasticTranscoderPipeline"
    
    # ============================================================
    # GAME TECH (3 serviços)
    # ============================================================
    GAMELIFT = "GameLift"
    GAMESPARKS = "GameSparks"
    LUMBERYARD = "Lumberyard"
    
    # ============================================================
    # AR/VR (3 serviços)
    # ============================================================
    SUMERIAN = "Sumerian"
    AR_VR = "ARVR"
    SIMSPACE_WEAVER = "SimSpaceWeaver"
    
    # ============================================================
    # BLOCKCHAIN (2 serviços)
    # ============================================================
    MANAGED_BLOCKCHAIN = "ManagedBlockchain"
    QUANTUM_LEDGER_DATABASE = "QuantumLedgerDatabase"
    
    # ============================================================
    # QUANTUM COMPUTING (1 serviço)
    # ============================================================
    BRAKET = "Braket"
    
    # ============================================================
    # SATELLITE (1 serviço)
    # ============================================================
    GROUND_STATION = "GroundStation"
    
    # ============================================================
    # COST MANAGEMENT (7 serviços)
    # ============================================================
    COST_EXPLORER = "CostExplorer"
    COST_AND_USAGE_REPORT = "CostAndUsageReport"
    BUDGETS = "Budgets"
    COST_ANOMALY_DETECTION = "CostAnomalyDetection"
    SAVINGS_PLANS = "SavingsPlans"
    BILLING_CONDUCTOR = "BillingConductor"
    MARKETPLACE = "Marketplace"
    
    # ============================================================
    # CUSTOMER ENABLEMENT (3 serviços)
    # ============================================================
    IQ = "IQ"
    SUPPORT = "Support"
    MANAGED_SERVICES = "ManagedServices"
    
    # ============================================================
    # GENERIC/UNKNOWN
    # ============================================================
    GENERIC = "Generic"
    UNKNOWN = "Unknown"


class UsagePattern(Enum):
    """Padrões de uso de recursos."""
    STEADY = "steady"
    VARIABLE = "variable"
    BATCH = "batch"
    IDLE = "idle"
    UNKNOWN = "unknown"


class Priority(Enum):
    """Níveis de prioridade das recomendações."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class RiskLevel(Enum):
    """Níveis de risco para recomendações."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class MetricDataPoint:
    """A single metric data point."""
    timestamp: datetime
    value: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "value": round(self.value, 2)
        }


@dataclass
class ResourceMetrics:
    """Container for resource metrics."""
    cpu_utilization: List[MetricDataPoint] = field(default_factory=list)
    memory_utilization: List[MetricDataPoint] = field(default_factory=list)
    network_in: List[MetricDataPoint] = field(default_factory=list)
    network_out: List[MetricDataPoint] = field(default_factory=list)
    disk_read_ops: List[MetricDataPoint] = field(default_factory=list)
    disk_write_ops: List[MetricDataPoint] = field(default_factory=list)
    custom_metrics: Dict[str, List[MetricDataPoint]] = field(default_factory=dict)

    def get_cpu_stats(self) -> Dict[str, float]:
        """Calculate CPU statistics."""
        if not self.cpu_utilization:
            return {"mean": 0.0, "p95": 0.0, "p99": 0.0, "max": 0.0}

        values = [dp.value for dp in self.cpu_utilization]
        values.sort()
        n = len(values)

        return {
            "mean": sum(values) / n,
            "p95": values[int(0.95 * n)] if n > 0 else 0.0,
            "p99": values[int(0.99 * n)] if n > 0 else 0.0,
            "max": max(values)
        }


@dataclass
class AWSResource:
    """
    Core AWS Resource entity.

    This entity represents any AWS resource that can be analyzed for cost optimization.
    It follows the Single Responsibility Principle by focusing only on resource data.
    """
    resource_id: str
    resource_type: ResourceType
    region: str
    account_id: str
    tags: Dict[str, str] = field(default_factory=dict)
    configuration: Dict[str, Any] = field(default_factory=dict)
    metrics: ResourceMetrics = field(default_factory=ResourceMetrics)
    created_at: Optional[datetime] = None
    last_updated: Optional[datetime] = None

    def __post_init__(self):
        """Post-initialization validation."""
        if not self.resource_id:
            raise ValueError("resource_id cannot be empty")
        if not self.region:
            raise ValueError("region cannot be empty")
        if not self.account_id:
            raise ValueError("account_id cannot be empty")

    def get_tag(self, key: str, default: str = "") -> str:
        """Get tag value by key."""
        return self.tags.get(key, default)

    def is_production(self) -> bool:
        """Check if resource is in production environment."""
        env = self.get_tag("Environment", "").lower()
        return env in ["prod", "production", "prd"]

    def get_criticality(self) -> str:
        """Get resource criticality level."""
        return self.get_tag("Criticality", "medium").lower()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "resource_id": self.resource_id,
            "resource_type": self.resource_type.value,
            "region": self.region,
            "account_id": self.account_id,
            "tags": self.tags,
            "configuration": self.configuration,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None,
            "metrics": {
                "cpu_utilization": [dp.to_dict() for dp in self.metrics.cpu_utilization],
                "memory_utilization": [dp.to_dict() for dp in self.metrics.memory_utilization],
                "network_in": [dp.to_dict() for dp in self.metrics.network_in],
                "network_out": [dp.to_dict() for dp in self.metrics.network_out],
                "disk_read_ops": [dp.to_dict() for dp in self.metrics.disk_read_ops],
                "disk_write_ops": [dp.to_dict() for dp in self.metrics.disk_write_ops],
                "custom_metrics": {
                    k: [dp.to_dict() for dp in v]
                    for k, v in self.metrics.custom_metrics.items()
                }
            }
        }


@dataclass
class CostData:
    """Cost information for resources."""
    total_cost_usd: Decimal
    period_days: int
    cost_by_service: Dict[str, Decimal] = field(default_factory=dict)
    daily_costs: List[Dict[str, Any]] = field(default_factory=list)

    def get_top_services(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top services by cost."""
        sorted_services = sorted(
            self.cost_by_service.items(),
            key=lambda x: x[1],
            reverse=True
        )[:limit]

        return [
            {
                "service": service,
                "cost_usd": float(cost),
                "percentage": float(cost / self.total_cost_usd * 100) if self.total_cost_usd > 0 else 0.0
            }
            for service, cost in sorted_services
        ]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "total_cost_usd": float(self.total_cost_usd),
            "period_days": self.period_days,
            "cost_by_service": {
                service: float(cost)
                for service, cost in self.cost_by_service.items()
            },
            "daily_costs": self.daily_costs,
            "top_services": self.get_top_services()
        }


@dataclass
class OptimizationRecommendation:
    """
    Optimization recommendation entity.

    Represents a specific recommendation for cost optimization.
    """
    resource_id: str
    resource_type: ResourceType
    current_config: str
    recommended_action: str
    recommendation_details: str
    reasoning: str
    monthly_savings_usd: Decimal
    annual_savings_usd: Decimal
    savings_percentage: float
    risk_level: RiskLevel
    priority: Priority
    implementation_steps: List[str] = field(default_factory=list)
    usage_pattern: UsagePattern = UsagePattern.UNKNOWN
    confidence_score: float = 0.0

    def __post_init__(self):
        """Post-initialization validation."""
        if self.monthly_savings_usd < 0:
            raise ValueError("monthly_savings_usd cannot be negative")
        if not 0 <= self.confidence_score <= 1:
            raise ValueError("confidence_score must be between 0 and 1")
        if not 0 <= self.savings_percentage <= 100:
            raise ValueError("savings_percentage must be between 0 and 100")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "resource_id": self.resource_id,
            "resource_type": self.resource_type.value,
            "current_config": self.current_config,
            "recommended_action": self.recommended_action,
            "recommendation_details": self.recommendation_details,
            "reasoning": self.reasoning,
            "monthly_savings_usd": float(self.monthly_savings_usd),
            "annual_savings_usd": float(self.annual_savings_usd),
            "savings_percentage": self.savings_percentage,
            "risk_level": self.risk_level.value,
            "priority": self.priority.value,
            "implementation_steps": self.implementation_steps,
            "usage_pattern": self.usage_pattern.value,
            "confidence_score": self.confidence_score
        }


@dataclass
class AnalysisReport:
    """
    Complete analysis report entity.

    Aggregates all analysis results and recommendations.
    """
    generated_at: datetime
    version: str
    model_used: str
    analysis_period_days: int
    total_resources_analyzed: int
    total_monthly_savings_usd: Decimal
    total_annual_savings_usd: Decimal
    recommendations: List[OptimizationRecommendation] = field(default_factory=list)
    cost_data: Optional[CostData] = None

    def get_recommendations_by_priority(self, priority: Priority) -> List[OptimizationRecommendation]:
        """Get recommendations filtered by priority."""
        return [r for r in self.recommendations if r.priority == priority]

    def get_high_priority_count(self) -> int:
        """Get count of high priority recommendations."""
        return len(self.get_recommendations_by_priority(Priority.HIGH))

    def get_medium_priority_count(self) -> int:
        """Get count of medium priority recommendations."""
        return len(self.get_recommendations_by_priority(Priority.MEDIUM))

    def get_low_priority_count(self) -> int:
        """Get count of low priority recommendations."""
        return len(self.get_recommendations_by_priority(Priority.LOW))

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "generated_at": self.generated_at.isoformat(),
            "version": self.version,
            "model_used": self.model_used,
            "analysis_period_days": self.analysis_period_days,
            "total_resources_analyzed": self.total_resources_analyzed,
            "total_monthly_savings_usd": float(self.total_monthly_savings_usd),
            "total_annual_savings_usd": float(self.total_annual_savings_usd),
            "high_priority_actions": self.get_high_priority_count(),
            "medium_priority_actions": self.get_medium_priority_count(),
            "low_priority_actions": self.get_low_priority_count(),
            "recommendations": [r.to_dict() for r in self.recommendations],
            "cost_data": self.cost_data.to_dict() if self.cost_data else None
        }
