"use client"

import Image from "next/image" // Import the Image component
import { useEffect, useRef } from "react"

export function DashboardPreview() {
  const videoRef = useRef<HTMLVideoElement>(null)

  useEffect(() => {
    if (videoRef.current) {
      videoRef.current.play().catch(() => {
        // Ignore play promise rejections (happens when browser blocks autoplay)
      })
    }
  }, [])

  return (
    <div className="w-full max-w-[860px] lg:max-w-[920px] mx-auto">
      <div className="rounded-2xl p-2 border border-border/60 bg-background/20">
        <video
          ref={videoRef}
          src="/blamegpt.mp4"
          className="w-full h-auto rounded-xl"
          autoPlay
          muted
          loop
          playsInline
          preload="auto"
          poster="/images/change-summary.png"
        />
      </div>
    </div>
  )
}
