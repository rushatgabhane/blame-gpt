'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { FooterSection } from '@/components/footer-section';
import { CheckCircle, Server, Cloud } from 'lucide-react';

export default function PricingPage() {
  return (
    <div className="min-h-screen bg-background relative overflow-hidden">
      <section className="pt-10 pb-20 lg:pb-32 relative">
        {/* Animated background orb */}
        <div
          className="w-[500px] h-[700px] absolute top-[100px] right-[-200px] origin-center rounded-full opacity-40 blur-3xl z-0"
          style={{
            background:
              'linear-gradient(225deg, #06b6d4 0%, #8b5cf6 50%, #f59e0b 100%)',
            filter: 'blur(100px) contrast(1.5) saturate(1.2)',
            animation:
              'breathe 6s ease-in-out infinite, drift 25s ease-in-out infinite',
            transform: 'rotate(-30deg)',
          }}
        />

        <div className="max-w-[1320px] mx-auto px-4 md:px-6 relative z-10">
          <div className="max-w-4xl mx-auto text-center mb-10">
            <h1 className="text-4xl md:text-5xl lg:text-7xl font-semibold leading-tight mb-8">
              Pricing
            </h1>
            <p className="text-lg text-muted-foreground">
              Choose the deployment option that works best for your team.
            </p>
            <p className="text-lg font-bold text-white mt-2">
              30 day free trial
            </p>
          </div>

          <div className="grid md:grid-cols-2 gap-8 max-w-4xl mx-auto">
            {/* Cloud Version */}
            <Card className="relative p-6 flex flex-col border-0">
              <CardHeader className="text-center pb-6">
                <div className="w-16 h-16 bg-purple-500/10 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Cloud className="w-8 h-8 text-purple-500" />
                </div>
                <CardTitle className="text-2xl mb-2">Cloud Version</CardTitle>
                <p className="text-muted-foreground">Managed service</p>
              </CardHeader>
              <CardContent className="flex flex-col flex-1">
                <div className="space-y-4 mb-8 flex-1">
                  <div className="flex items-start gap-3">
                    <CheckCircle className="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" />
                    <span className="text-sm font-semibold">
                      Flat pricing for your entire company. Not per user.
                    </span>
                  </div>
                  <div className="flex items-start gap-3">
                    <CheckCircle className="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" />
                    <span className="text-sm">
                      No infrastructure management
                    </span>
                  </div>
                  <div className="flex items-start gap-3">
                    <CheckCircle className="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" />
                    <span className="text-sm">
                      Unlimited repositories & users
                    </span>
                  </div>
                  <div className="flex items-start gap-3">
                    <CheckCircle className="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" />
                    <span className="text-sm">Code security analysis</span>
                  </div>
                  <div className="flex items-start gap-3">
                    <CheckCircle className="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" />
                    <span className="text-sm">Advanced analytics</span>
                  </div>
                </div>

                <div className="text-center">
                  <a
                    href="https://tally.so/r/nP7L6d"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="w-full bg-transparent border border-white/20 text-white hover:bg-white/10 py-3 px-6 rounded-full font-medium transition-all duration-300 inline-block mt-auto shadow-lg"
                  >
                    Join the waitlist
                  </a>
                </div>
              </CardContent>
            </Card>

            {/* Self-Hosted */}
            <Card className="relative p-6 flex flex-col border-0">
              <CardHeader className="text-center pb-6">
                <div className="w-16 h-16 bg-blue-500/10 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Server className="w-8 h-8 text-blue-500" />
                </div>
                <CardTitle className="text-2xl mb-2">Self-Hosted</CardTitle>
                <p className="text-muted-foreground">
                  Deploy on your infrastructure
                </p>
              </CardHeader>
              <CardContent className="flex flex-col flex-1">
                <div className="space-y-4 mb-8 flex-1">
                  <div className="flex items-start gap-3">
                    <CheckCircle className="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" />
                    <span className="text-sm font-semibold">
                      Flat pricing for your entire company. Not per user.
                    </span>
                  </div>
                  <div className="flex items-start gap-3">
                    <CheckCircle className="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" />
                    <span className="text-sm">
                      Unlimited repositories & users
                    </span>
                  </div>
                  <div className="flex items-start gap-3">
                    <CheckCircle className="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" />
                    <span className="text-sm">Air-gapped</span>
                  </div>
                  <div className="flex items-start gap-3">
                    <CheckCircle className="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" />
                    <span className="text-sm">Use your own LLM provider</span>
                  </div>
                  <div className="flex items-start gap-3">
                    <CheckCircle className="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" />
                    <span className="text-sm">Code security analysis</span>
                  </div>
                </div>

                <div className="text-center">
                  <a
                    href="https://calendly.com/rushatgabhane/blamegpt-overview-with-rushat"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="w-full bg-white text-black hover:bg-gray-100 py-3 px-6 rounded-full font-medium transition-colors inline-block mt-auto shadow-lg"
                  >
                    Book a demo
                  </a>
                </div>
              </CardContent>
            </Card>
          </div>

          <div className="text-center mt-16">
            <p className="text-muted-foreground mb-4">Have any questions?</p>
            <a
              href="mailto:hello@blamegpt.io"
              className="text-white hover:underline font-bold"
            >
              Contact us at hello@blamegpt.io
            </a>
          </div>

          <div className="flex justify-center mt-12">
            <div className="max-w-[860px] lg:max-w-[920px] w-full">
              <div className="rounded-2xl p-2 border border-border/60 bg-background/20">
                <video
                  src="/blamegpt.mp4"
                  className="w-full h-auto rounded-xl"
                  autoPlay
                  muted
                  loop
                  playsInline
                  preload="auto"
                  poster="/images/change-summary.png"
                />
              </div>
            </div>
          </div>
        </div>

        <div className="relative z-10">
          <FooterSection />
        </div>
      </section>
    </div>
  );
}
