import React from "react"

export function InstallationSection() {
  const steps = [
    "Create GitHub App (guided)—5 minutes",
    "Deploy server: clone repo and docker compose up",
    "Configure LLM API keys (OpenAI, Claude, Azure OpenAI or AWS Bedrock)",
    "Select repositories to monitor",
  ]
  return (
    <section className="w-full px-5 flex flex-col justify-center items-center">
      <div className="self-stretch py-8 md:py-14 flex flex-col justify-center items-center gap-2 z-10">
        <div className="flex flex-col justify-start items-center gap-4">
          <h2 className="text-center text-foreground text-4xl md:text-5xl font-semibold leading-tight">
            Installation in 15 minutes
          </h2>
          <p className="text-center text-muted-foreground text-base md:text-lg font-medium leading-relaxed max-w-[800px]">
            Self-hosted with minimal infrastructure.
          </p>
        </div>
        <ol className="w-full max-w-[900px] grid grid-cols-1 md:grid-cols-2 gap-4 mt-6">
          {steps.map((s, i) => (
            <li key={s} className="p-5 rounded-xl border border-border bg-card/30">
              <div className="text-muted-foreground text-sm mb-1">Step {i + 1}</div>
              <div className="text-foreground font-medium">{s}</div>
            </li>
          ))}
        </ol>
      </div>
    </section>
  )
}

export default InstallationSection 