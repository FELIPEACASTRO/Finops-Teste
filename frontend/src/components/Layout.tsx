/**
 * Main Layout Component
 * Implements React 19 features and KNOWLEDGE_BASE.md specifications
 * 
 * Features:
 * - Server Components for static content
 * - Client Components for interactivity
 * - Optimistic updates
 * - Error boundaries
 * - Accessibility (WCAG 2.2 AA)
 */

import React, { Suspense, useOptimistic, useTransition } from 'react'
import { Outlet, useLocation, useNavigate } from 'react-router-dom'
import { Helmet } from 'react-helmet-async'
import { 
  BarChart3, 
  DollarSign, 
  TrendingUp, 
  Settings, 
  User, 
  Menu,
  Bell,
  Search,
  Sun,
  Moon,
  LogOut
} from 'lucide-react'

import { useAuth } from '@/hooks/useAuth'
import { useTheme } from '@/hooks/useTheme'
import { useFeature } from '@/hooks/useFeatureFlags'
import { LoadingSpinner } from '@/components/LoadingSpinner'
import { ErrorBoundary } from '@/components/ErrorBoundary'
import { NotificationCenter } from '@/components/NotificationCenter'
import { SearchCommand } from '@/components/SearchCommand'

interface NavigationItem {
  name: string
  href: string
  icon: React.ComponentType<{ className?: string }>
  badge?: number
  feature?: string
}

const navigation: NavigationItem[] = [
  { name: 'Dashboard', href: '/dashboard', icon: BarChart3 },
  { name: 'Resources', href: '/resources', icon: DollarSign },
  { name: 'Cost Analysis', href: '/cost-analysis', icon: TrendingUp, feature: 'enableCostAnalysis' },
  { name: 'Optimization', href: '/optimization', icon: TrendingUp, feature: 'enableOptimization' },
  { name: 'Budgets', href: '/budgets', icon: DollarSign, feature: 'enableBudgetManagement' },
  { name: 'Reports', href: '/reports', icon: BarChart3, feature: 'enableReporting' },
]

const userNavigation = [
  { name: 'Profile', href: '/profile' },
  { name: 'Settings', href: '/settings' },
]

export function Layout() {
  const { user, logout } = useAuth()
  const { theme, actualTheme, toggleTheme } = useTheme()
  const location = useLocation()
  const navigate = useNavigate()
  
  const [sidebarOpen, setSidebarOpen] = React.useState(false)
  const [searchOpen, setSearchOpen] = React.useState(false)
  const [notificationsOpen, setNotificationsOpen] = React.useState(false)
  const [isPending, startTransition] = useTransition()
  
  // React 19 useOptimistic for navigation state
  const [optimisticLocation, setOptimisticLocation] = useOptimistic(
    location.pathname,
    (state, newLocation: string) => newLocation
  )

  const handleNavigation = (href: string) => {
    startTransition(() => {
      setOptimisticLocation(href)
      navigate(href)
      setSidebarOpen(false)
    })
  }

  const handleLogout = () => {
    startTransition(() => {
      logout()
    })
  }

  // Filter navigation based on feature flags
  const enabledNavigation = navigation.filter(item => {
    if (!item.feature) return true
    return useFeature(item.feature as any)
  })

  return (
    <>
      <Helmet>
        <title>FinOps-Teste - Enterprise Cost Optimization</title>
        <meta name="description" content="Comprehensive cloud cost optimization and management platform" />
      </Helmet>

      <div className="min-h-screen bg-background">
        {/* Mobile sidebar */}
        <div className={`fixed inset-0 z-50 lg:hidden ${sidebarOpen ? 'block' : 'hidden'}`}>
          <div className="fixed inset-0 bg-black/20" onClick={() => setSidebarOpen(false)} />
          <div className="fixed left-0 top-0 bottom-0 w-64 bg-card border-r border-border">
            <SidebarContent 
              navigation={enabledNavigation}
              currentPath={optimisticLocation}
              onNavigate={handleNavigation}
              isPending={isPending}
            />
          </div>
        </div>

        {/* Desktop sidebar */}
        <div className="hidden lg:fixed lg:inset-y-0 lg:left-0 lg:z-40 lg:w-64">
          <div className="flex h-full flex-col bg-card border-r border-border">
            <SidebarContent 
              navigation={enabledNavigation}
              currentPath={optimisticLocation}
              onNavigate={handleNavigation}
              isPending={isPending}
            />
          </div>
        </div>

        {/* Main content */}
        <div className="lg:pl-64">
          {/* Top navigation */}
          <header className="sticky top-0 z-30 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 border-b border-border">
            <div className="flex h-16 items-center justify-between px-4 sm:px-6 lg:px-8">
              {/* Mobile menu button */}
              <button
                type="button"
                className="lg:hidden p-2 rounded-md text-muted-foreground hover:text-foreground hover:bg-accent"
                onClick={() => setSidebarOpen(true)}
                aria-label="Open sidebar"
              >
                <Menu className="h-5 w-5" />
              </button>

              {/* Page title */}
              <div className="flex-1 lg:flex-none">
                <h1 className="text-lg font-semibold text-foreground">
                  {getPageTitle(optimisticLocation)}
                </h1>
              </div>

              {/* Right side actions */}
              <div className="flex items-center gap-2">
                {/* Search */}
                <button
                  type="button"
                  className="p-2 rounded-md text-muted-foreground hover:text-foreground hover:bg-accent"
                  onClick={() => setSearchOpen(true)}
                  aria-label="Search"
                >
                  <Search className="h-5 w-5" />
                </button>

                {/* Theme toggle */}
                <button
                  type="button"
                  className="p-2 rounded-md text-muted-foreground hover:text-foreground hover:bg-accent"
                  onClick={toggleTheme}
                  aria-label={`Switch to ${actualTheme === 'light' ? 'dark' : 'light'} theme`}
                >
                  {actualTheme === 'light' ? (
                    <Moon className="h-5 w-5" />
                  ) : (
                    <Sun className="h-5 w-5" />
                  )}
                </button>

                {/* Notifications */}
                <button
                  type="button"
                  className="relative p-2 rounded-md text-muted-foreground hover:text-foreground hover:bg-accent"
                  onClick={() => setNotificationsOpen(true)}
                  aria-label="Notifications"
                >
                  <Bell className="h-5 w-5" />
                  <span className="absolute top-1 right-1 h-2 w-2 bg-red-500 rounded-full" />
                </button>

                {/* User menu */}
                <UserMenu 
                  user={user}
                  userNavigation={userNavigation}
                  onNavigate={handleNavigation}
                  onLogout={handleLogout}
                  isPending={isPending}
                />
              </div>
            </div>
          </header>

          {/* Page content */}
          <main className="flex-1">
            <ErrorBoundary>
              <Suspense fallback={<PageLoadingFallback />}>
                <Outlet />
              </Suspense>
            </ErrorBoundary>
          </main>
        </div>

        {/* Search Command Palette */}
        <SearchCommand 
          open={searchOpen}
          onOpenChange={setSearchOpen}
          onNavigate={handleNavigation}
        />

        {/* Notification Center */}
        <NotificationCenter
          open={notificationsOpen}
          onOpenChange={setNotificationsOpen}
        />
      </div>
    </>
  )
}

// Server Component for sidebar content
function SidebarContent({ 
  navigation, 
  currentPath, 
  onNavigate, 
  isPending 
}: {
  navigation: NavigationItem[]
  currentPath: string
  onNavigate: (href: string) => void
  isPending: boolean
}) {
  return (
    <>
      {/* Logo */}
      <div className="flex h-16 items-center px-6 border-b border-border">
        <div className="flex items-center gap-2">
          <div className="h-8 w-8 rounded-lg bg-primary flex items-center justify-center">
            <DollarSign className="h-5 w-5 text-primary-foreground" />
          </div>
          <span className="text-lg font-semibold text-foreground">FinOps</span>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-4 py-4 space-y-1">
        {navigation.map((item) => {
          const isActive = currentPath === item.href
          const Icon = item.icon
          
          return (
            <button
              key={item.name}
              onClick={() => onNavigate(item.href)}
              disabled={isPending}
              className={`
                w-full flex items-center gap-3 px-3 py-2 text-sm font-medium rounded-lg
                transition-colors duration-200
                ${isActive 
                  ? 'bg-primary text-primary-foreground' 
                  : 'text-muted-foreground hover:text-foreground hover:bg-accent'
                }
                ${isPending ? 'opacity-50 cursor-not-allowed' : ''}
              `}
              aria-current={isActive ? 'page' : undefined}
            >
              <Icon className="h-5 w-5 flex-shrink-0" />
              <span className="truncate">{item.name}</span>
              {item.badge && (
                <span className="ml-auto bg-red-500 text-white text-xs rounded-full px-2 py-0.5 min-w-[1.25rem] text-center">
                  {item.badge}
                </span>
              )}
              {isPending && currentPath === item.href && (
                <LoadingSpinner size="sm" className="ml-auto" />
              )}
            </button>
          )
        })}
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-border">
        <div className="text-xs text-muted-foreground">
          <div>Version 1.0.0</div>
          <div>© 2024 FinOps-Teste</div>
        </div>
      </div>
    </>
  )
}

// Client Component for user menu
function UserMenu({ 
  user, 
  userNavigation, 
  onNavigate, 
  onLogout, 
  isPending 
}: {
  user: any
  userNavigation: { name: string; href: string }[]
  onNavigate: (href: string) => void
  onLogout: () => void
  isPending: boolean
}) {
  const [menuOpen, setMenuOpen] = React.useState(false)

  return (
    <div className="relative">
      <button
        type="button"
        className="flex items-center gap-2 p-2 rounded-md text-muted-foreground hover:text-foreground hover:bg-accent"
        onClick={() => setMenuOpen(!menuOpen)}
        aria-expanded={menuOpen}
        aria-label="User menu"
      >
        <div className="h-6 w-6 rounded-full bg-primary flex items-center justify-center">
          <User className="h-4 w-4 text-primary-foreground" />
        </div>
        <span className="hidden sm:block text-sm font-medium">
          {user?.fullName || 'User'}
        </span>
      </button>

      {menuOpen && (
        <>
          <div 
            className="fixed inset-0 z-10" 
            onClick={() => setMenuOpen(false)}
            aria-hidden="true"
          />
          <div className="absolute right-0 top-full mt-2 w-48 bg-card border border-border rounded-lg shadow-lg z-20">
            <div className="p-3 border-b border-border">
              <div className="text-sm font-medium text-foreground">
                {user?.fullName}
              </div>
              <div className="text-xs text-muted-foreground">
                {user?.email}
              </div>
            </div>
            
            <div className="py-1">
              {userNavigation.map((item) => (
                <button
                  key={item.name}
                  onClick={() => {
                    onNavigate(item.href)
                    setMenuOpen(false)
                  }}
                  disabled={isPending}
                  className="w-full text-left px-3 py-2 text-sm text-muted-foreground hover:text-foreground hover:bg-accent disabled:opacity-50"
                >
                  {item.name}
                </button>
              ))}
              
              <hr className="my-1 border-border" />
              
              <button
                onClick={() => {
                  onLogout()
                  setMenuOpen(false)
                }}
                disabled={isPending}
                className="w-full text-left px-3 py-2 text-sm text-muted-foreground hover:text-foreground hover:bg-accent disabled:opacity-50 flex items-center gap-2"
              >
                <LogOut className="h-4 w-4" />
                Sign out
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  )
}

function PageLoadingFallback() {
  return (
    <div className="flex items-center justify-center min-h-[400px]">
      <div className="text-center">
        <LoadingSpinner size="lg" />
        <p className="mt-4 text-sm text-muted-foreground">Loading page...</p>
      </div>
    </div>
  )
}

function getPageTitle(pathname: string): string {
  const routes: Record<string, string> = {
    '/dashboard': 'Dashboard',
    '/resources': 'Resources',
    '/cost-analysis': 'Cost Analysis',
    '/optimization': 'Optimization',
    '/budgets': 'Budgets',
    '/reports': 'Reports',
    '/profile': 'Profile',
    '/settings': 'Settings',
  }
  
  return routes[pathname] || 'FinOps-Teste'
}