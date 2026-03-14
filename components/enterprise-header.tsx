"use client"

import { Bell, Search, Moon, Sun, FileText, LayoutDashboard, AlertTriangle, FileSearch, Settings, LogOut, ChevronDown } from "lucide-react"
import { useState, useEffect, useRef } from "react"
import { useRouter, usePathname } from "next/navigation"
import Link from "next/link"
import { useAuth } from "@/lib/auth-context"
import { DropdownMenu, DropdownMenuTrigger, DropdownMenuContent } from "@/components/ui/dropdown-menu"

interface EnterpriseHeaderProps {
  title: string
  subtitle?: string
}

const navItems = [
  { icon: LayoutDashboard, label: "Home", href: "/home" },
  { icon: FileText, label: "Contracts", href: "/contracts" },
  { icon: AlertTriangle, label: "Risk", href: "/risk" },
  { icon: FileSearch, label: "Clauses", href: "/clauses" },
  { icon: Settings, label: "Settings", href: "/settings" },
]

export function EnterpriseHeader({ title, subtitle }: EnterpriseHeaderProps) {
  const [isDark, setIsDark] = useState(false)
  const [searchQuery, setSearchQuery] = useState("")
  const pathname = usePathname()
  const router = useRouter()
  const { user, signOut } = useAuth()

  const initials = user?.name
    ? user.name.split(" ").map((n: string) => n[0]).join("").toUpperCase().slice(0, 2)
    : "?"

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

  const handleLogout = () => {
    signOut()
    router.push("/login")
  }

  return (
    <header className="h-16 sticky top-0 z-50 px-6 flex items-center justify-between" style={{
      background: "rgba(255, 255, 255, 0.75)",
      backdropFilter: "blur(24px)",
      WebkitBackdropFilter: "blur(24px)",
      borderBottom: "1px solid rgba(0,0,0,0.08)",
      boxShadow: "0 4px 24px rgba(0,0,0,0.08), inset 0 -1px 0 rgba(0,0,0,0.04)",
    }}>

      {/* Left: Logo */}
      <div className="flex items-center gap-3 flex-shrink-0">
        <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-[#007AFF] to-[#00C6FF] flex items-center justify-center shadow-[0_0_16px_rgba(0,198,255,0.4)]">
          <FileText className="w-4 h-4 text-white" />
        </div>
        <span className="text-base font-bold text-gray-900 tracking-tight">Lexra</span>
      </div>

      {/* Center: Nav + Search */}
      <div className="flex items-center gap-1 mx-8 flex-1 justify-center">
        {/* Nav pill */}
        <nav className="flex items-center gap-1 px-2 py-1.5 rounded-2xl mr-4" style={{
          background: "rgba(0,0,0,0.04)",
          border: "1px solid rgba(0,0,0,0.08)",
        }}>
          {navItems.map((item) => {
            const Icon = item.icon
            const isActive = pathname === item.href
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-xl text-sm font-medium transition-all duration-200 ${
                  isActive
                    ? "bg-white text-gray-900 shadow-[0_2px_8px_rgba(0,0,0,0.12)]"
                    : "text-gray-500 hover:text-gray-900 hover:bg-white/60"
                }`}
              >
                <Icon className="w-3.5 h-3.5 flex-shrink-0" />
                <span>{item.label}</span>
              </Link>
            )
          })}
        </nav>

        {/* Search */}
        <div className="relative group hidden lg:block w-48 xl:w-64">
          <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 transition-colors group-focus-within:text-blue-500" />
          <input
            type="text"
            placeholder="Search contracts..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={handleSearch}
            className="pl-9 pr-4 py-1.5 w-full text-sm rounded-xl transition-all duration-200 text-gray-900 placeholder-gray-400 outline-none"
            style={{
              background: "rgba(0,0,0,0.05)",
              border: "1px solid rgba(0,0,0,0.1)",
            }}
            onFocus={(e) => { e.currentTarget.style.border = "1px solid rgba(59,130,246,0.5)"; e.currentTarget.style.boxShadow = "0 0 0 3px rgba(59,130,246,0.1)" }}
            onBlur={(e) => { e.currentTarget.style.border = "1px solid rgba(0,0,0,0.1)"; e.currentTarget.style.boxShadow = "none" }}
          />
        </div>
      </div>

      {/* Right: Actions */}
      <div className="flex items-center gap-1.5 flex-shrink-0">
        {/* Status */}
        <div className="hidden lg:flex items-center gap-1.5 px-2.5 py-1.5 rounded-full mr-1" style={{
          background: "rgba(16,185,129,0.08)",
          border: "1px solid rgba(16,185,129,0.2)",
        }}>
          <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
          <span className="text-xs font-medium text-emerald-600">Online</span>
        </div>

        {/* Notifications */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button className="p-2 rounded-xl hover:bg-black/05 transition-all duration-200 group" title="Notifications">
              <Bell className="w-4 h-4 text-gray-500 group-hover:text-gray-900 group-hover:rotate-12 transition-all" />
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="rounded-xl w-64 p-4" style={{
            background: "rgba(255,255,255,0.95)",
            backdropFilter: "blur(20px)",
            border: "1px solid rgba(0,0,0,0.08)",
            boxShadow: "0 8px 32px rgba(0,0,0,0.12)",
          }}>
            <p className="text-sm font-semibold text-gray-900 mb-1">Notifications</p>
            <p className="text-xs text-gray-400">No notifications yet.</p>
          </DropdownMenuContent>
        </DropdownMenu>

        {/* Theme */}
        <button onClick={toggleTheme} className="p-2 rounded-xl hover:bg-black/05 transition-all duration-200 group" title={isDark ? "Light Mode" : "Dark Mode"}>
          {isDark
            ? <Sun className="w-4 h-4 text-gray-500 group-hover:text-gray-900 group-hover:rotate-12 transition-all" />
            : <Moon className="w-4 h-4 text-gray-500 group-hover:text-gray-900 group-hover:-rotate-12 transition-all" />
          }
        </button>

        {/* User avatar */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button className="flex items-center gap-2 pl-1 pr-2 py-1 rounded-xl hover:bg-black/05 transition-all duration-200 group ml-1">
              <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-[#007AFF] to-[#00C6FF] flex items-center justify-center text-xs font-bold text-white shadow-sm">
                {initials}
              </div>
              <ChevronDown className="w-3 h-3 text-gray-400 group-hover:text-gray-600 transition-colors" />
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="rounded-xl w-48 p-2" style={{
            background: "rgba(255,255,255,0.95)",
            backdropFilter: "blur(20px)",
            border: "1px solid rgba(0,0,0,0.08)",
            boxShadow: "0 8px 32px rgba(0,0,0,0.12)",
          }}>
            <div className="px-3 py-2 border-b border-gray-100 mb-1">
              <p className="text-sm font-semibold text-gray-900 truncate">{user?.name || "User"}</p>
              <p className="text-xs text-gray-400 truncate">{user?.email || ""}</p>
            </div>
            <button
              onClick={handleLogout}
              className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm text-gray-500 hover:text-red-500 hover:bg-red-50 transition-all duration-200"
            >
              <LogOut className="w-3.5 h-3.5" />
              Sign out
            </button>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  )
}
