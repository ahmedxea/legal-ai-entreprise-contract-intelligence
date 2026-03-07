"use client"

import { createContext, useContext, useState, useEffect, type ReactNode } from "react"
import { config } from "./config"
import { apiClient } from "./api-client"

const API_URL = config.apiUrl

interface User {
  id: string
  email: string
  name: string
  full_name?: string
  organization?: string
  role?: string
}

interface AuthContextType {
  user: User | null
  token: string | null
  signIn: (email: string, password: string) => Promise<{ success: boolean; error?: string }>
  signUp: (email: string, password: string, name: string, organization?: string) => Promise<{ success: boolean; error?: string }>
  signOut: () => void
  isLoading: boolean
  isAuthenticated: boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  // Keep the apiClient singleton in sync with the current auth token
  useEffect(() => {
    apiClient.setToken(token)
  }, [token])
  useEffect(() => {
    const savedToken = localStorage.getItem("lexra_token")
    const savedUser = localStorage.getItem("lexra_user")

    if (savedToken && savedUser) {
      setToken(savedToken)
      setUser(JSON.parse(savedUser))

      // Validate token with backend
      fetch(`${API_URL}/api/auth/me`, {
        headers: { Authorization: `Bearer ${savedToken}` },
      })
        .then((res) => {
          if (!res.ok) {
            // Token expired — clear session
            localStorage.removeItem("lexra_token")
            localStorage.removeItem("lexra_user")
            setToken(null)
            setUser(null)
          }
        })
        .catch(() => {
          // Backend unreachable — keep local session for now
        })
        .finally(() => setIsLoading(false))
    } else {
      setIsLoading(false)
    }
  }, [])

  const signIn = async (email: string, password: string): Promise<{ success: boolean; error?: string }> => {
    try {
      const res = await fetch(`${API_URL}/api/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      })

      if (!res.ok) {
        const data = await res.json()
        return { success: false, error: data.detail || "Invalid email or password" }
      }

      const data = await res.json()
      const userData: User = {
        id: data.user.id,
        email: data.user.email,
        name: data.user.full_name || data.user.name || email.split("@")[0],
        full_name: data.user.full_name,
        organization: data.user.organization,
        role: data.user.role,
      }

      setToken(data.token)
      setUser(userData)
      localStorage.setItem("lexra_token", data.token)
      localStorage.setItem("lexra_user", JSON.stringify(userData))

      return { success: true }
    } catch {
      return { success: false, error: "Unable to connect to server" }
    }
  }

  const signUp = async (
    email: string,
    password: string,
    name: string,
    organization?: string
  ): Promise<{ success: boolean; error?: string }> => {
    try {
      const res = await fetch(`${API_URL}/api/auth/signup`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email,
          password,
          full_name: name,
          organization: organization || "",
        }),
      })

      if (!res.ok) {
        const data = await res.json()
        return { success: false, error: data.detail || "Sign up failed" }
      }

      const data = await res.json()
      const userData: User = {
        id: data.user.id,
        email: data.user.email,
        name: data.user.full_name || data.user.name || name,
        full_name: data.user.full_name,
        organization: data.user.organization,
        role: data.user.role,
      }

      setToken(data.token)
      setUser(userData)
      localStorage.setItem("lexra_token", data.token)
      localStorage.setItem("lexra_user", JSON.stringify(userData))

      return { success: true }
    } catch {
      return { success: false, error: "Unable to connect to server" }
    }
  }

  const signOut = () => {
    if (token) {
      fetch(`${API_URL}/api/auth/logout`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      }).catch(() => {})
    }

    setToken(null)
    setUser(null)
    localStorage.removeItem("lexra_token")
    localStorage.removeItem("lexra_user")
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        signIn,
        signUp,
        signOut,
        isLoading,
        isAuthenticated: !!user && !!token,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider")
  }
  return context
}
