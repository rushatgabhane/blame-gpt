'use client';

import { FooterSection } from '@/components/footer-section';

export default function PrivacyPage() {
  return (
    <div className="min-h-screen bg-background">
      <section className="py-20 lg:py-32">
        <div className="max-w-4xl mx-auto px-4 md:px-6">
          <div className="mb-16">
            <h1 className="text-4xl md:text-5xl lg:text-6xl font-semibold leading-tight mb-4">
              Privacy Policy
            </h1>
            <p className="text-lg text-muted-foreground">
              Last updated: {new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })}
            </p>
          </div>

          <div className="prose prose-lg max-w-none dark:prose-invert">
            <section className="mb-12">
              <h2 className="text-2xl font-semibold mb-4">Introduction</h2>
              <p className="text-muted-foreground mb-4">
                BlameGPT ("we," "our," or "us") is committed to protecting your privacy. This Privacy Policy explains how we collect, use, disclose, and safeguard your information when you use our AI-powered code review and security analysis service.
              </p>
            </section>

            <section className="mb-12">
              <h2 className="text-2xl font-semibold mb-4">Information We Collect</h2>
              
              <h3 className="text-xl font-medium mb-3">Information You Provide</h3>
              <ul className="list-disc list-inside text-muted-foreground mb-6 space-y-2">
                <li>Account information (email address, username)</li>
                <li>Communication data when you contact us</li>
                <li>Payment information (processed by third-party providers)</li>
              </ul>

              <h3 className="text-xl font-medium mb-3">Information We Collect Automatically</h3>
              <ul className="list-disc list-inside text-muted-foreground mb-4 space-y-2">
                <li>Usage data and analytics</li>
                <li>Log files and technical information</li>
                <li>Device and browser information</li>
              </ul>
            </section>

            <section className="mb-12">
              <h2 className="text-2xl font-semibold mb-4">How We Use Your Information</h2>
              <ul className="list-disc list-inside text-muted-foreground space-y-2">
                <li>Provide and maintain our code review services</li>
                <li>Process and analyze your code for security vulnerabilities</li>
                <li>Communicate with you about our services</li>
                <li>Comply with legal obligations</li>
              </ul>
            </section>

            <section className="mb-12">
              <h2 className="text-2xl font-semibold mb-4">Data Security and Storage</h2>
              <div className="bg-muted/30 p-6 rounded-lg mb-4">
                <h3 className="text-xl font-medium mb-3">Self-Hosted Architecture</h3>
                <p className="text-muted-foreground mb-4">
                  For self-hosted:
                </p>
                <ul className="list-disc list-inside text-muted-foreground space-y-2">
                  <li>Code is processed locally on your servers</li>
                  <li>Only relevant code snippets are sent to AI providers for analysis</li>
                  <li>Temporary clones are created and deleted after analysis</li>
                  <li>No data ever sent to our systems. It is airgapped</li>
                </ul>
              </div>
              
              <h3 className="text-xl font-medium mb-3">Security Measures</h3>
              <ul className="list-disc list-inside text-muted-foreground space-y-2">
                <li>Encrypted data transmission using industry-standard protocols</li>
                <li>Access controls and authentication mechanisms</li>
                <li>Regular security assessments and updates</li>
                <li>Minimal data retention policies</li>
              </ul>
            </section>

            <section className="mb-12">
              <h2 className="text-2xl font-semibold mb-4">Third-Party Services</h2>
              <p className="text-muted-foreground mb-4">
                We may use third-party services including:
              </p>
              <ul className="list-disc list-inside text-muted-foreground space-y-2">
                <li>AI/LLM providers (OpenAI, Anthropic, Azure OpenAI, AWS Bedrock)</li>
                <li>GitHub for repository access</li>
                <li>Analytics and monitoring services</li>
                <li>Payment processors</li>
              </ul>
              <p className="text-muted-foreground mt-4">
                These services have their own privacy policies governing their use of your information.
              </p>
            </section>

            <section className="mb-12">
              <h2 className="text-2xl font-semibold mb-4">Your Rights</h2>
              <p className="text-muted-foreground mb-4">
                Depending on your location, you may have the following rights:
              </p>
              <ul className="list-disc list-inside text-muted-foreground space-y-2">
                <li>Access to your personal information</li>
                <li>Correction of inaccurate data</li>
                <li>Deletion of your data</li>
                <li>Data portability</li>
                <li>Opt-out of certain processing activities</li>
              </ul>
            </section>

            <section className="mb-12">
              <h2 className="text-2xl font-semibold mb-4">International Transfers</h2>
              <p className="text-muted-foreground">
                Since BlameGPT is self-hosted on your infrastructure, your data primarily remains within your chosen geographic location. However, when using third-party AI services, data may be processed in different jurisdictions according to those providers' policies.
              </p>
            </section>

            <section className="mb-12">
              <h2 className="text-2xl font-semibold mb-4">Changes to This Policy</h2>
              <p className="text-muted-foreground">
                We may update this Privacy Policy from time to time. We will notify you of any changes by posting the new Privacy Policy on this page and updating the "Last updated" date.
              </p>
            </section>

            <section className="mb-12">
              <h2 className="text-2xl font-semibold mb-4">Contact Us</h2>
              <p className="text-muted-foreground">
                If you have any questions about this Privacy Policy, please contact us at:{' '}
                <a href="mailto:hello@blamegpt.io" className="text-primary hover:underline">
                  hello@blamegpt.io
                </a>
              </p>
            </section>
          </div>
        </div>
      </section>

      <FooterSection />
    </div>
  );
}