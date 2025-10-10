"use client"

import { useState } from "react"
import { Check } from "lucide-react"
import { CTAButton } from "@/components/cta-button"

export function PricingSection() {
  const [isAnnual] = useState(true)

  const enterprise = {
    title: "Custom pricing for startups and enterprises",
    bullets: [
      "Self-hosted with full source access",
      "Flat pricing, not per-user",
      "AI PR reviews, dependency scanning, production debugging",
      "GitHub App integration and org-level controls",
      "Support and feature requests included",
    ],
  }

  return (
    <section className="w-full px-5 overflow-hidden flex flex-col justify-start items-center my-0 py-8 md:py-14">
      <div className="self-stretch relative flex flex-col justify-center items-center gap-2 py-0">
        <div className="flex flex-col justify-start items-center gap-4">
          <h2 className="text-center text-foreground text-4xl md:text-5xl font-semibold leading-tight md:leading-[40px]">
            Contact us to self-host today
          </h2>
          <p className="self-stretch text-center text-muted-foreground text-sm font-medium leading-tight">
            We would love to hear from you
          </p>
        </div>
      </div>
      <div className="self-stretch max-w-[900px] mt-6">
        <div className="p-6 md:p-10 rounded-2xl border border-border bg-gradient-to-b from-gray-50/5 to-gray-50/0">
          <div className="flex flex-col md:flex-row gap-10 items-center md:items-start justify-center md:justify-between">
            <div className="flex-1">
              <h3 className="text-foreground text-2xl font-semibold mb-3">{enterprise.title}</h3>
              <div className="flex flex-col gap-3">
                {enterprise.bullets.map((b) => (
                  <div key={b} className="flex items-start gap-2">
                    <Check className="w-5 h-5 text-muted-foreground" />
                    <span className="text-muted-foreground text-sm leading-tight">{b}</span>
                  </div>
                ))}
              </div>
            </div>
            <div className="w-full md:w-auto flex flex-col gap-3 justify-center">
              <CTAButton 
                href="https://calendly.com/rushatgabhane/blamegpt-overview-with-rushat" 
                className="w-full md:w-auto"
              >
                Contact us
              </CTAButton>
              <CTAButton 
                href="/learn-more" 
                className="w-full md:w-auto bg-transparent border border-white/20 text-white hover:bg-white/10"
              >
                Learn more
              </CTAButton>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
