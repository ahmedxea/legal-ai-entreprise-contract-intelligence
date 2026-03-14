"use client"

import { Bell, Search, Moon, Sun } from "lucide-react"
import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { DropdownMenu, DropdownMenuTrigger, DropdownMenuContent } from "@/components/ui/dropdown-menu"

interface EnterpriseHeaderProps {
  title: string
  subtitle?: string
}

export function EnterpriseHeader({ title, subtitle }: EnterpriseHeaderProps) {
  const [isDark, setIsDark] = useState(false)
  const [searchQuery, setSearchQuery] = useState("")
  const router = useRouter()

  const handleSearch = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && searchQuery.trim()) {
      router.push(`/contracts?q=${encodeURIComponent(searchQuery.trim())}`)
    }
  }

  useEffect(() => {
    const theme = localStorage.getItem("theme")
    if (theme === "dark" || (!theme && window.matchMedia("(prefers-color-scheme: dark)").matches)) {
      setIsDark(true)
      document.documentElement.classList.add("dark")
    }
  }, [])

  const toggleTheme = () => {
    const newTheme = !isDark
    setIsDark(newTheme)
    if (newTheme) {
      document.documentElement.classList.add("dark")
      localStorage.setItem("theme", "dark")
    } else {
      document.documentElement.classList.remove("dark")
      localStorage.setItem("theme", "light")
    }
  }

  return (
    <header className="h-16 border-b backdrop-blur-sm bg-card/95 sticky top-0 z-50" style={{ borderColor: "rgb(var(--border))" }}>
      <div className="h-full px-6 flex items-center justify-between">
        {/* Left: Page Title */}
        <div className="space-y-0.5">
          <h1 className="text-xl font-bold tracking-tight" style={{ color: "rgb(var(--foreground))" }}>
            {title}
          </h1>
          {subtitle && (
            <p className="text-xs" style={{ color: "rgb(var(--muted-foreground))" }}>
              {subtitle}
            </p>
          )}
        </div>

        {/* Right: Actions */}
        <div className="flex items-center gap-2">
          {/* Search */}
          <div className="relative hidden md:block group">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 transition-colors group-hover:text-primary" style={{ color: "rgb(var(--muted-foreground))" }} />
            <input
              type="text"
              placeholder="Search contracts..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={handleSearch}
              className="input-enterprise pl-9 pr-4 py-2 w-64 text-sm rounded-lg border transition-all duration-200 focus:w-72 focus:border-primary/50 focus:shadow-lg focus:shadow-primary/10"
              style={{
                background: "rgb(var(--background))",
                color: "rgb(var(--foreground))",
                border: `1.5px solid rgb(var(--border))`,
              }}
            />
          </div>

          {/* Notifications */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <button
                className="p-2.5 rounded-xl hover:bg-accent/80 hover:scale-105 transition-all duration-200 relative group"
                title="Notifications"
              >
                <Bell className="w-5 h-5 group-hover:rotate-12 transition-transform" style={{ color: "rgb(var(--foreground))" }} />
              </button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="glass-card border-primary/20 rounded-xl w-64 p-4">
              <p className="text-sm font-semibold mb-1" style={{ color: "rgb(var(--foreground))" }}>Notifications</p>
              <p className="text-xs" style={{ color: "rgb(var(--muted-foreground))" }}>No notifications yet.</p>
            </DropdownMenuContent>
          </DropdownMenu>

          {/* Theme Toggle */}
          <button
            onClick={toggleTheme}
            className="p-2.5 rounded-xl hover:bg-accent/80 hover:scale-105 transition-all duration-200 group"
            title={isDark ? "Light Mode" : "Dark Mode"}
          >
            {isDark ? (
              <Sun className="w-5 h-5 group-hover:rotate-12 transition-transform" style={{ color: "rgb(var(--foreground))" }} />
            ) : (
              <Moon className="w-5 h-5 group-hover:-rotate-12 transition-transform" style={{ color: "rgb(var(--foreground))" }} />
            )}
          </button>

          {/* Status Indicator */}
          <div className="hidden lg:flex items-center gap-2 px-3 py-2 rounded-full bg-emerald-500/10 border border-emerald-500/20">
            <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></div>
            <span className="text-xs font-semibold text-emerald-600 dark:text-emerald-400">
              Online
            </span>
          </div>
        </div>
      </div>
    </header>
  )
}
