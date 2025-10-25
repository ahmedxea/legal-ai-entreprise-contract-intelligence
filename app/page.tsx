"use client"

import { Button } from "@/components/ui/button"
import { useRouter } from "next/navigation"
import { useEffect, useState } from "react"
import { Moon, Sun } from "lucide-react"
import { motion } from "framer-motion"

export default function LandingPage() {
  const router = useRouter()
  const [isDark, setIsDark] = useState(false)
  const [scrolled, setScrolled] = useState(false)

  const navItems = ["Home", "Services", "About Us", "Who Benefits", "Contact Us"]

  useEffect(() => {
    const theme = localStorage.getItem("theme")
    if (theme === "dark" || (!theme && window.matchMedia("(prefers-color-scheme: dark)").matches)) {
      setIsDark(true)
      document.documentElement.classList.add("dark")
    }

    const handleScroll = () => {
      setScrolled(window.scrollY > 20)
    }
    window.addEventListener("scroll", handleScroll)
    return () => window.removeEventListener("scroll", handleScroll)
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
    <div className="min-h-screen bg-gradient-to-b from-[#FFFFFF] to-[#F9FAFB] dark:from-[#020B1B] dark:to-[#0A1F44] transition-colors duration-500">
      {/* Header Navigation */}
      <nav
        className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
          scrolled ? "bg-white/80 dark:bg-[#0A1F44]/80 backdrop-blur-xl shadow-lg" : "bg-transparent backdrop-blur-sm"
        }`}
      >
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Logo */}
            <span className="text-2xl font-semibold text-[#111827] dark:text-white">quill.</span>

            {/* Center Navigation Links */}
            <div className="hidden md:flex items-center gap-8">
              {navItems.map((item) => (
                <button
                  key={item}
                  className="text-sm font-medium text-[#6B7280] hover:text-[#111827] dark:text-[#9CA3AF] dark:hover:text-white transition-colors"
                >
                  {item}
                </button>
              ))}
            </div>

            {/* Right Side - Theme Toggle & CTA */}
            <div className="flex items-center gap-3">
              <button
                onClick={toggleTheme}
                className="p-2 rounded-xl hover:bg-[#F3F4F6] dark:hover:bg-[#1E293B] transition-all duration-300"
                aria-label="Toggle theme"
              >
                {isDark ? <Sun className="w-5 h-5 text-[#00E0FF]" /> : <Moon className="w-5 h-5 text-[#007AFF]" />}
              </button>
              <Button
                onClick={() => router.push("/login")}
                className="rounded-xl bg-gradient-to-r from-[#007AFF] to-[#00C6FF] text-white px-5 py-2 hover:opacity-90 shadow-[0_0_10px_rgba(0,198,255,0.3)] transition-all"
              >
                Get Started →
              </Button>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <main className="flex flex-col items-center justify-center min-h-screen px-4 pt-16">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="text-center max-w-5xl mx-auto"
        >
          {/* Badge */}
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.5, delay: 0.2 }}
            className="mb-6"
          >
            <span className="inline-block bg-[#F3F4F6] dark:bg-[#1E293B] text-[#111827] dark:text-white px-4 py-1 rounded-full text-sm font-medium shadow-sm">
              Quill is now public!
            </span>
          </motion.div>

          {/* Main Heading */}
          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.3 }}
            className="text-5xl sm:text-6xl lg:text-7xl font-bold text-center text-[#111827] dark:text-white mb-6 text-balance"
          >
            Chat with your{" "}
            <span className="bg-gradient-to-r from-[#007AFF] to-[#00C6FF] bg-clip-text text-transparent">
              documents
            </span>{" "}
            in seconds.
          </motion.h1>

          {/* Subtitle */}
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.4 }}
            className="text-[#6B7280] dark:text-[#9CA3AF] text-center mt-4 text-lg sm:text-xl max-w-2xl mx-auto text-balance"
          >
            Quill allows you to have conversations with any PDF document. Simply upload your file and start asking
            questions right away.
          </motion.p>

          {/* CTA Button */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.5 }}
            className="mt-8"
          >
            <Button
              onClick={() => router.push("/login")}
              className="rounded-xl bg-gradient-to-r from-[#007AFF] to-[#00C6FF] text-white px-8 py-3 text-lg font-medium hover:opacity-90 hover:scale-105 transition-all shadow-[0_0_20px_rgba(0,198,255,0.4)] dark:shadow-[0_0_30px_rgba(0,224,255,0.5)]"
            >
              Get Started →
            </Button>
          </motion.div>

          {/* Navigation Buttons */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.6 }}
            className="flex flex-wrap justify-center gap-3 mt-12"
          >
            {navItems.map((item, index) => (
              <motion.div
                key={item}
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.4, delay: 0.7 + index * 0.1 }}
              >
                <Button
                  variant="outline"
                  className="rounded-2xl border border-[#E5E7EB] dark:border-[#1E293B] bg-white/50 dark:bg-[#0A1F44]/50 backdrop-blur-md text-[#111827] dark:text-white hover:bg-[#F3F4F6] dark:hover:bg-[#1E293B] hover:scale-105 transition-all shadow-sm"
                >
                  {item}
                </Button>
              </motion.div>
            ))}
          </motion.div>
        </motion.div>
      </main>

      {/* Footer */}
      <footer className="text-center text-[#9CA3AF] dark:text-[#6B7280] mt-16 mb-8 text-sm">
        © 2025 Quill. All rights reserved.
      </footer>
    </div>
  )
}
