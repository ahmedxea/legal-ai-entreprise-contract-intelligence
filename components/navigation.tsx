"use client"

import Link from "next/link"
import { usePathname, useRouter } from "next/navigation"
import {
  FileText,
  Home,
  Upload,
  Shield,
  FileCode,
  MessageSquare,
  Moon,
  Sun,
  FolderOpen,
  LogOut,
  User,
} from "lucide-react"
import { cn } from "@/lib/utils"
import { useEffect, useState } from "react"
import { useAuth } from "@/lib/auth-context"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"

const navigation = [
  { name: "Home", href: "/", icon: Home },
  { name: "Upload", href: "/upload", icon: Upload },
  { name: "Contracts", href: "/contracts", icon: FolderOpen },
  { name: "Dashboard", href: "/dashboard", icon: FileText },
  { name: "Risk Analysis", href: "/risk", icon: Shield },
  { name: "Clause Generator", href: "/clauses", icon: FileCode },
  { name: "Ask AI", href: "/chat", icon: MessageSquare },
]

export function Navigation() {
  const pathname = usePathname()
  const router = useRouter()
  const { user, signOut } = useAuth()
  const [isDark, setIsDark] = useState(false)

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

  const handleSignOut = () => {
    signOut()
    router.push("/")
  }

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 glass-blur border-b border-border/50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center gap-8">
            <Link href="/" className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-xl gradient-blue flex items-center justify-center shadow-lg">
                <FileText className="w-5 h-5 text-white" />
              </div>
              <span className="font-semibold text-lg gradient-text">ContractAI</span>
            </Link>

            <div className="hidden md:flex items-center gap-1">
              {navigation.map((item) => {
                const isActive = pathname === item.href
                return (
                  <Link
                    key={item.name}
                    href={item.href}
                    className={cn(
                      "flex items-center gap-2 px-3 py-2 rounded-xl text-sm font-medium transition-all duration-300",
                      isActive
                        ? "gradient-blue text-white shadow-lg"
                        : "text-muted-foreground hover:text-foreground hover:bg-secondary/50",
                    )}
                  >
                    <item.icon className="w-4 h-4" />
                    {item.name}
                  </Link>
                )
              })}
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={toggleTheme}
              className="p-2 rounded-xl hover:bg-secondary/50 transition-all duration-300"
              aria-label="Toggle theme"
            >
              {isDark ? <Sun className="w-5 h-5 text-accent" /> : <Moon className="w-5 h-5 text-primary" />}
            </button>

            {user ? (
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" className="flex items-center gap-2 rounded-xl">
                    <div className="w-8 h-8 rounded-full gradient-blue flex items-center justify-center">
                      <User className="w-4 h-4 text-white" />
                    </div>
                    <span className="hidden md:inline text-sm font-medium">{user.name}</span>
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-56">
                  <DropdownMenuLabel>
                    <div className="flex flex-col">
                      <span className="font-medium">{user.name}</span>
                      <span className="text-xs text-muted-foreground">{user.email}</span>
                    </div>
                  </DropdownMenuLabel>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem onClick={handleSignOut} className="text-destructive cursor-pointer">
                    <LogOut className="w-4 h-4 mr-2" />
                    Sign Out
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            ) : (
              <>
                <button
                  onClick={() => router.push("/login")}
                  className="px-4 py-2 text-sm font-medium text-foreground hover:bg-secondary/50 rounded-xl transition-all duration-300"
                >
                  Sign In
                </button>
                <button
                  onClick={() => router.push("/login")}
                  className="px-4 py-2 text-sm font-medium btn-gradient text-white rounded-xl shadow-lg"
                >
                  Get Started
                </button>
              </>
            )}
          </div>
        </div>
      </div>
    </nav>
  )
}
