import React from "react"

export function ProblemSection() {
  return (
    <section className="w-full px-5 flex flex-col justify-center items-center overflow-visible" id="problem">
      <div className="self-stretch py-8 md:py-14 flex flex-col justify-center items-center gap-2 z-10">
        <div className="flex flex-col justify-start items-center gap-4">
          <h2 className="w-full max-w-[655px] text-center text-foreground text-4xl md:text-5xl font-semibold leading-tight">
            The problem
          </h2>
          <p className="w-full max-w-[700px] text-center text-muted-foreground text-base md:text-lg font-medium leading-relaxed">
            AI increases developer productivity, but PR reviews fall behind and are a bottleneck. Senior engineers drown in 20+ file PRs, that may have subtle bugs and vulnerabilities that may slip through.
          </p>
        </div>
        <div className="w-full max-w-[900px] grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
          {["AI-generated code hides logic and security bugs","Reviews bottleneck on limited senior bandwidth","Manual dependency verification is error prone"].map((item) => (
            <div key={item} className="p-5 rounded-xl border border-border bg-gradient-to-b from-white/5 to-transparent">
              <div className="text-foreground font-medium">{item}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

export default ProblemSection 