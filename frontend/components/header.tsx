"use client"

import type React from "react"

import { CTAButton } from "@/components/cta-button"
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from "@/components/ui/sheet"
import Link from "next/link" // Import Link for client-side navigation
import { usePathname, useRouter } from "next/navigation"

export function Header() {
  const router = useRouter()
  const pathname = usePathname()


  const handleNav = (e: React.MouseEvent<HTMLAnchorElement>, href: string, type: "route" | "anchor") => {
    if (type === "anchor") {
      if (pathname === "/") {
        e.preventDefault()
        const targetId = href.substring(1)
        const targetElement = document.getElementById(targetId)
        if (targetElement) targetElement.scrollIntoView({ behavior: "smooth" })
      } else {
        e.preventDefault()
        router.push(`/${href}`)
      }
    }
  }

  return (
    <header className="w-full sticky top-0 z-40 backdrop-blur supports-[backdrop-filter]:bg-background/70">
      <div className="max-w-7xl mx-auto flex items-center justify-between py-3 px-6">
        <div className="flex items-center gap-8">
          <div className="flex items-center gap-3">
            <Link href="/" className="text-foreground text-2xl font-semibold hover:opacity-80 transition-opacity">
              BlameGPT
            </Link>
          </div>
          <nav className="hidden md:flex items-center gap-8">
            <Link href="/pricing" className="text-muted-foreground hover:text-white transition-colors font-medium">
              Pricing
            </Link>
            <Link href="/learn-more" className="text-muted-foreground hover:text-white transition-colors font-medium">
              Learn more
            </Link>
          </nav>
        </div>
        
        <div className="flex items-center gap-4">
          <CTAButton 
            href="https://calendly.com/rushatgabhane/blamegpt-overview-with-rushat" 
            className="hidden md:flex bg-transparent border border-white/20 text-white hover:bg-white/10"
          >
            Book a demo
          </CTAButton>
        </div>
      </div>
    </header>
  )
}
