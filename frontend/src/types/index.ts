// Core Types for FinOps-Teste Frontend
// Matches backend domain entities

export interface User {
  id: string;
  email: string;
  fullName: string;
  isActive: boolean;
  isSuperuser: boolean;
  lastLogin?: string;
  createdAt: string;
  updatedAt: string;
}

export interface AuthTokens {
  accessToken: string;
  refreshToken: string;
  tokenType: string;
  expiresIn: number;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  user: User;
  tokens: AuthTokens;
}

// Resource Types
export enum ResourceType {
  EC2 = 'ec2',
  RDS = 'rds',
  S3 = 's3',
  LAMBDA = 'lambda',
  ELB = 'elb',
  EBS = 'ebs',
  CLOUDFRONT = 'cloudfront',
  ROUTE53 = 'route53',
  VPC = 'vpc',
  DYNAMODB = 'dynamodb',
  ECS = 'ecs',
  EKS = 'eks',
  FARGATE = 'fargate',
  BATCH = 'batch',
  LIGHTSAIL = 'lightsail',
}

export enum CostCategory {
  COMPUTE = 'compute',
  STORAGE = 'storage',
  NETWORK = 'network',
  DATABASE = 'database',
  SECURITY = 'security',
  MONITORING = 'monitoring',
  OTHER = 'other',
}

export enum OptimizationStatus {
  PENDING = 'pending',
  APPLIED = 'applied',
  REJECTED = 'rejected',
  EXPIRED = 'expired',
}

export interface Money {
  amount: number;
  currency: string;
}

export interface TimeRange {
  start: string;
  end: string;
}

export interface ResourceMetrics {
  cpuUtilization: number;
  memoryUtilization: number;
  networkIn: number;
  networkOut: number;
  storageUtilization: number;
}

export interface CloudResource {
  id: string;
  resourceId: string;
  resourceType: ResourceType;
  name: string;
  region: string;
  accountId: string;
  tags: Record<string, string>;
  createdAt: string;
  updatedAt: string;
}

export interface CostEntry {
  id: string;
  resourceId: string;
  cost: Money;
  category: CostCategory;
  timeRange: TimeRange;
  usageMetrics?: ResourceMetrics;
  createdAt: string;
}

export interface OptimizationRecommendation {
  id: string;
  resourceId: string;
  title: string;
  description: string;
  potentialSavings: Money;
  confidenceScore: number;
  status: OptimizationStatus;
  createdAt: string;
  expiresAt?: string;
  appliedAt?: string;
  rejectedAt?: string;
  rejectionReason?: string;
}

export interface Budget {
  id: string;
  name: string;
  amount: Money;
  spent: Money;
  timeRange: TimeRange;
  costCenter: string;
  alertThresholds: number[];
  createdAt: string;
  updatedAt: string;
  utilizationPercentage: number;
  remainingBudget: Money;
}

// API Response Types
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export interface ApiError {
  detail: string;
  code?: string;
  field?: string;
}

export interface ApiResponse<T> {
  data?: T;
  error?: ApiError;
  success: boolean;
  message?: string;
}

// Dashboard Types
export interface DashboardStats {
  totalCost: Money;
  monthlyTrend: number;
  totalResources: number;
  activeRecommendations: number;
  potentialSavings: Money;
  budgetUtilization: number;
}

export interface CostTrendData {
  date: string;
  cost: number;
  category: CostCategory;
}

export interface ResourceCostSummary {
  resourceType: ResourceType;
  totalCost: Money;
  resourceCount: number;
  averageCost: Money;
  trend: number;
}

export interface BudgetAlert {
  budgetId: string;
  budgetName: string;
  threshold: number;
  currentUtilization: number;
  severity: 'warning' | 'critical' | 'over_budget';
}

// Chart Data Types
export interface ChartDataPoint {
  date: string;
  value: number;
  label?: string;
  category?: string;
}

export interface PieChartData {
  name: string;
  value: number;
  color: string;
  percentage: number;
}

export interface BarChartData {
  name: string;
  value: number;
  color?: string;
  trend?: number;
}

// Filter Types
export interface DateFilter {
  start: Date;
  end: Date;
  preset?: 'last_7_days' | 'last_30_days' | 'last_90_days' | 'last_year' | 'custom';
}

export interface ResourceFilter {
  resourceTypes?: ResourceType[];
  regions?: string[];
  costCenters?: string[];
  tags?: Record<string, string>;
}

export interface CostFilter extends ResourceFilter {
  dateRange: DateFilter;
  categories?: CostCategory[];
  minAmount?: number;
  maxAmount?: number;
}

// Form Types
export interface CreateBudgetForm {
  name: string;
  amount: number;
  currency: string;
  startDate: string;
  endDate: string;
  costCenter: string;
  alertThresholds: number[];
}

export interface UpdateResourceForm {
  name: string;
  tags: Record<string, string>;
}

export interface OptimizationActionForm {
  recommendationId: string;
  action: 'apply' | 'reject';
  reason?: string;
}

// Table Types
export interface TableColumn<T> {
  key: keyof T;
  title: string;
  sortable?: boolean;
  filterable?: boolean;
  render?: (value: any, record: T) => React.ReactNode;
  width?: string | number;
}

export interface TablePagination {
  page: number;
  size: number;
  total: number;
}

export interface TableSort {
  field: string;
  direction: 'asc' | 'desc';
}

// Notification Types
export interface Notification {
  id: string;
  type: 'info' | 'success' | 'warning' | 'error';
  title: string;
  message: string;
  timestamp: string;
  read: boolean;
  actions?: NotificationAction[];
}

export interface NotificationAction {
  label: string;
  action: () => void;
  variant?: 'primary' | 'secondary';
}

// Theme Types
export interface Theme {
  name: string;
  colors: {
    primary: string;
    secondary: string;
    success: string;
    warning: string;
    error: string;
    background: string;
    foreground: string;
    muted: string;
    border: string;
  };
  spacing: Record<string, string>;
  typography: {
    fontFamily: string;
    fontSize: Record<string, string>;
    fontWeight: Record<string, string>;
  };
}

// Settings Types
export interface UserSettings {
  theme: 'light' | 'dark' | 'system';
  currency: string;
  timezone: string;
  notifications: {
    email: boolean;
    push: boolean;
    budgetAlerts: boolean;
    optimizationRecommendations: boolean;
  };
  dashboard: {
    defaultDateRange: string;
    refreshInterval: number;
    chartsPerRow: number;
  };
}

// Export Types
export interface ExportRequest {
  type: 'csv' | 'xlsx' | 'pdf';
  data: 'costs' | 'resources' | 'recommendations' | 'budgets';
  filters?: any;
  dateRange?: DateFilter;
}

export interface ExportResponse {
  downloadUrl: string;
  filename: string;
  expiresAt: string;
}

// Utility Types
export type LoadingState = 'idle' | 'loading' | 'success' | 'error';

export interface AsyncState<T> {
  data?: T;
  loading: boolean;
  error?: string;
}

export type DeepPartial<T> = {
  [P in keyof T]?: T[P] extends object ? DeepPartial<T[P]> : T[P];
};

export type Optional<T, K extends keyof T> = Omit<T, K> & Partial<Pick<T, K>>;

export type RequiredFields<T, K extends keyof T> = T & Required<Pick<T, K>>;

// Event Types
export interface AppEvent {
  type: string;
  payload?: any;
  timestamp: string;
}

export interface AnalyticsEvent extends AppEvent {
  userId?: string;
  sessionId: string;
  properties?: Record<string, any>;
}

// Feature Flag Types
export interface FeatureFlags {
  enableCostAnalysis: boolean;
  enableOptimization: boolean;
  enableBudgetManagement: boolean;
  enableReporting: boolean;
  enableMLRecommendations: boolean;
  enableRealTimeUpdates: boolean;
  enableAdvancedFilters: boolean;
  enableDataExport: boolean;
}

// Environment Types
export interface AppConfig {
  apiUrl: string;
  appTitle: string;
  version: string;
  environment: 'development' | 'staging' | 'production';
  features: FeatureFlags;
  analytics: {
    enabled: boolean;
    trackingId?: string;
  };
  monitoring: {
    enabled: boolean;
    dsn?: string;
  };
}