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
    <header className="h-16 border-b sticky top-0 z-50" style={{
      background: "linear-gradient(135deg, rgba(2,11,27,0.85) 0%, rgba(10,31,68,0.85) 100%)",
      backdropFilter: "blur(20px)",
      WebkitBackdropFilter: "blur(20px)",
      borderColor: "rgba(0,224,255,0.15)",
      boxShadow: "0 4px 24px rgba(0,0,0,0.4), 0 1px 0 rgba(0,224,255,0.08)",
    }}>
      <div className="h-full px-6 flex items-center justify-between">
        {/* Left: Page Title */}
        <div className="space-y-0.5 flex-shrink-0">
          <h1 className="text-xl font-bold tracking-tight text-white">
            {title}
          </h1>
          {subtitle && (
            <p className="text-xs text-[#CBD5E1]">
              {subtitle}
            </p>
          )}
        </div>

        {/* Center: Search */}
        <div className="relative hidden md:block group flex-1 max-w-sm mx-6">
          <Search className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-[#CBD5E1] transition-colors group-hover:text-[#00E0FF]" />
          <input
            type="text"
            placeholder="Search contracts..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={handleSearch}
            className="pl-10 pr-4 py-2 w-full text-sm rounded-lg transition-all duration-200 text-white placeholder-white/40 outline-none focus:shadow-[0_0_0_2px_rgba(0,224,255,0.3)]"
            style={{
              background: "rgba(255,255,255,0.07)",
              border: "1.5px solid rgba(0,224,255,0.2)",
            }}
          />
        </div>

        {/* Right: Actions */}
        <div className="flex items-center gap-2 flex-shrink-0">
          {/* Notifications */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <button
                className="p-2.5 rounded-xl hover:bg-white/10 hover:scale-105 transition-all duration-200 relative group"
                title="Notifications"
              >
                <Bell className="w-5 h-5 group-hover:rotate-12 transition-transform text-white/80 group-hover:text-[#00E0FF]" />
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
            className="p-2.5 rounded-xl hover:bg-white/10 hover:scale-105 transition-all duration-200 group"
            title={isDark ? "Light Mode" : "Dark Mode"}
          >
            {isDark ? (
              <Sun className="w-5 h-5 group-hover:rotate-12 transition-transform text-white/80 group-hover:text-[#00E0FF]" />
            ) : (
              <Moon className="w-5 h-5 group-hover:-rotate-12 transition-transform text-white/80 group-hover:text-[#00E0FF]" />
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
