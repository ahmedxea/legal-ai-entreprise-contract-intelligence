"use client"

import { createContext, useContext, useState, useEffect, type ReactNode } from "react"
import { config } from "./config"

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
  token: string | null  // always null — session is carried by HttpOnly cookie
  signIn: (email: string, password: string) => Promise<{ success: boolean; error?: string }>
  signUp: (email: string, password: string, name: string, organization?: string) => Promise<{ success: boolean; error?: string }>
  signOut: () => void
  isLoading: boolean
  isAuthenticated: boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    // Restore user for instant UI, then validate the HttpOnly cookie with backend
    const savedUser = localStorage.getItem("lexra_user")
    if (savedUser) {
      try { setUser(JSON.parse(savedUser)) } catch { localStorage.removeItem("lexra_user") }
    }

    fetch(`${API_URL}/api/auth/me`, { credentials: "include" })
      .then((res) => {
        if (!res.ok) {
          localStorage.removeItem("lexra_user")
          setUser(null)
          return null
        }
        return res.json()
      })
      .then((data) => {
        if (data?.user) {
          const u = data.user
          const userData: User = {
            id: u.id,
            email: u.email,
            name: u.full_name || u.name || u.email.split("@")[0],
            full_name: u.full_name,
            organization: u.organization,
            role: u.role,
          }
          setUser(userData)
          localStorage.setItem("lexra_user", JSON.stringify(userData))
        }
      })
      .catch(() => {
        // Backend unreachable — keep cached user
      })
      .finally(() => setIsLoading(false))
  }, [])

  const signIn = async (email: string, password: string): Promise<{ success: boolean; error?: string }> => {
    try {
      const res = await fetch(`${API_URL}/api/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
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

      setUser(userData)
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
        credentials: "include",
        body: JSON.stringify({ email, password, full_name: name, organization: organization || "" }),
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

      setUser(userData)
      localStorage.setItem("lexra_user", JSON.stringify(userData))
      return { success: true }
    } catch {
      return { success: false, error: "Unable to connect to server" }
    }
  }

  const signOut = () => {
    fetch(`${API_URL}/api/auth/logout`, {
      method: "POST",
      credentials: "include",
    }).catch(() => {})

    setUser(null)
    localStorage.removeItem("lexra_user")
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        token: null,
        signIn,
        signUp,
        signOut,
        isLoading,
        isAuthenticated: !!user,
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
