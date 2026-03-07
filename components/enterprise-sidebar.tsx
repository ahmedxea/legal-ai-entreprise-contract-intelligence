"use client"

import { useState } from "react"
import Link from "next/link"
import { usePathname, useRouter } from "next/navigation"
import { useAuth } from "@/lib/auth-context"
import {
  LayoutDashboard,
  FileText,
  Settings,
  AlertTriangle,
  FileSearch,
  LogOut,
  ChevronLeft,
  ChevronRight,
} from "lucide-react"

interface SidebarItem {
  icon: React.ElementType
  label: string
  href: string
  badge?: string
}

const sidebarItems: SidebarItem[] = [
  { icon: LayoutDashboard, label: "Home", href: "/home" },
  { icon: FileText, label: "Contracts", href: "/contracts" },
  { icon: AlertTriangle, label: "Risk Analysis", href: "/risk" },
  { icon: FileSearch, label: "Clauses", href: "/clauses" },
]

export function EnterpriseSidebar() {
  const pathname = usePathname()
  const router = useRouter()
  const { user, signOut } = useAuth()
  const [isCollapsed, setIsCollapsed] = useState(false)

  const handleLogout = () => {
    signOut()
    router.push("/login")
  }

  // Derive initials from user name
  const initials = user?.name
    ? user.name.split(" ").map((n) => n[0]).join("").toUpperCase().slice(0, 2)
    : "?"

  return (
    <aside
      className={`fixed left-0 top-0 h-screen transition-all duration-300 ease-in-out z-40 border-r bg-gradient-to-b from-[#020B1B] to-[#0A1F44] ${
        isCollapsed ? "w-20" : "w-64"
      }`}
      style={{ borderColor: "rgba(0, 224, 255, 0.2)" }}
    >
      {/* Logo/Brand Area */}
      <div className="h-16 flex items-center justify-between px-4 border-b border-[#00E0FF]/20">
        {!isCollapsed && (
          <div className="flex items-center gap-3 animate-fade-in-up">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-[#007AFF] to-[#00C6FF] flex items-center justify-center shadow-[0_0_20px_rgba(0,198,255,0.5)]">
              <FileText className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="text-base font-bold text-white">
                Lexra
              </h1>
              <p className="text-[11px] text-[#CBD5E1]">
                Contract Intelligence
              </p>
            </div>
          </div>
        )}
        <button
          onClick={() => setIsCollapsed(!isCollapsed)}
          className="p-2 rounded-lg hover:bg-[#00E0FF]/10 transition-all duration-200 hover:scale-110 text-white"
        >
          {isCollapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
        </button>
      </div>

      {/* Navigation Items */}
      <nav className="flex-1 px-3 py-6 space-y-1.5">
        {sidebarItems.map((item, idx) => {
          const Icon = item.icon
          const isActive = pathname === item.href

          return (
            <Link
              key={item.href}
              href={item.href}
              className={`group flex items-center gap-3 px-3 py-3 rounded-xl transition-all duration-200 ${
                isActive
                  ? "bg-white/15 border border-white/30 text-white shadow-[0_6px_18px_rgba(0,0,0,0.28)] scale-[1.02]"
                    : "text-white/75 border border-transparent hover:bg-white/10 hover:border-white/20 hover:text-white hover:scale-[1.02]"
              } ${isCollapsed ? "justify-center" : ""}`}
              style={{ 
                animationDelay: `${idx * 50}ms`
              }}
              title={isCollapsed ? item.label : undefined}
            >
              <Icon className={`w-5 h-5 flex-shrink-0 transition-transform ${isActive ? "scale-110" : "group-hover:scale-110"}`} />
              {!isCollapsed && (
                <span className="text-sm font-semibold flex-1">{item.label}</span>
              )}
              {!isCollapsed && item.badge && (
                <span className="px-2 py-0.5 rounded-full bg-[#00E0FF] text-[#020B1B] text-[10px] font-bold shadow-[0_0_10px_rgba(0,224,255,0.5)]">
                  {item.badge}
                </span>
              )}
            </Link>
          )
        })}
      </nav>

      {/* Bottom Section */}
      <div className="border-t border-[#00E0FF]/20 p-3 space-y-1">
        <Link
          href="/settings"
          className={`group flex items-center gap-3 px-3 py-2.5 rounded-xl hover:bg-[#00E0FF]/10 transition-all duration-200 hover:scale-[1.02] text-white/80 hover:text-[#00E0FF] ${
            isCollapsed ? "justify-center" : ""
          }`}
          title={isCollapsed ? "Settings" : undefined}
        >
          <Settings className="w-5 h-5 flex-shrink-0 group-hover:rotate-90 transition-transform duration-300" />
          {!isCollapsed && <span className="text-sm font-medium">Settings</span>}
        </Link>

        <button
          onClick={handleLogout}
          className={`w-full group flex items-center gap-3 px-3 py-2.5 rounded-xl hover:bg-red-500/10 transition-all duration-200 hover:scale-[1.02] text-white/80 hover:text-red-400 ${
            isCollapsed ? "justify-center" : ""
          }`}
          title={isCollapsed ? "Logout" : undefined}
        >
          <LogOut className="w-5 h-5 flex-shrink-0 group-hover:translate-x-1 transition-transform" />
          {!isCollapsed && <span className="text-sm font-medium">Logout</span>}
        </button>

        {/* User Info */}
        {!isCollapsed && (
          <div className="mt-3 px-3 py-3 rounded-xl bg-[#00E0FF]/10 hover:bg-[#00E0FF]/15 transition-colors border border-[#00E0FF]/20">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-gradient-to-br from-[#007AFF] to-[#00C6FF] flex items-center justify-center text-sm font-bold text-white shadow-[0_0_15px_rgba(0,198,255,0.5)]">
                {initials}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-semibold truncate text-white">
                  {user?.name || "Guest"}
                </p>
                <p className="text-xs text-[#CBD5E1] truncate">
                  {user?.email || "Not signed in"}
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
    </aside>
  )
}
