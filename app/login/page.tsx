"use client"

import type React from "react"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { useAuth } from "@/lib/auth-context"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { motion } from "framer-motion"
import { ArrowLeft } from "lucide-react"

export default function LoginPage() {
  const router = useRouter()
  const { signIn, signUp } = useAuth()
  const [isSignUp, setIsSignUp] = useState(false)
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [name, setName] = useState("")
  const [error, setError] = useState("")
  const [isLoading, setIsLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError("")
    setIsLoading(true)

    try {
      let success = false
      if (isSignUp) {
        if (!name) {
          setError("Please enter your name")
          setIsLoading(false)
          return
        }
        success = await signUp(email, password, name)
      } else {
        success = await signIn(email, password)
      }

      if (success) {
        router.push("/upload")
      } else {
        setError(isSignUp ? "Sign up failed. Please try again." : "Invalid email or password")
      }
    } catch (err) {
      setError("An error occurred. Please try again.")
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-[#020B1B] to-[#0A1F44] flex items-center justify-center px-4">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="w-full max-w-md"
      >
        {/* Back Button */}
        <button
          onClick={() => router.push("/")}
          className="flex items-center gap-2 text-[#00E0FF] hover:text-[#00C6FF] transition-colors mb-8"
        >
          <ArrowLeft className="w-4 h-4" />
          <span className="text-sm">Back to home</span>
        </button>

        {/* Login Card */}
        <div className="bg-[#0A1F44]/70 backdrop-blur-xl border border-[#00E0FF]/20 rounded-2xl p-8 shadow-[0_0_30px_rgba(0,224,255,0.1)]">
          {/* Logo */}
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold text-white mb-2">{isSignUp ? "Create Account" : "Welcome Back"}</h1>
            <p className="text-[#9CA3AF]">
              {isSignUp ? "Sign up to get started with Quill" : "Sign in to continue to Quill"}
            </p>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            {isSignUp && (
              <div className="space-y-2">
                <Label htmlFor="name" className="text-white">
                  Name
                </Label>
                <Input
                  id="name"
                  type="text"
                  placeholder="John Doe"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="bg-[#020B1B]/80 border-[#00E0FF]/20 text-white placeholder:text-[#6B7280] focus:border-[#00C6FF] rounded-xl"
                  required={isSignUp}
                />
              </div>
            )}

            <div className="space-y-2">
              <Label htmlFor="email" className="text-white">
                Email
              </Label>
              <Input
                id="email"
                type="email"
                placeholder="you@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="bg-[#020B1B]/80 border-[#00E0FF]/20 text-white placeholder:text-[#6B7280] focus:border-[#00C6FF] rounded-xl"
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="password" className="text-white">
                Password
              </Label>
              <Input
                id="password"
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="bg-[#020B1B]/80 border-[#00E0FF]/20 text-white placeholder:text-[#6B7280] focus:border-[#00C6FF] rounded-xl"
                required
                minLength={6}
              />
              {!isSignUp && (
                <div className="text-right">
                  <button type="button" className="text-sm text-[#00E0FF] hover:text-[#00C6FF] transition-colors">
                    Forgot password?
                  </button>
                </div>
              )}
            </div>

            {error && (
              <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-3 text-red-400 text-sm">{error}</div>
            )}

            <Button
              type="submit"
              disabled={isLoading}
              className="w-full rounded-xl bg-gradient-to-r from-[#007AFF] to-[#00C6FF] text-white py-3 hover:opacity-90 transition-all shadow-[0_0_20px_rgba(0,198,255,0.3)] disabled:opacity-50"
            >
              {isLoading ? "Loading..." : isSignUp ? "Sign Up" : "Sign In"}
            </Button>
          </form>

          {/* Toggle Sign Up/Sign In */}
          <div className="mt-6 text-center">
            <p className="text-[#9CA3AF] text-sm">
              {isSignUp ? "Already have an account?" : "Don't have an account?"}{" "}
              <button
                type="button"
                onClick={() => {
                  setIsSignUp(!isSignUp)
                  setError("")
                }}
                className="text-[#00E0FF] hover:text-[#00C6FF] transition-colors font-medium"
              >
                {isSignUp ? "Sign In" : "Sign Up"}
              </button>
            </p>
          </div>
        </div>
      </motion.div>
    </div>
  )
}
