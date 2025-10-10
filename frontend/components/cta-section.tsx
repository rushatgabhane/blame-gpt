import { CTAButton } from "@/components/cta-button"

export function CTASection() {
  return (
    <section className="w-full pb-8 md:pb-14 px-5 relative flex flex-col justify-center items-center overflow-visible">
      <div className="absolute inset-0 top-[-90px]">
        <div className="w-full h-full" />
      </div>
      <div className="relative z-10 flex flex-col justify-start items-center gap-8 max-w-4xl mx-auto">
        <div className="flex flex-col justify-start items-center gap-4 text-center">
          <h2 className="text-foreground text-4xl md:text-5xl lg:text-[68px] font-semibold leading-tight md:leading-tight lg:leading-[76px] break-words max-w-[680px]">
            Flat pricing for your entire company. Not per user. All on your infra. 
          </h2>
          <p className="text-muted-foreground text-sm md:text-base font-medium leading-[18.20px] md:leading-relaxed break-words max-w-2xl">
            BlameGPT code access for transparency. Run AI code reviews, detect vulnerabilities, debug production issues. Reduce bottleneck on your senior engineers.
          </p>
        </div>
        <div className="flex flex-col sm:flex-row gap-3 sm:gap-4">
          <CTAButton href="https://calendly.com/rushatgabhane/blamegpt-overview-with-rushat">
            Book a demo
          </CTAButton>
          <CTAButton href="/learn-more" className="bg-transparent border border-white/20 text-white hover:bg-white/10">
            Learn more
          </CTAButton>
        </div>
      </div>
    </section>
  )
}
