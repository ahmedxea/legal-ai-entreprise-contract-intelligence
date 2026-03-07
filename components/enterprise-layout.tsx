"use client"

import { EnterpriseSidebar } from "./enterprise-sidebar"
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
    if (!isLoading && !isAuthenticated && pathname !== "/" && pathname !== "/login") {
      router.push("/login")
    }
  }, [isAuthenticated, isLoading, pathname, router])

  if (pathname === "/" || pathname === "/login") {
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
    <div className="flex h-screen overflow-hidden">
      <EnterpriseSidebar />
      <div className="flex-1 flex flex-col ml-64 transition-all duration-300">
        <EnterpriseHeader title={pageInfo.title} subtitle={pageInfo.subtitle} />
        <main className="flex-1 overflow-auto" style={{ background: "rgb(var(--background))" }}>
          <div className="p-6 max-w-[1600px] mx-auto">
            {children}
          </div>
        </main>
      </div>
    </div>
  )
}
