"use client"

import { Github } from "lucide-react"

export function FooterSection() {
  return (
    <footer className="w-full bg-transparent border-0">
      <div className="max-w-[1320px] mx-auto px-5 flex flex-col md:flex-row justify-between items-start md:items-center gap-8 md:gap-0 py-12 md:py-16">
        {/* Left Section: Logo, Description, Social Links */}
        <div className="flex flex-col justify-start items-start gap-6">
          <div className="flex gap-3 items-center justify-start">
            <div className="text-foreground text-2xl font-bold">BlameGPT</div>
          </div>
          <p className="text-muted-foreground text-base font-normal leading-6 max-w-sm">
            AI-powered code review and security analysis
          </p>
          <div className="flex justify-start items-start gap-4">
            <a 
              href="https://github.com/blame-gpt" 
              aria-label="GitHub" 
              className="w-5 h-5 flex items-center justify-center hover:scale-110 transition-transform" 
              target="_blank" 
              rel="noopener noreferrer"
            >
              <Github className="w-full h-full text-muted-foreground hover:text-foreground transition-colors" />
            </a>
          </div>
        </div>
        
        {/* Right Section: Links */}
        <div className="flex flex-col md:flex-row justify-start items-start md:items-center gap-4 md:gap-8">
          <a href="/careers" className="text-muted-foreground hover:text-foreground text-sm font-medium transition-colors">
            Careers
          </a>
          <a href="/privacy" className="text-muted-foreground hover:text-foreground text-sm font-medium transition-colors">
            Privacy
          </a>
          <a href="/pricing" className="text-muted-foreground hover:text-foreground text-sm font-medium transition-colors">
            Pricing
          </a>
          <a href="/learn-more" className="text-muted-foreground hover:text-foreground text-sm font-medium transition-colors">
            Learn more
          </a>
        </div>
      </div>
    </footer>
  )
}
