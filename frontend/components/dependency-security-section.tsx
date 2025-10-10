import React from "react"

export function DependencySecuritySection() {
  const bullets = [
    "Cross-checks GitHub Advisories, OSV.dev, and NVD",
    "Alerts on vulnerable dependencies added in PRs",
    "Dashboard visibility for existing vulnerabilities",
    "Optional GitHub Issues or Slack alerts",
    "CWE mapping for compliance",
  ]
  return (
    <section className="w-full px-5 flex flex-col justify-center items-center">
      <div className="self-stretch py-8 md:py-14 flex flex-col justify-center items-center gap-2 z-10">
        <div className="flex flex-col justify-start items-center gap-4">
          <h2 className="text-center text-foreground text-4xl md:text-5xl font-semibold leading-tight">
            Dependency vulnerability scanning
          </h2>
          <p className="text-center text-muted-foreground text-base md:text-lg font-medium leading-relaxed max-w-[800px]">
            Continuous checks across multiple databases with actionable alerts and compliance mapping.
          </p>
        </div>
        <div className="w-full max-w-[900px] grid grid-cols-1 md:grid-cols-2 gap-4 mt-6">
          {bullets.map((b) => (
            <div key={b} className="p-5 rounded-xl border border-border bg-gradient-to-b from-white/5 to-transparent">
              <div className="text-foreground font-medium">{b}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

export default DependencySecuritySection 