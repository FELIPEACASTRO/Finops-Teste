/**
 * Authentication Hook with React 19 Features
 * Implements JWT authentication with optimistic updates and actions
 * Following KNOWLEDGE_BASE.md specifications for React 19 best practices
 */

import React, { createContext, useContext, useReducer, useOptimistic, useCallback } from 'react'
import { User, LoginRequest, LoginResponse, AuthTokens } from '@/types'
import { authService } from '@/services/auth'
import toast from 'react-hot-toast'

interface AuthState {
  user: User | null
  tokens: AuthTokens | null
  isLoading: boolean
  isAuthenticated: boolean
  error: string | null
}

interface AuthContextType extends AuthState {
  login: (credentials: LoginRequest) => Promise<void>
  logout: () => void
  refreshToken: () => Promise<void>
  updateUser: (userData: Partial<User>) => void
}

const initialState: AuthState = {
  user: null,
  tokens: null,
  isLoading: true,
  isAuthenticated: false,
  error: null,
}

type AuthAction =
  | { type: 'LOGIN_START' }
  | { type: 'LOGIN_SUCCESS'; payload: { user: User; tokens: AuthTokens } }
  | { type: 'LOGIN_FAILURE'; payload: string }
  | { type: 'LOGOUT' }
  | { type: 'UPDATE_USER'; payload: Partial<User> }
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'CLEAR_ERROR' }

function authReducer(state: AuthState, action: AuthAction): AuthState {
  switch (action.type) {
    case 'LOGIN_START':
      return {
        ...state,
        isLoading: true,
        error: null,
      }
    case 'LOGIN_SUCCESS':
      return {
        ...state,
        user: action.payload.user,
        tokens: action.payload.tokens,
        isLoading: false,
        isAuthenticated: true,
        error: null,
      }
    case 'LOGIN_FAILURE':
      return {
        ...state,
        user: null,
        tokens: null,
        isLoading: false,
        isAuthenticated: false,
        error: action.payload,
      }
    case 'LOGOUT':
      return {
        ...state,
        user: null,
        tokens: null,
        isAuthenticated: false,
        error: null,
      }
    case 'UPDATE_USER':
      return {
        ...state,
        user: state.user ? { ...state.user, ...action.payload } : null,
      }
    case 'SET_LOADING':
      return {
        ...state,
        isLoading: action.payload,
      }
    case 'CLEAR_ERROR':
      return {
        ...state,
        error: null,
      }
    default:
      return state
  }
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [state, dispatch] = useReducer(authReducer, initialState)
  
  // React 19 useOptimistic for user updates
  const [optimisticUser, updateOptimisticUser] = useOptimistic(
    state.user,
    (currentUser, newUserData: Partial<User>) => 
      currentUser ? { ...currentUser, ...newUserData } : null
  )

  // Initialize auth state from localStorage
  React.useEffect(() => {
    const initializeAuth = async () => {
      try {
        const storedTokens = localStorage.getItem('finops_tokens')
        const storedUser = localStorage.getItem('finops_user')

        if (storedTokens && storedUser) {
          const tokens: AuthTokens = JSON.parse(storedTokens)
          const user: User = JSON.parse(storedUser)

          // Verify token validity
          const isValid = await authService.verifyToken(tokens.accessToken)
          
          if (isValid) {
            dispatch({
              type: 'LOGIN_SUCCESS',
              payload: { user, tokens }
            })
          } else {
            // Try to refresh token
            try {
              const refreshResponse = await authService.refreshToken(tokens.refreshToken)
              dispatch({
                type: 'LOGIN_SUCCESS',
                payload: refreshResponse
              })
              localStorage.setItem('finops_tokens', JSON.stringify(refreshResponse.tokens))
            } catch {
              // Clear invalid tokens
              localStorage.removeItem('finops_tokens')
              localStorage.removeItem('finops_user')
            }
          }
        }
      } catch (error) {
        console.error('Auth initialization error:', error)
      } finally {
        dispatch({ type: 'SET_LOADING', payload: false })
      }
    }

    initializeAuth()
  }, [])

  // React 19 Actions API for login
  const login = useCallback(async (credentials: LoginRequest) => {
    dispatch({ type: 'LOGIN_START' })
    
    try {
      const response = await authService.login(credentials)
      
      // Store tokens and user data
      localStorage.setItem('finops_tokens', JSON.stringify(response.tokens))
      localStorage.setItem('finops_user', JSON.stringify(response.user))
      
      dispatch({
        type: 'LOGIN_SUCCESS',
        payload: response
      })
      
      toast.success(`Welcome back, ${response.user.fullName}!`)
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || 'Login failed'
      dispatch({
        type: 'LOGIN_FAILURE',
        payload: errorMessage
      })
      toast.error(errorMessage)
      throw error
    }
  }, [])

  const logout = useCallback(() => {
    localStorage.removeItem('finops_tokens')
    localStorage.removeItem('finops_user')
    dispatch({ type: 'LOGOUT' })
    toast.success('Logged out successfully')
  }, [])

  const refreshToken = useCallback(async () => {
    if (!state.tokens?.refreshToken) {
      throw new Error('No refresh token available')
    }

    try {
      const response = await authService.refreshToken(state.tokens.refreshToken)
      
      localStorage.setItem('finops_tokens', JSON.stringify(response.tokens))
      localStorage.setItem('finops_user', JSON.stringify(response.user))
      
      dispatch({
        type: 'LOGIN_SUCCESS',
        payload: response
      })
    } catch (error) {
      logout()
      throw error
    }
  }, [state.tokens?.refreshToken, logout])

  // Optimistic user updates
  const updateUser = useCallback((userData: Partial<User>) => {
    // Optimistic update
    updateOptimisticUser(userData)
    
    // Actual update
    dispatch({ type: 'UPDATE_USER', payload: userData })
    
    // Update localStorage
    if (state.user) {
      const updatedUser = { ...state.user, ...userData }
      localStorage.setItem('finops_user', JSON.stringify(updatedUser))
    }
  }, [state.user, updateOptimisticUser])

  const contextValue: AuthContextType = {
    ...state,
    user: optimisticUser, // Use optimistic user for better UX
    login,
    logout,
    refreshToken,
    updateUser,
  }

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

// React 19 Server Action for login form
export async function loginAction(prevState: any, formData: FormData) {
  const email = formData.get('email') as string
  const password = formData.get('password') as string

  if (!email || !password) {
    return {
      success: false,
      error: 'Email and password are required',
    }
  }

  try {
    const response = await authService.login({ email, password })
    
    // Store tokens (this would be handled by the hook in a real app)
    localStorage.setItem('finops_tokens', JSON.stringify(response.tokens))
    localStorage.setItem('finops_user', JSON.stringify(response.user))
    
    return {
      success: true,
      user: response.user,
    }
  } catch (error: any) {
    return {
      success: false,
      error: error.response?.data?.detail || 'Login failed',
    }
  }
}