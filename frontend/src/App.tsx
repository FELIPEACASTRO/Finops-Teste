import { Routes, Route, Navigate } from 'react-router-dom'
import { Helmet } from 'react-helmet-async'
import { Suspense, lazy } from 'react'

import { useAuth } from '@/hooks/useAuth'
import { Layout } from '@/components/Layout'
import { LoadingSpinner } from '@/components/LoadingSpinner'
import { ProtectedRoute } from '@/components/ProtectedRoute'

// Lazy load pages for better performance
const Dashboard = lazy(() => import('@/pages/Dashboard'))
const Login = lazy(() => import('@/pages/Login'))
const Resources = lazy(() => import('@/pages/Resources'))
const CostAnalysis = lazy(() => import('@/pages/CostAnalysis'))
const Optimization = lazy(() => import('@/pages/Optimization'))
const Budgets = lazy(() => import('@/pages/Budgets'))
const Reports = lazy(() => import('@/pages/Reports'))
const Settings = lazy(() => import('@/pages/Settings'))
const Profile = lazy(() => import('@/pages/Profile'))
const NotFound = lazy(() => import('@/pages/NotFound'))

// Loading fallback component
const PageLoader = () => (
  <div className="flex items-center justify-center min-h-screen">
    <LoadingSpinner size="lg" />
  </div>
)

function App() {
  const { user, isLoading } = useAuth()

  // Show loading spinner while checking authentication
  if (isLoading) {
    return <PageLoader />
  }

  return (
    <>
      <Helmet>
        <title>FinOps-Teste - Enterprise Cost Optimization Platform</title>
        <meta 
          name="description" 
          content="Comprehensive cloud cost optimization and management platform for enterprise environments" 
        />
        <meta name="keywords" content="finops, cloud costs, aws optimization, cost management, cloud economics" />
        <meta property="og:title" content="FinOps-Teste" />
        <meta property="og:description" content="Enterprise Cost Optimization Platform" />
        <meta property="og:type" content="website" />
        <link rel="canonical" href={window.location.origin} />
      </Helmet>

      <Suspense fallback={<PageLoader />}>
        <Routes>
          {/* Public routes */}
          <Route 
            path="/login" 
            element={
              user ? <Navigate to="/dashboard" replace /> : <Login />
            } 
          />

          {/* Protected routes */}
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <Layout />
              </ProtectedRoute>
            }
          >
            {/* Dashboard - Default route */}
            <Route index element={<Navigate to="/dashboard" replace />} />
            <Route path="dashboard" element={<Dashboard />} />

            {/* Cost Management */}
            <Route path="resources" element={<Resources />} />
            <Route path="cost-analysis" element={<CostAnalysis />} />
            <Route path="optimization" element={<Optimization />} />
            <Route path="budgets" element={<Budgets />} />
            <Route path="reports" element={<Reports />} />

            {/* User Management */}
            <Route path="profile" element={<Profile />} />
            <Route path="settings" element={<Settings />} />
          </Route>

          {/* Catch all route */}
          <Route path="*" element={<NotFound />} />
        </Routes>
      </Suspense>
    </>
  )
}

export default App