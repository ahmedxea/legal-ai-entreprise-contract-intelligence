"use client"

import type React from "react"
import { Inter, Geist_Mono } from "next/font/google"
import { Analytics } from "@vercel/analytics/next"
import { AuthProvider } from "@/lib/auth-context"

const inter = Inter({ subsets: ["latin"] })
const _geistMono = Geist_Mono({ subsets: ["latin"] })

export default function ClientLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      <AuthProvider>
        <ThemeProvider>{children}</ThemeProvider>
      </AuthProvider>
      <Analytics />
    </>
  )
}

function ThemeProvider({ children }: { children: React.ReactNode }) {
  return <>{children}</>
}
