import { HeroSection } from "@/components/hero-section"
import { DashboardPreview } from "@/components/dashboard-preview"
// import { SocialProof } from "@/components/social-proof"
import { BentoSection } from "@/components/bento-section"
// import { LargeTestimonial } from "@/components/large-testimonial"
import { SecuritySection } from "@/components/security-section"
import { PricingSection } from "@/components/pricing-section"
// import { TestimonialGridSection } from "@/components/testimonial-grid-section"
import { FAQSection } from "@/components/faq-section"
import { CTASection } from "@/components/cta-section"
import { FooterSection } from "@/components/footer-section"
import { AnimatedSection } from "@/components/animated-section"

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-background relative overflow-hidden pb-0">
      <div className="relative z-10">
        <main className="max-w-[1320px] mx-auto relative">
          <HeroSection />
        </main>
        {/**
        <AnimatedSection className="relative z-10 max-w-[1320px] mx-auto px-5 mt-10 md:mt-16" delay={0.1}>
          <SocialProof />
        </AnimatedSection>
        **/}
        <AnimatedSection id="features-section" className="relative z-10 max-w-[1320px] mx-auto mt-6" delay={0.2}>
          <BentoSection />
        </AnimatedSection>
        <AnimatedSection id="security-section" className="relative z-10 mt-6 md:mt-10" delay={0.2}>
          <SecuritySection />
        </AnimatedSection>
        {/** Temporarily hidden testimonials **/}
        {/**
        <AnimatedSection className="relative z-10 max-w-[1320px] mx-auto mt-6 md:mt-10" delay={0.2}>
          <LargeTestimonial />
        </AnimatedSection>
        **/}
        {/**
        <AnimatedSection
          id="testimonials-section"
          className="relative z-10 max-w-[1320px] mx-auto mt-6 md:mt-10"
          delay={0.2}
        >
          <TestimonialGridSection />
        </AnimatedSection>
        **/}
        <AnimatedSection id="faq-section" className="relative z-10 max-w-[1320px] mx-auto mt-6 md:mt-10" delay={0.2}>
          <FAQSection />
        </AnimatedSection>
        <AnimatedSection className="relative z-10 max-w-[1320px] mx-auto mt-6 md:mt-10" delay={0.2}>
          <CTASection />
        </AnimatedSection>
        <AnimatedSection className="relative z-10 max-w-[1320px] mx-auto mt-6 md:mt-10" delay={0.2}>
          <FooterSection />
        </AnimatedSection>
      </div>
    </div>
  )
}
