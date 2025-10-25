"use client"

import { createContext, useContext, useState, useEffect, type ReactNode } from "react"

interface User {
  id: string
  email: string
  name: string
}

interface AuthContextType {
  user: User | null
  signIn: (email: string, password: string) => Promise<boolean>
  signUp: (email: string, password: string, name: string) => Promise<boolean>
  signOut: () => void
  isLoading: boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    // Check if user is logged in on mount
    const storedUser = localStorage.getItem("user")
    if (storedUser) {
      setUser(JSON.parse(storedUser))
    }
    setIsLoading(false)
  }, [])

  const signIn = async (email: string, password: string): Promise<boolean> => {
    // Simulate API call
    await new Promise((resolve) => setTimeout(resolve, 500))

    // Simple validation (in production, this would be a real API call)
    if (email && password.length >= 6) {
      const user = {
        id: Math.random().toString(36).substr(2, 9),
        email,
        name: email.split("@")[0],
      }
      setUser(user)
      localStorage.setItem("user", JSON.stringify(user))
      return true
    }
    return false
  }

  const signUp = async (email: string, password: string, name: string): Promise<boolean> => {
    // Simulate API call
    await new Promise((resolve) => setTimeout(resolve, 500))

    // Simple validation (in production, this would be a real API call)
    if (email && password.length >= 6 && name) {
      const user = {
        id: Math.random().toString(36).substr(2, 9),
        email,
        name,
      }
      setUser(user)
      localStorage.setItem("user", JSON.stringify(user))
      return true
    }
    return false
  }

  const signOut = () => {
    setUser(null)
    localStorage.removeItem("user")
  }

  return <AuthContext.Provider value={{ user, signIn, signUp, signOut, isLoading }}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider")
  }
  return context
}
