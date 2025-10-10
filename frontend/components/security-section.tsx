"use client"

import { CheckCircle, Shield, Server, Github, ArrowLeftRight } from "lucide-react"

export function SecuritySection() {
  return (
    <section className="w-full px-5 py-20 lg:py-32 bg-muted/30">
      <div className="max-w-[1320px] mx-auto">
        <div className="text-center mb-16">
          <h2 className="text-4xl md:text-5xl lg:text-6xl font-semibold leading-tight mb-4">
            Security-first architecture
          </h2>
          <p className="text-lg text-muted-foreground mb-8">
            Your code, your infrastructure. Choose your LLM provider,
            ephemeral data handling.
          </p>
        </div>

        <div className="grid lg:grid-cols-2 gap-12 items-center">
          <div className="space-y-6">
            <div className="flex items-start gap-4">
              <CheckCircle className="w-6 h-6 text-green-500 mt-1 flex-shrink-0" />
              <div>
                <h3 className="mb-1">
                  Minimal infra: 1GB RAM, 1 vCPU Linux server
                </h3>
              </div>
            </div>
            <div className="flex items-start gap-4">
              <CheckCircle className="w-6 h-6 text-green-500 mt-1 flex-shrink-0" />
              <div>
                <h3 className="mb-1">
                  Self-hosted with local SQLite. No database setup required
                </h3>
              </div>
            </div>
            <div className="flex items-start gap-4">
              <CheckCircle className="w-6 h-6 text-green-500 mt-1 flex-shrink-0" />
              <div>
                <h3 className="mb-1">
                  Temporary clones, encrypted APIs, no permanent code storage
                </h3>
              </div>
            </div>
            <div className="flex items-start gap-4">
              <CheckCircle className="w-6 h-6 text-green-500 mt-1 flex-shrink-0" />
              <div>
                <h3 className="mb-1">
                  Direct LLM API keys or via Azure foundary or AWS Bedrock
                </h3>
              </div>
            </div>
          </div>

          <div className="bg-muted/50 rounded-2xl p-4 md:p-8">
            <div className="flex items-center justify-center gap-2 md:gap-8">
              {/* GitHub App */}
              <div className="text-center">
                <div className="w-12 h-12 md:w-16 md:h-16 bg-background rounded-lg flex items-center justify-center mx-auto mb-2 md:mb-3 shadow-sm">
                  <Github className="w-6 h-6 md:w-8 md:h-8 text-purple-600" />
                </div>
                <p className="text-xs md:text-sm font-medium">PR on Github</p>
              </div>

              {/* Double arrow to BlameGPT */}
              <div className="flex items-center">
                <ArrowLeftRight className="w-4 h-4 md:w-8 md:h-8 text-muted-foreground" />
              </div>

              {/* BlameGPT Server */}
              <div className="text-center">
                <div className="w-12 h-12 md:w-16 md:h-16 bg-background rounded-lg flex items-center justify-center mx-auto mb-2 md:mb-3 shadow-sm">
                  <Server className="w-6 h-6 md:w-8 md:h-8 text-blue-600" />
                </div>
                <p className="text-xs md:text-sm font-medium">
                  BlameGPT server on your infra
                </p>
              </div>

              {/* Double arrow to LLM */}
              <div className="flex items-center">
                <ArrowLeftRight className="w-4 h-4 md:w-8 md:h-8 text-muted-foreground" />
              </div>

              {/* LLM Provider */}
              <div className="text-center">
                <div className="w-12 h-12 md:w-16 md:h-16 bg-background rounded-lg flex items-center justify-center mx-auto mb-2 md:mb-3 shadow-sm">
                  <Shield className="w-6 h-6 md:w-8 md:h-8 text-red-600" />
                </div>
                <p className="text-xs md:text-sm font-medium">LLM Provider</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}