/**
 * Dashboard Page Component
 * Implements React 19 features and KNOWLEDGE_BASE.md specifications
 * 
 * Features:
 * - Server Components for data fetching
 * - useOptimistic for real-time updates
 * - Core Web Vitals optimization
 * - WCAG 2.2 AA accessibility
 * - Nielsen's Heuristics compliance
 */

import React, { Suspense, useOptimistic, useTransition, useMemo } from 'react'
import { Helmet } from 'react-helmet-async'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { 
  TrendingUp, 
  TrendingDown, 
  DollarSign, 
  Server, 
  AlertTriangle,
  Zap,
  Calendar,
  Filter,
  RefreshCw
} from 'lucide-react'

import { useWebVitals } from '@/hooks/useWebVitals'
import { useFeature } from '@/hooks/useFeatureFlags'
import { LoadingSpinner, Skeleton, LoadingOverlay } from '@/components/LoadingSpinner'
import { ErrorBoundary } from '@/components/ErrorBoundary'
import { dashboardService } from '@/services/dashboard'
import { DashboardStats, CostTrendData, ResourceCostSummary, BudgetAlert } from '@/types'
import { formatCurrency, formatPercentage } from '@/utils/format'
import { cn } from '@/utils/cn'

// Server Component for dashboard data
async function DashboardData() {
  // This would be a Server Component in a real Next.js app
  // For now, we'll use React Query for data fetching
  return null
}

export default function Dashboard() {
  const queryClient = useQueryClient()
  const [isPending, startTransition] = useTransition()
  const [refreshing, setRefreshing] = React.useState(false)
  
  // Initialize Web Vitals monitoring
  useWebVitals({
    enableAnalytics: true,
    enableConsoleLogging: process.env.NODE_ENV === 'development'
  })

  // Feature flags
  const enableCostAnalysis = useFeature('enableCostAnalysis')
  const enableOptimization = useFeature('enableOptimization')
  const enableRealTimeUpdates = useFeature('enableRealTimeUpdates')

  // Dashboard data queries
  const { 
    data: stats, 
    isLoading: statsLoading, 
    error: statsError 
  } = useQuery({
    queryKey: ['dashboard', 'stats'],
    queryFn: dashboardService.getStats,
    staleTime: 1000 * 60 * 5, // 5 minutes
    refetchInterval: enableRealTimeUpdates ? 1000 * 30 : false, // 30 seconds if real-time enabled
  })

  const { 
    data: trends, 
    isLoading: trendsLoading 
  } = useQuery({
    queryKey: ['dashboard', 'trends'],
    queryFn: dashboardService.getCostTrends,
    staleTime: 1000 * 60 * 10, // 10 minutes
  })

  const { 
    data: alerts, 
    isLoading: alertsLoading 
  } = useQuery({
    queryKey: ['dashboard', 'alerts'],
    queryFn: dashboardService.getBudgetAlerts,
    staleTime: 1000 * 60 * 2, // 2 minutes
  })

  // Optimistic updates for real-time data
  const [optimisticStats, updateOptimisticStats] = useOptimistic(
    stats,
    (currentStats, newStats: DashboardStats) => ({
      ...currentStats,
      ...newStats,
    })
  )

  // Manual refresh function
  const handleRefresh = () => {
    startTransition(() => {
      setRefreshing(true)
      Promise.all([
        queryClient.invalidateQueries({ queryKey: ['dashboard'] }),
      ]).finally(() => {
        setRefreshing(false)
      })
    })
  }

  // Simulate real-time updates (in production, this would come from WebSocket)
  React.useEffect(() => {
    if (!enableRealTimeUpdates || !stats) return

    const interval = setInterval(() => {
      // Simulate small cost fluctuations
      const variation = (Math.random() - 0.5) * 0.02 // ±1%
      updateOptimisticStats({
        ...stats,
        totalCost: {
          ...stats.totalCost,
          amount: stats.totalCost.amount * (1 + variation)
        }
      })
    }, 5000)

    return () => clearInterval(interval)
  }, [stats, enableRealTimeUpdates, updateOptimisticStats])

  if (statsError) {
    throw statsError // Will be caught by ErrorBoundary
  }

  return (
    <>
      <Helmet>
        <title>Dashboard - FinOps-Teste</title>
        <meta name="description" content="FinOps dashboard with cost analysis, optimization recommendations, and budget tracking" />
      </Helmet>

      <div className="p-6 space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-foreground">
              Cost Dashboard
            </h1>
            <p className="text-muted-foreground">
              Monitor your cloud costs and optimization opportunities
            </p>
          </div>
          
          <div className="flex items-center gap-2">
            <button
              onClick={handleRefresh}
              disabled={refreshing || isPending}
              className="btn btn-outline btn-sm"
              aria-label="Refresh dashboard data"
            >
              <RefreshCw className={cn(
                'h-4 w-4',
                (refreshing || isPending) && 'animate-spin'
              )} />
              Refresh
            </button>
            
            <button className="btn btn-outline btn-sm">
              <Filter className="h-4 w-4 mr-2" />
              Filters
            </button>
            
            <button className="btn btn-outline btn-sm">
              <Calendar className="h-4 w-4 mr-2" />
              Last 30 days
            </button>
          </div>
        </div>

        {/* Alert Banner */}
        <ErrorBoundary>
          <Suspense fallback={<Skeleton className="h-16 w-full" />}>
            <AlertBanner alerts={alerts} isLoading={alertsLoading} />
          </Suspense>
        </ErrorBoundary>

        {/* Key Metrics */}
        <ErrorBoundary>
          <Suspense fallback={<MetricsSkeleton />}>
            <KeyMetrics 
              stats={optimisticStats} 
              isLoading={statsLoading}
              showRealTimeIndicator={enableRealTimeUpdates}
            />
          </Suspense>
        </ErrorBoundary>

        {/* Charts Section */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Cost Trends Chart */}
          {enableCostAnalysis && (
            <ErrorBoundary>
              <Suspense fallback={<ChartSkeleton />}>
                <CostTrendsChart 
                  data={trends} 
                  isLoading={trendsLoading}
                />
              </Suspense>
            </ErrorBoundary>
          )}

          {/* Resource Breakdown */}
          <ErrorBoundary>
            <Suspense fallback={<ChartSkeleton />}>
              <ResourceBreakdown />
            </Suspense>
          </ErrorBoundary>
        </div>

        {/* Optimization Recommendations */}
        {enableOptimization && (
          <ErrorBoundary>
            <Suspense fallback={<Skeleton className="h-64 w-full" />}>
              <OptimizationRecommendations />
            </Suspense>
          </ErrorBoundary>
        )}

        {/* Recent Activity */}
        <ErrorBoundary>
          <Suspense fallback={<Skeleton className="h-48 w-full" />}>
            <RecentActivity />
          </Suspense>
        </ErrorBoundary>
      </div>
    </>
  )
}

// Alert Banner Component
function AlertBanner({ 
  alerts, 
  isLoading 
}: { 
  alerts?: BudgetAlert[]
  isLoading: boolean 
}) {
  if (isLoading) return null
  if (!alerts || alerts.length === 0) return null

  const criticalAlerts = alerts.filter(alert => alert.severity === 'critical')
  const warningAlerts = alerts.filter(alert => alert.severity === 'warning')

  return (
    <div className="space-y-2">
      {criticalAlerts.map((alert) => (
        <div 
          key={alert.budgetId}
          className="flex items-center gap-3 p-4 bg-destructive/10 border border-destructive/20 rounded-lg"
          role="alert"
          aria-live="polite"
        >
          <AlertTriangle className="h-5 w-5 text-destructive flex-shrink-0" />
          <div className="flex-1">
            <p className="font-medium text-destructive">
              Budget Alert: {alert.budgetName}
            </p>
            <p className="text-sm text-muted-foreground">
              {formatPercentage(alert.currentUtilization)} of budget used 
              (threshold: {formatPercentage(alert.threshold)})
            </p>
          </div>
          <button className="btn btn-sm btn-destructive">
            View Details
          </button>
        </div>
      ))}
      
      {warningAlerts.map((alert) => (
        <div 
          key={alert.budgetId}
          className="flex items-center gap-3 p-4 bg-warning/10 border border-warning/20 rounded-lg"
          role="alert"
          aria-live="polite"
        >
          <AlertTriangle className="h-5 w-5 text-warning flex-shrink-0" />
          <div className="flex-1">
            <p className="font-medium text-warning">
              Budget Warning: {alert.budgetName}
            </p>
            <p className="text-sm text-muted-foreground">
              {formatPercentage(alert.currentUtilization)} of budget used
            </p>
          </div>
          <button className="btn btn-sm btn-outline">
            View Details
          </button>
        </div>
      ))}
    </div>
  )
}

// Key Metrics Component
function KeyMetrics({ 
  stats, 
  isLoading,
  showRealTimeIndicator = false
}: { 
  stats?: DashboardStats
  isLoading: boolean
  showRealTimeIndicator?: boolean
}) {
  if (isLoading) return <MetricsSkeleton />
  if (!stats) return null

  const metrics = [
    {
      name: 'Total Cost',
      value: formatCurrency(stats.totalCost.amount, stats.totalCost.currency),
      change: stats.monthlyTrend,
      icon: DollarSign,
      color: 'text-blue-600',
      bgColor: 'bg-blue-50 dark:bg-blue-950',
    },
    {
      name: 'Resources',
      value: stats.totalResources.toLocaleString(),
      change: 0, // Would come from API
      icon: Server,
      color: 'text-green-600',
      bgColor: 'bg-green-50 dark:bg-green-950',
    },
    {
      name: 'Recommendations',
      value: stats.activeRecommendations.toString(),
      change: 0,
      icon: Zap,
      color: 'text-yellow-600',
      bgColor: 'bg-yellow-50 dark:bg-yellow-950',
    },
    {
      name: 'Potential Savings',
      value: formatCurrency(stats.potentialSavings.amount, stats.potentialSavings.currency),
      change: 0,
      icon: TrendingUp,
      color: 'text-purple-600',
      bgColor: 'bg-purple-50 dark:bg-purple-950',
    },
  ]

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {metrics.map((metric) => {
        const Icon = metric.icon
        const isPositive = metric.change > 0
        const isNegative = metric.change < 0
        
        return (
          <div 
            key={metric.name}
            className="card p-6 hover:shadow-md transition-shadow"
          >
            <div className="flex items-center justify-between">
              <div className={cn('p-2 rounded-lg', metric.bgColor)}>
                <Icon className={cn('h-6 w-6', metric.color)} />
              </div>
              
              {showRealTimeIndicator && (
                <div className="h-2 w-2 bg-green-500 rounded-full animate-pulse" />
              )}
            </div>
            
            <div className="mt-4">
              <p className="text-sm font-medium text-muted-foreground">
                {metric.name}
              </p>
              <p className="text-2xl font-bold text-foreground">
                {metric.value}
              </p>
              
              {metric.change !== 0 && (
                <div className="flex items-center mt-2">
                  {isPositive ? (
                    <TrendingUp className="h-4 w-4 text-green-600 mr-1" />
                  ) : (
                    <TrendingDown className="h-4 w-4 text-red-600 mr-1" />
                  )}
                  <span className={cn(
                    'text-sm font-medium',
                    isPositive ? 'text-green-600' : 'text-red-600'
                  )}>
                    {formatPercentage(Math.abs(metric.change))}
                  </span>
                  <span className="text-sm text-muted-foreground ml-1">
                    vs last month
                  </span>
                </div>
              )}
            </div>
          </div>
        )
      })}
    </div>
  )
}

// Cost Trends Chart Component
function CostTrendsChart({ 
  data, 
  isLoading 
}: { 
  data?: CostTrendData[]
  isLoading: boolean 
}) {
  if (isLoading) return <ChartSkeleton />
  
  return (
    <div className="card p-6">
      <h3 className="text-lg font-semibold text-foreground mb-4">
        Cost Trends
      </h3>
      
      <div className="h-64 flex items-center justify-center text-muted-foreground">
        {/* Chart implementation would go here */}
        <div className="text-center">
          <TrendingUp className="h-12 w-12 mx-auto mb-2 opacity-50" />
          <p>Cost trend chart</p>
          <p className="text-sm">(Chart library integration needed)</p>
        </div>
      </div>
    </div>
  )
}

// Resource Breakdown Component
function ResourceBreakdown() {
  return (
    <div className="card p-6">
      <h3 className="text-lg font-semibold text-foreground mb-4">
        Resource Breakdown
      </h3>
      
      <div className="h-64 flex items-center justify-center text-muted-foreground">
        <div className="text-center">
          <Server className="h-12 w-12 mx-auto mb-2 opacity-50" />
          <p>Resource breakdown chart</p>
          <p className="text-sm">(Chart library integration needed)</p>
        </div>
      </div>
    </div>
  )
}

// Optimization Recommendations Component
function OptimizationRecommendations() {
  return (
    <div className="card p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-foreground">
          Optimization Recommendations
        </h3>
        <button className="btn btn-outline btn-sm">
          View All
        </button>
      </div>
      
      <div className="space-y-4">
        {/* Placeholder recommendations */}
        {[1, 2, 3].map((i) => (
          <div key={i} className="flex items-center gap-4 p-4 border border-border rounded-lg">
            <div className="p-2 bg-yellow-50 dark:bg-yellow-950 rounded-lg">
              <Zap className="h-5 w-5 text-yellow-600" />
            </div>
            
            <div className="flex-1">
              <p className="font-medium text-foreground">
                Downsize EC2 instance i-{i}234567890abcdef0
              </p>
              <p className="text-sm text-muted-foreground">
                Low CPU utilization detected. Potential savings: $45/month
              </p>
            </div>
            
            <button className="btn btn-sm btn-primary">
              Apply
            </button>
          </div>
        ))}
      </div>
    </div>
  )
}

// Recent Activity Component
function RecentActivity() {
  return (
    <div className="card p-6">
      <h3 className="text-lg font-semibold text-foreground mb-4">
        Recent Activity
      </h3>
      
      <div className="space-y-3">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="flex items-center gap-3 text-sm">
            <div className="h-2 w-2 bg-blue-500 rounded-full" />
            <span className="text-muted-foreground">2 hours ago</span>
            <span className="text-foreground">
              Budget alert triggered for Engineering team
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}

// Loading Skeletons
function MetricsSkeleton() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {[1, 2, 3, 4].map((i) => (
        <div key={i} className="card p-6">
          <div className="flex items-center justify-between mb-4">
            <Skeleton className="h-10 w-10 rounded-lg" />
            <Skeleton className="h-2 w-2 rounded-full" />
          </div>
          <Skeleton className="h-4 w-20 mb-2" />
          <Skeleton className="h-8 w-24 mb-2" />
          <Skeleton className="h-4 w-32" />
        </div>
      ))}
    </div>
  )
}

function ChartSkeleton() {
  return (
    <div className="card p-6">
      <Skeleton className="h-6 w-32 mb-4" />
      <Skeleton className="h-64 w-full" />
    </div>
  )
}