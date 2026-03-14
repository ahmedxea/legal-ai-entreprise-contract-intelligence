"use client"

import { EnterpriseHeader } from "./enterprise-header"
import { useAuth } from "@/lib/auth-context"
import { usePathname, useRouter } from "next/navigation"
import { useEffect } from "react"

interface EnterpriseLayoutProps {
  children: React.ReactNode
}

const pageTitles: Record<string, { title: string; subtitle?: string }> = {
  "/home": { title: "Lexra Dashboard", subtitle: "Overview of your contract portfolio" },
  "/contracts": { title: "Contracts", subtitle: "Manage and analyze your contracts" },
  "/risk": { title: "Risk Analysis", subtitle: "Identify and manage contract risks" },
  "/clauses": { title: "Clause Library", subtitle: "Browse and manage contract clauses" },
  "/settings": { title: "Settings", subtitle: "Configure your preferences" },
}

export function EnterpriseLayout({ children }: EnterpriseLayoutProps) {
  const pathname = usePathname()
  const { isLoading, isAuthenticated } = useAuth()
  const router = useRouter()
  const pageInfo = pageTitles[pathname] || { title: "Lexra Dashboard", subtitle: "" }

  useEffect(() => {
    if (!isLoading && !isAuthenticated && pathname !== "/" && pathname !== "/login" && pathname !== "/lexra") {
      router.push("/login")
    }
  }, [isAuthenticated, isLoading, pathname, router])

  if (pathname === "/" || pathname === "/login" || pathname === "/lexra") {
    return <>{children}</>
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen" style={{ background: "rgb(var(--background))" }}>
        <div className="text-center">
          <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-sm" style={{ color: "rgb(var(--muted-foreground))" }}>Loading...</p>
        </div>
      </div>
    )
  }

  if (!isAuthenticated) {
    return null
  }

  return (
    <div className="flex flex-col min-h-screen" style={{ background: "#020B1B" }}>
      {/* Subtle background grid — same as landing hero */}
      <div className="fixed inset-0 pointer-events-none" style={{
        backgroundImage: "linear-gradient(rgba(0,122,255,0.04) 1px, transparent 1px), linear-gradient(90deg, rgba(0,122,255,0.04) 1px, transparent 1px)",
        backgroundSize: "64px 64px",
        zIndex: 0,
      }} />
      {/* Ambient glow */}
      <div className="fixed top-0 right-0 w-[600px] h-[600px] pointer-events-none" style={{
        background: "radial-gradient(circle, rgba(0,122,255,0.06) 0%, transparent 70%)",
        zIndex: 0,
      }} />
      <EnterpriseHeader title={pageInfo.title} subtitle={pageInfo.subtitle} />
      <main className="flex-1 overflow-auto relative z-10">
        <div className="p-6 max-w-[1600px] mx-auto">
          {children}
        </div>
      </main>
    </div>
  )
}
