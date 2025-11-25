/**
 * Web Vitals Monitoring Hook
 * Implements Core Web Vitals monitoring following KNOWLEDGE_BASE.md specifications
 * 
 * Tracks:
 * - LCP (Largest Contentful Paint) < 2.5s
 * - FID (First Input Delay) < 100ms  
 * - CLS (Cumulative Layout Shift) < 0.1
 * - INP (Interaction to Next Paint) < 200ms
 * - TTFB (Time to First Byte) < 600ms
 * - FCP (First Contentful Paint) < 1.8s
 */

import { useEffect, useCallback } from 'react'
import { onCLS, onFID, onLCP, onINP, onFCP, onTTFB, Metric } from 'web-vitals'

interface WebVitalsConfig {
  enableAnalytics?: boolean
  enableConsoleLogging?: boolean
  enablePerformanceAPI?: boolean
  thresholds?: {
    LCP: number
    FID: number
    CLS: number
    INP: number
    TTFB: number
    FCP: number
  }
}

interface WebVitalsMetric extends Metric {
  isGood?: boolean
  isNeedsImprovement?: boolean
  isPoor?: boolean
  threshold?: {
    good: number
    needsImprovement: number
  }
}

const DEFAULT_THRESHOLDS = {
  LCP: 2500,  // 2.5s
  FID: 100,   // 100ms
  CLS: 0.1,   // 0.1
  INP: 200,   // 200ms
  TTFB: 600,  // 600ms
  FCP: 1800,  // 1.8s
}

const THRESHOLDS_CONFIG = {
  LCP: { good: 2500, needsImprovement: 4000 },
  FID: { good: 100, needsImprovement: 300 },
  CLS: { good: 0.1, needsImprovement: 0.25 },
  INP: { good: 200, needsImprovement: 500 },
  TTFB: { good: 600, needsImprovement: 1500 },
  FCP: { good: 1800, needsImprovement: 3000 },
}

export function useWebVitals(config: WebVitalsConfig = {}) {
  const {
    enableAnalytics = true,
    enableConsoleLogging = process.env.NODE_ENV === 'development',
    enablePerformanceAPI = true,
    thresholds = DEFAULT_THRESHOLDS,
  } = config

  const reportWebVitals = useCallback((metric: Metric) => {
    const enhancedMetric: WebVitalsMetric = {
      ...metric,
      threshold: THRESHOLDS_CONFIG[metric.name as keyof typeof THRESHOLDS_CONFIG],
    }

    // Determine metric quality
    const threshold = enhancedMetric.threshold
    if (threshold) {
      enhancedMetric.isGood = metric.value <= threshold.good
      enhancedMetric.isNeedsImprovement = 
        metric.value > threshold.good && metric.value <= threshold.needsImprovement
      enhancedMetric.isPoor = metric.value > threshold.needsImprovement
    }

    // Console logging for development
    if (enableConsoleLogging) {
      const status = enhancedMetric.isGood ? '✅' : 
                    enhancedMetric.isNeedsImprovement ? '⚠️' : '❌'
      
      console.group(`${status} Web Vital: ${metric.name}`)
      console.log(`Value: ${metric.value}${getMetricUnit(metric.name)}`)
      console.log(`Rating: ${metric.rating}`)
      console.log(`Delta: ${metric.delta}${getMetricUnit(metric.name)}`)
      if (threshold) {
        console.log(`Threshold (Good): ${threshold.good}${getMetricUnit(metric.name)}`)
        console.log(`Threshold (Needs Improvement): ${threshold.needsImprovement}${getMetricUnit(metric.name)}`)
      }
      console.log('Navigation Type:', metric.navigationType)
      console.groupEnd()
    }

    // Send to analytics
    if (enableAnalytics) {
      sendToAnalytics(enhancedMetric)
    }

    // Send to Performance API
    if (enablePerformanceAPI && 'sendBeacon' in navigator) {
      sendToPerformanceAPI(enhancedMetric)
    }

    // Store in session storage for debugging
    storeMetricForDebugging(enhancedMetric)

  }, [enableAnalytics, enableConsoleLogging, enablePerformanceAPI])

  useEffect(() => {
    // Register all Core Web Vitals observers
    onCLS(reportWebVitals)
    onFID(reportWebVitals)
    onLCP(reportWebVitals)
    onINP(reportWebVitals)
    onFCP(reportWebVitals)
    onTTFB(reportWebVitals)

    // Additional performance monitoring
    if (enablePerformanceAPI) {
      monitorResourceTiming()
      monitorNavigationTiming()
      monitorLongTasks()
    }

    // Cleanup function
    return () => {
      // Web Vitals library handles cleanup automatically
    }
  }, [reportWebVitals, enablePerformanceAPI])

  return {
    reportWebVitals,
    getStoredMetrics: () => getStoredMetrics(),
    clearStoredMetrics: () => clearStoredMetrics(),
  }
}

function getMetricUnit(metricName: string): string {
  switch (metricName) {
    case 'CLS':
      return ''
    case 'LCP':
    case 'FID':
    case 'INP':
    case 'TTFB':
    case 'FCP':
      return 'ms'
    default:
      return ''
  }
}

function sendToAnalytics(metric: WebVitalsMetric) {
  // Send to your analytics service
  if (typeof gtag !== 'undefined') {
    // Google Analytics 4
    gtag('event', metric.name, {
      event_category: 'Web Vitals',
      event_label: metric.id,
      value: Math.round(metric.name === 'CLS' ? metric.value * 1000 : metric.value),
      custom_map: {
        metric_rating: metric.rating,
        metric_delta: metric.delta,
        metric_is_good: metric.isGood,
        metric_navigation_type: metric.navigationType,
      },
    })
  }

  // Send to custom analytics endpoint
  fetch('/api/v1/analytics/web-vitals', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      name: metric.name,
      value: metric.value,
      rating: metric.rating,
      delta: metric.delta,
      id: metric.id,
      navigationType: metric.navigationType,
      isGood: metric.isGood,
      isNeedsImprovement: metric.isNeedsImprovement,
      isPoor: metric.isPoor,
      url: window.location.href,
      userAgent: navigator.userAgent,
      timestamp: Date.now(),
    }),
  }).catch(error => {
    console.warn('Failed to send web vitals to analytics:', error)
  })
}

function sendToPerformanceAPI(metric: WebVitalsMetric) {
  const data = JSON.stringify({
    type: 'web-vital',
    name: metric.name,
    value: metric.value,
    rating: metric.rating,
    url: window.location.href,
    timestamp: Date.now(),
  })

  if (navigator.sendBeacon) {
    navigator.sendBeacon('/api/v1/performance/beacon', data)
  }
}

function storeMetricForDebugging(metric: WebVitalsMetric) {
  try {
    const stored = sessionStorage.getItem('finops_web_vitals') || '[]'
    const metrics = JSON.parse(stored)
    
    metrics.push({
      ...metric,
      timestamp: Date.now(),
      url: window.location.href,
    })

    // Keep only last 50 metrics
    if (metrics.length > 50) {
      metrics.splice(0, metrics.length - 50)
    }

    sessionStorage.setItem('finops_web_vitals', JSON.stringify(metrics))
  } catch (error) {
    console.warn('Failed to store web vitals metric:', error)
  }
}

function getStoredMetrics(): WebVitalsMetric[] {
  try {
    const stored = sessionStorage.getItem('finops_web_vitals') || '[]'
    return JSON.parse(stored)
  } catch (error) {
    console.warn('Failed to retrieve stored web vitals:', error)
    return []
  }
}

function clearStoredMetrics() {
  try {
    sessionStorage.removeItem('finops_web_vitals')
  } catch (error) {
    console.warn('Failed to clear stored web vitals:', error)
  }
}

function monitorResourceTiming() {
  if (!('PerformanceObserver' in window)) return

  try {
    const observer = new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        if (entry.entryType === 'resource') {
          const resourceEntry = entry as PerformanceResourceTiming
          
          // Monitor slow resources
          if (resourceEntry.duration > 1000) {
            console.warn('Slow resource detected:', {
              name: resourceEntry.name,
              duration: resourceEntry.duration,
              size: resourceEntry.transferSize,
              type: resourceEntry.initiatorType,
            })

            // Send to analytics
            fetch('/api/v1/analytics/slow-resource', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                url: resourceEntry.name,
                duration: resourceEntry.duration,
                size: resourceEntry.transferSize,
                type: resourceEntry.initiatorType,
                timestamp: Date.now(),
              }),
            }).catch(() => {}) // Ignore errors
          }
        }
      }
    })

    observer.observe({ entryTypes: ['resource'] })
  } catch (error) {
    console.warn('Failed to set up resource timing monitoring:', error)
  }
}

function monitorNavigationTiming() {
  if (!('PerformanceObserver' in window)) return

  try {
    const observer = new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        if (entry.entryType === 'navigation') {
          const navEntry = entry as PerformanceNavigationTiming
          
          const timings = {
            dns: navEntry.domainLookupEnd - navEntry.domainLookupStart,
            tcp: navEntry.connectEnd - navEntry.connectStart,
            ssl: navEntry.connectEnd - navEntry.secureConnectionStart,
            ttfb: navEntry.responseStart - navEntry.requestStart,
            download: navEntry.responseEnd - navEntry.responseStart,
            domInteractive: navEntry.domInteractive - navEntry.navigationStart,
            domComplete: navEntry.domComplete - navEntry.navigationStart,
            loadComplete: navEntry.loadEventEnd - navEntry.navigationStart,
          }

          // Send navigation timings to analytics
          fetch('/api/v1/analytics/navigation-timing', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              ...timings,
              navigationType: navEntry.type,
              url: window.location.href,
              timestamp: Date.now(),
            }),
          }).catch(() => {}) // Ignore errors
        }
      }
    })

    observer.observe({ entryTypes: ['navigation'] })
  } catch (error) {
    console.warn('Failed to set up navigation timing monitoring:', error)
  }
}

function monitorLongTasks() {
  if (!('PerformanceObserver' in window)) return

  try {
    const observer = new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        if (entry.entryType === 'longtask') {
          console.warn('Long task detected:', {
            duration: entry.duration,
            startTime: entry.startTime,
            name: entry.name,
          })

          // Send long task info to analytics
          fetch('/api/v1/analytics/long-task', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              duration: entry.duration,
              startTime: entry.startTime,
              url: window.location.href,
              timestamp: Date.now(),
            }),
          }).catch(() => {}) // Ignore errors
        }
      }
    })

    observer.observe({ entryTypes: ['longtask'] })
  } catch (error) {
    console.warn('Failed to set up long task monitoring:', error)
  }
}

// Hook for getting real-time performance metrics
export function usePerformanceMetrics() {
  const getMetrics = useCallback(() => {
    if (!('performance' in window)) return null

    const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming
    if (!navigation) return null

    return {
      // Core timings
      ttfb: navigation.responseStart - navigation.requestStart,
      fcp: performance.getEntriesByName('first-contentful-paint')[0]?.startTime || 0,
      domInteractive: navigation.domInteractive - navigation.navigationStart,
      domComplete: navigation.domComplete - navigation.navigationStart,
      loadComplete: navigation.loadEventEnd - navigation.navigationStart,

      // Network timings
      dns: navigation.domainLookupEnd - navigation.domainLookupStart,
      tcp: navigation.connectEnd - navigation.connectStart,
      ssl: navigation.connectEnd - navigation.secureConnectionStart,
      download: navigation.responseEnd - navigation.responseStart,

      // Resource counts
      resourceCount: performance.getEntriesByType('resource').length,
      
      // Memory info (if available)
      memory: (performance as any).memory ? {
        used: (performance as any).memory.usedJSHeapSize,
        total: (performance as any).memory.totalJSHeapSize,
        limit: (performance as any).memory.jsHeapSizeLimit,
      } : null,
    }
  }, [])

  return { getMetrics }
}

// Component for displaying Web Vitals in development
export function WebVitalsDebugger() {
  const { getStoredMetrics, clearStoredMetrics } = useWebVitals()
  
  if (process.env.NODE_ENV !== 'development') {
    return null
  }

  const metrics = getStoredMetrics()
  const latestMetrics = metrics.reduce((acc, metric) => {
    acc[metric.name] = metric
    return acc
  }, {} as Record<string, WebVitalsMetric>)

  return (
    <div 
      style={{
        position: 'fixed',
        bottom: '10px',
        right: '10px',
        background: 'rgba(0, 0, 0, 0.8)',
        color: 'white',
        padding: '10px',
        borderRadius: '5px',
        fontSize: '12px',
        fontFamily: 'monospace',
        zIndex: 9999,
        maxWidth: '300px',
      }}
    >
      <div style={{ marginBottom: '10px', fontWeight: 'bold' }}>
        Web Vitals Debug
        <button
          onClick={clearStoredMetrics}
          style={{
            marginLeft: '10px',
            background: 'red',
            color: 'white',
            border: 'none',
            padding: '2px 6px',
            borderRadius: '3px',
            fontSize: '10px',
          }}
        >
          Clear
        </button>
      </div>
      
      {Object.entries(latestMetrics).map(([name, metric]) => (
        <div key={name} style={{ marginBottom: '5px' }}>
          <span style={{ 
            color: metric.isGood ? '#4ade80' : 
                   metric.isNeedsImprovement ? '#fbbf24' : '#ef4444' 
          }}>
            {name}: {metric.value.toFixed(name === 'CLS' ? 3 : 0)}{getMetricUnit(name)}
          </span>
          <span style={{ marginLeft: '10px', opacity: 0.7 }}>
            ({metric.rating})
          </span>
        </div>
      ))}
    </div>
  )
}