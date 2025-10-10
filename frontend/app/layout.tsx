import type React from "react"
import type { Metadata } from "next"
// Removed IBM Plex Mono import
import "./globals.css"
import { Header } from "@/components/header"

// Using system Helvetica font

export const metadata: Metadata = {
  title: "BlameGPT – AI code reviews and security analysis",
  description:
    "Self-hosted, enterprise-grade PR reviews with line-by-line findings, dependency risk alerts, and production tracebacks—no vendor lock-in.",
  generator: "v0.app",
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en">
      <head>
        <link rel="preload" as="video" href="/blamegpt.mp4" />
        <style>{`
html {
  font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
}
        `}</style>
      </head>
      <body className="font-sans">
        <Header />
        {children}
      </body>
    </html>
  )
}
