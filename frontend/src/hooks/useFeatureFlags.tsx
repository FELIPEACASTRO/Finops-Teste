/**
 * Feature Flags Provider
 * Implements feature flag management following KNOWLEDGE_BASE.md specifications
 * Supports A/B testing and gradual rollouts
 */

import React, { createContext, useContext, useEffect, useState } from 'react'
import { FeatureFlags } from '@/types'

interface FeatureFlagContextType {
  flags: FeatureFlags
  isFeatureEnabled: (feature: keyof FeatureFlags) => boolean
  updateFlags: (newFlags: Partial<FeatureFlags>) => void
}

const defaultFlags: FeatureFlags = {
  enableCostAnalysis: true,
  enableOptimization: true,
  enableBudgetManagement: true,
  enableReporting: true,
  enableMLRecommendations: false, // Disabled by default for MVP
  enableRealTimeUpdates: true,
  enableAdvancedFilters: true,
  enableDataExport: true,
}

const FeatureFlagContext = createContext<FeatureFlagContextType | undefined>(undefined)

export function FeatureFlagProvider({ children }: { children: React.ReactNode }) {
  const [flags, setFlags] = useState<FeatureFlags>(defaultFlags)

  // Load feature flags from API or localStorage
  useEffect(() => {
    const loadFeatureFlags = async () => {
      try {
        // Try to load from API first
        const response = await fetch('/api/v1/feature-flags')
        if (response.ok) {
          const apiFlags = await response.json()
          setFlags({ ...defaultFlags, ...apiFlags })
          return
        }
      } catch (error) {
        console.warn('Failed to load feature flags from API:', error)
      }

      // Fallback to localStorage
      const storedFlags = localStorage.getItem('finops_feature_flags')
      if (storedFlags) {
        try {
          const parsedFlags = JSON.parse(storedFlags)
          setFlags({ ...defaultFlags, ...parsedFlags })
        } catch (error) {
          console.warn('Failed to parse stored feature flags:', error)
        }
      }
    }

    loadFeatureFlags()
  }, [])

  const isFeatureEnabled = (feature: keyof FeatureFlags): boolean => {
    return flags[feature] === true
  }

  const updateFlags = (newFlags: Partial<FeatureFlags>) => {
    const updatedFlags = { ...flags, ...newFlags }
    setFlags(updatedFlags)
    localStorage.setItem('finops_feature_flags', JSON.stringify(updatedFlags))
  }

  const contextValue: FeatureFlagContextType = {
    flags,
    isFeatureEnabled,
    updateFlags,
  }

  return (
    <FeatureFlagContext.Provider value={contextValue}>
      {children}
    </FeatureFlagContext.Provider>
  )
}

export function useFeatureFlags(): FeatureFlagContextType {
  const context = useContext(FeatureFlagContext)
  if (context === undefined) {
    throw new Error('useFeatureFlags must be used within a FeatureFlagProvider')
  }
  return context
}

// Hook for checking individual features
export function useFeature(feature: keyof FeatureFlags): boolean {
  const { isFeatureEnabled } = useFeatureFlags()
  return isFeatureEnabled(feature)
}