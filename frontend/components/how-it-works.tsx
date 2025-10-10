import React from "react"

export function HowItWorks() {
  const steps = [
    "Create a PR and comment @BlameGPT review",
    "Get instant PR feedback with issues that you might have missed",
    "Push more commits → re-review by commenting - @BlameGPT review",
    "Clean PR ready for an engineer's final review",
  ]
  return (
    <section className="w-full px-5 flex flex-col justify-center items-center" id="how-it-works">
      <div className="self-stretch py-8 md:py-14 flex flex-col justify-center items-center gap-2">
        <div className="flex flex-col justify-start items-center gap-4">
          <h2 className="text-center text-foreground text-4xl md:text-5xl font-semibold leading-tight">How it works</h2>
          <p className="text-center text-muted-foreground text-base md:text-lg font-medium leading-relaxed max-w-[800px]">
            50–70% faster merges, fewer bugs, and consistent quality reducing review bottlenecks.
          </p>
        </div>
        <ol className="w-full max-w-[1000px] grid grid-cols-1 md:grid-cols-4 gap-4 mt-6">
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

export default HowItWorks 