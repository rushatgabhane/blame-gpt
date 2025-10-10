import React from "react"

export function SecurityArchitectureSection() {
  const bullets = [
    "Minimal infra: 1GB RAM, 1 vCPU Linux server",
    "Self-hosted with local SQLite—no complex setup",
    "Temporary clones, encrypted APIs, no permanent code storage",
    "Direct LLM API keys or via Azure foundary or AWS Bedrock",
  ]
  return (
    <section className="w-full px-5 flex flex-col justify-center items-center" id="security-architecture">
      <div className="self-stretch py-8 md:py-14 flex flex-col justify-center items-center gap-2">
        <div className="flex flex-col justify-start items-center gap-4">
          <h2 className="text-center text-foreground text-4xl md:text-5xl font-semibold leading-tight">
            Security-first architecture
          </h2>
          <p className="text-center text-muted-foreground text-base md:text-lg font-medium leading-relaxed max-w-[800px]">
            Your code, your infrastructure. Choose your LLM provider, ephemeral data handling.
          </p>
        </div>
        <div className="w-full max-w-[900px] mx-auto grid grid-cols-1 md:grid-cols-2 gap-6 mt-8">
          <div className="p-6 rounded-xl border border-border bg-card/30">
            <ul className="list-disc list-inside space-y-3 text-muted-foreground text-base">
              {bullets.map((b) => (
                <li key={b}>{b}</li>
              ))}
            </ul>
          </div>
          <div className="p-6 rounded-xl border border-border bg-card/30">
            <svg viewBox="0 0 400 220" className="w-full h-[200px]" xmlns="http://www.w3.org/2000/svg">
              <rect x="10" y="10" width="120" height="60" rx="8" fill="none" stroke="currentColor" opacity="0.6" />
              <text x="70" y="45" textAnchor="middle" fontSize="12" fill="currentColor" opacity="0.8">GitHub App</text>
              <rect x="160" y="10" width="120" height="60" rx="8" fill="none" stroke="currentColor" opacity="0.6" />
              <text x="220" y="45" textAnchor="middle" fontSize="12" fill="currentColor" opacity="0.8">BlameGPT server</text>
              <rect x="310" y="10" width="80" height="60" rx="8" fill="none" stroke="currentColor" opacity="0.6" />
              <text x="350" y="45" textAnchor="middle" fontSize="12" fill="currentColor" opacity="0.8">SQLite</text>
              <rect x="160" y="130" width="90" height="60" rx="8" fill="none" stroke="currentColor" opacity="0.6" />
              <text x="205" y="165" textAnchor="middle" fontSize="12" fill="currentColor" opacity="0.8">Azure OpenAI</text>
              <rect x="260" y="130" width="100" height="60" rx="8" fill="none" stroke="currentColor" opacity="0.6" />
              <text x="310" y="165" textAnchor="middle" fontSize="12" fill="currentColor" opacity="0.8">AWS Bedrock</text>
              <path d="M130 40 L160 40" stroke="currentColor" opacity="0.5" />
              <path d="M280 40 L310 40" stroke="currentColor" opacity="0.5" />
              <path d="M220 70 L205 130" stroke="currentColor" opacity="0.5" />
              <path d="M220 70 L310 130" stroke="currentColor" opacity="0.5" />
            </svg>
          </div>
        </div>
      </div>
    </section>
  )
}

export default SecurityArchitectureSection 