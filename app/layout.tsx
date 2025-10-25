import type React from "react"
import type { Metadata } from "next"
import "./globals.css"
import ClientLayout from "./client-layout"

export const metadata: Metadata = {
  title: "Contract Lifecycle Management | AI-Powered",
  description: "AI-driven contract analysis, risk detection, and lifecycle management",
  generator: "v0.app",
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="font-sans antialiased">
        <ClientLayout>{children}</ClientLayout>
      </body>
    </html>
  )
}
