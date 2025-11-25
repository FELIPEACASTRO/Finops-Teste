/**
 * Loading Spinner Component
 * Implements WCAG 2.2 AA accessibility standards from KNOWLEDGE_BASE.md
 * 
 * Features:
 * - Screen reader announcements
 * - Reduced motion support
 * - High contrast mode support
 * - Semantic HTML
 * - Proper ARIA attributes
 */

import React from 'react'
import { cn } from '@/utils/cn'

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg' | 'xl'
  className?: string
  label?: string
  showLabel?: boolean
  variant?: 'default' | 'primary' | 'secondary'
}

const sizeClasses = {
  sm: 'h-4 w-4',
  md: 'h-6 w-6', 
  lg: 'h-8 w-8',
  xl: 'h-12 w-12',
}

const variantClasses = {
  default: 'text-muted-foreground',
  primary: 'text-primary',
  secondary: 'text-secondary',
}

export function LoadingSpinner({ 
  size = 'md',
  className,
  label = 'Loading',
  showLabel = false,
  variant = 'default'
}: LoadingSpinnerProps) {
  const spinnerClasses = cn(
    'animate-spin rounded-full border-2 border-current border-t-transparent',
    sizeClasses[size],
    variantClasses[variant],
    // Reduced motion support
    'motion-reduce:animate-pulse',
    className
  )

  return (
    <div 
      className="flex items-center justify-center gap-2"
      role="status"
      aria-live="polite"
      aria-label={label}
    >
      <div 
        className={spinnerClasses}
        aria-hidden="true"
      />
      
      {showLabel && (
        <span className="text-sm text-muted-foreground">
          {label}...
        </span>
      )}
      
      {/* Screen reader only text */}
      <span className="sr-only">
        {label}, please wait
      </span>
    </div>
  )
}

// Skeleton loader for content placeholders
export function Skeleton({ 
  className,
  ...props 
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        'animate-pulse rounded-md bg-muted',
        // Reduced motion support
        'motion-reduce:animate-none motion-reduce:bg-muted/50',
        className
      )}
      role="presentation"
      aria-hidden="true"
      {...props}
    />
  )
}

// Specific skeleton variants
export function SkeletonText({ 
  lines = 1,
  className 
}: { 
  lines?: number
  className?: string 
}) {
  return (
    <div className={cn('space-y-2', className)} role="presentation" aria-hidden="true">
      {Array.from({ length: lines }).map((_, i) => (
        <Skeleton 
          key={i}
          className={cn(
            'h-4',
            i === lines - 1 ? 'w-3/4' : 'w-full' // Last line shorter
          )}
        />
      ))}
    </div>
  )
}

export function SkeletonCard({ className }: { className?: string }) {
  return (
    <div className={cn('space-y-3', className)} role="presentation" aria-hidden="true">
      <Skeleton className="h-4 w-3/4" />
      <Skeleton className="h-4 w-1/2" />
      <Skeleton className="h-20 w-full" />
    </div>
  )
}

export function SkeletonTable({ 
  rows = 5,
  columns = 4,
  className 
}: { 
  rows?: number
  columns?: number
  className?: string 
}) {
  return (
    <div className={cn('space-y-3', className)} role="presentation" aria-hidden="true">
      {/* Header */}
      <div className="flex gap-4">
        {Array.from({ length: columns }).map((_, i) => (
          <Skeleton key={i} className="h-4 flex-1" />
        ))}
      </div>
      
      {/* Rows */}
      {Array.from({ length: rows }).map((_, rowIndex) => (
        <div key={rowIndex} className="flex gap-4">
          {Array.from({ length: columns }).map((_, colIndex) => (
            <Skeleton key={colIndex} className="h-4 flex-1" />
          ))}
        </div>
      ))}
    </div>
  )
}

// Loading states for specific components
export function LoadingButton({ 
  children, 
  isLoading = false,
  disabled = false,
  className,
  ...props 
}: React.ButtonHTMLAttributes<HTMLButtonElement> & {
  isLoading?: boolean
}) {
  return (
    <button
      className={cn(
        'btn btn-primary btn-md',
        'disabled:opacity-50 disabled:cursor-not-allowed',
        className
      )}
      disabled={disabled || isLoading}
      aria-busy={isLoading}
      {...props}
    >
      {isLoading && (
        <LoadingSpinner 
          size="sm" 
          className="mr-2" 
          label="Processing"
        />
      )}
      {children}
    </button>
  )
}

// Loading overlay for content areas
export function LoadingOverlay({ 
  isLoading = false,
  children,
  label = 'Loading content',
  className
}: {
  isLoading?: boolean
  children: React.ReactNode
  label?: string
  className?: string
}) {
  return (
    <div className={cn('relative', className)}>
      {children}
      
      {isLoading && (
        <div 
          className="absolute inset-0 bg-background/80 backdrop-blur-sm flex items-center justify-center z-10"
          role="status"
          aria-live="polite"
          aria-label={label}
        >
          <div className="text-center">
            <LoadingSpinner size="lg" />
            <p className="mt-2 text-sm text-muted-foreground">
              {label}...
            </p>
          </div>
        </div>
      )}
    </div>
  )
}

// Progress indicator for multi-step processes
export function ProgressSpinner({ 
  progress = 0,
  size = 'md',
  className,
  label = 'Progress'
}: {
  progress?: number // 0-100
  size?: 'sm' | 'md' | 'lg'
  className?: string
  label?: string
}) {
  const radius = size === 'sm' ? 16 : size === 'md' ? 20 : 24
  const circumference = 2 * Math.PI * radius
  const strokeDashoffset = circumference - (progress / 100) * circumference
  
  const svgSize = size === 'sm' ? 40 : size === 'md' ? 48 : 56

  return (
    <div 
      className={cn('flex items-center justify-center', className)}
      role="progressbar"
      aria-valuenow={progress}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-label={`${label}: ${progress}% complete`}
    >
      <div className="relative">
        <svg
          width={svgSize}
          height={svgSize}
          className="transform -rotate-90"
          aria-hidden="true"
        >
          {/* Background circle */}
          <circle
            cx={svgSize / 2}
            cy={svgSize / 2}
            r={radius}
            stroke="currentColor"
            strokeWidth="2"
            fill="none"
            className="text-muted"
          />
          
          {/* Progress circle */}
          <circle
            cx={svgSize / 2}
            cy={svgSize / 2}
            r={radius}
            stroke="currentColor"
            strokeWidth="2"
            fill="none"
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            className="text-primary transition-all duration-300 ease-in-out"
          />
        </svg>
        
        {/* Progress text */}
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="text-xs font-medium text-foreground">
            {Math.round(progress)}%
          </span>
        </div>
      </div>
      
      {/* Screen reader text */}
      <span className="sr-only">
        {label}: {progress}% complete
      </span>
    </div>
  )
}

// Pulse animation for live data
export function PulseIndicator({ 
  active = false,
  size = 'sm',
  className 
}: {
  active?: boolean
  size?: 'sm' | 'md' | 'lg'
  className?: string
}) {
  const sizeClass = size === 'sm' ? 'h-2 w-2' : size === 'md' ? 'h-3 w-3' : 'h-4 w-4'
  
  return (
    <div 
      className={cn(
        'rounded-full',
        sizeClass,
        active 
          ? 'bg-green-500 animate-pulse motion-reduce:animate-none' 
          : 'bg-muted',
        className
      )}
      role="status"
      aria-label={active ? 'Live data active' : 'Live data inactive'}
      title={active ? 'Live data active' : 'Live data inactive'}
    />
  )
}