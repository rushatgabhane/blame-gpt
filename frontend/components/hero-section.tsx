"use client"

import React, { useEffect, useState } from "react"
import { CTAButton } from "@/components/cta-button"
import { DashboardPreview } from "@/components/dashboard-preview"

export function HeroSection() {
  const [blobPosition, setBlobPosition] = useState({ x: 800, y: 100 }) // Default fallback position
  const [isClient, setIsClient] = useState(false)

  useEffect(() => {
    setIsClient(true)
    // Set initial position after component mounts
    const initialX = window.innerWidth * 0.55
    setBlobPosition({ x: initialX, y: 100 })
  }, [])

  return (
    <section
      className="flex flex-col items-center text-center min-h-[70vh] md:min-h-screen relative overflow-hidden pt-20 md:pt-32"
    >
      {/* Single gradient blob on right */}
      <div className="absolute inset-0 z-0">
        <div 
          className={`absolute w-[600px] h-[600px] rounded-full opacity-70 blur-3xl animate-pulse transition-all duration-300 ${!isClient ? 'opacity-0' : ''}`}
          style={{
            background: 'linear-gradient(225deg, #06b6d4 0%, #8b5cf6 50%, #f59e0b 100%)',
            filter: 'blur(100px) contrast(1.5) saturate(1.2)',
            animation: isClient ? 'breathe 4s ease-in-out infinite, drift 20s ease-in-out infinite' : 'none',
            left: `${blobPosition.x}px`,
            top: `${blobPosition.y}px`
          }}
        />
        {/* Gaussian noise overlay - follows the blob */}
        <div 
          className={`absolute w-[600px] h-[600px] rounded-full opacity-20 mix-blend-soft-light transition-all duration-300 ${!isClient ? 'opacity-0' : ''}`}
          style={{
            backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 400 400' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.6' numOctaves='1' result='noise' seed='1'/%3E%3CfeColorMatrix in='noise' type='saturate' values='0'/%3E%3CfeComponentTransfer%3E%3CfeFuncA type='discrete' tableValues='0 .5 0 .7 0 .4 0 .6'/%3E%3C/feComponentTransfer%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)' opacity='0.6'/%3E%3C/svg%3E")`,
            backgroundSize: '300px 300px',
            left: `${blobPosition.x}px`,
            top: `${blobPosition.y}px`,
            maskImage: 'radial-gradient(circle at 50% 50%, white 40%, transparent 70%)'
          }}
        />
      </div>

      <div className="relative z-10 max-w-6xl mx-auto px-4 md:px-6">
        <h1 className="text-foreground text-4xl md:text-5xl lg:text-7xl font-semibold leading-tight text-balance mb-4 md:mb-6">
          Self hosted AI code reviewer.
        </h1>
        <p className="text-muted-foreground text-base md:text-lg lg:text-xl font-medium leading-relaxed max-w-xl md:max-w-2xl mx-auto text-pretty mb-6 md:mb-8">
           Save time on code reviews, reduce bugs, and ship the feature. Flat pricing for your entire org (not per user).
        </p>
          <div className="flex flex-col sm:flex-row gap-3 sm:gap-4 justify-center mb-8 md:mb-16" id="book-demo">
            <CTAButton href="https://calendly.com/rushatgabhane/blamegpt-overview-with-rushat">
              Book a demo
            </CTAButton>
            <CTAButton href="/learn-more" className="bg-transparent border border-white/20 text-white hover:bg-white/10">
              Learn more
            </CTAButton>
          </div>
          
          {/* Video positioned relative to button */}
          <div className="flex justify-center">
            <div className="max-w-[1320px] w-full px-4">
              <div className="relative z-20">
                <DashboardPreview />
              </div>
            </div>
          </div>
        </div>
    </section>
  )
}
