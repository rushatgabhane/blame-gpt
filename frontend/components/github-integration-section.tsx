import React from "react"

export function GitHubIntegrationSection() {
  const bullets = [
    "Enterprise grade GitHub App",
    "Repository specific permissions",
  ]
  return (
    <section className="w-full px-5 flex flex-col justify-center items-center">
      <div className="self-stretch py-8 md:py-14 flex flex-col justify-center items-center gap-2 z-10">
        <div className="flex flex-col justify-start items-center gap-4">
          <h2 className="text-center text-foreground text-4xl md:text-5xl font-semibold leading-tight">
            GitHub integration
          </h2>
          <p className="text-center text-muted-foreground text-base md:text-lg font-medium leading-relaxed max-w-[800px]">
            Secure, scoped permissions tailored to each repository and organization.
          </p>
        </div>
        <div className="w-full max-w-[700px] grid grid-cols-1 gap-4 mt-6">
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

export default GitHubIntegrationSection 