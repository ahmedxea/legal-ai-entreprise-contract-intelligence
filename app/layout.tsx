import type React from "react"
import type { Metadata } from "next"
import { Lato } from "next/font/google"
import "./globals.css"
import ClientLayout from "./client-layout"

const lato = Lato({ 
  subsets: ['latin'],
  weight: ['300', '400', '700', '900'],
  display: 'swap',
  variable: '--font-lato',
})

export const metadata: Metadata = {
  title: "Lexra — Enterprise AI Contract Intelligence",
  description: "Lexra extracts key contract information, identifies risks and missing clauses, and enables secure AI-powered analysis.",
  generator: "v0.app",
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${lato.variable} font-sans antialiased`}>
        <ClientLayout>{children}</ClientLayout>
      </body>
    </html>
  )
}
