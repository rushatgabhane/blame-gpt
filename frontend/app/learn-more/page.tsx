'use client';

import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { FooterSection } from '@/components/footer-section';
import {
  Shield,
  Database,
  Server,
  Bug,
  AlertTriangle,
  CheckCircle,
  Clock,
  Zap,
  Github,
  ChevronDown,
  ArrowLeftRight,
} from 'lucide-react';

const howItWorksSteps = [
  {
    step: 'Step 1',
    title: 'Create a PR and comment @BlameGPT review',
  },
  {
    step: 'Step 2',
    title: 'Get instant PR feedback with issues that you might have missed',
  },
  {
    step: 'Step 3',
    title: 'Push more commits → re-review by commenting - @BlameGPT review',
  },
  {
    step: 'Step 4',
    title: "Clean PR ready for an engineer's final review",
  },
];

const installationSteps = [
  {
    step: 'Step 1',
    title: 'Select repositories',
    description:
      'Choose which repositories you want BlameGPT to do PR code reviews.',
  },
  {
    step: 'Step 2',
    title: 'Deploy server: clone repo and docker compose up',
    description:
      'Clone our repository and start the server with a simple docker compose command.',
  },
  {
    step: 'Step 3',
    title: 'Create a LLM API key (OpenAI, Claude, Azure OpenAI or AWS Bedrock)',
    description:
      "Add your preferred AI provider's API keys to enable intelligent code analysis.",
  },
];

const architectureComponents = [
  { name: 'PR on Github', icon: Github, color: 'text-purple-600' },
  {
    name: 'BlameGPT server on your infra',
    icon: Server,
    color: 'text-blue-600',
  },
  // { name: 'SQLite', icon: Database, color: 'text-green-600' },
  { name: 'LLM Provider', icon: Shield, color: 'text-red-600' },
];

export default function LearnMorePage() {
  return (
    <div className="min-h-screen bg-background">
      {/* The Problem Section */}
      <section className="py-20 lg:py-32">
        <div className="max-w-[1320px] mx-auto px-4 md:px-6">
          <div className="max-w-4xl mx-auto text-center">
            <h2 className="text-4xl md:text-5xl lg:text-7xl font-semibold leading-tight mb-8">
              The problem
            </h2>
            <div className="text-lg text-muted-foreground space-y-4">
              <p>
                AI increases developer productivity, but PR reviews fall behind
                and are a bottleneck. Senior engineers drown in 20+ file PRs,
                that may have subtle bugs and vulnerabilities that may slip
                through.
              </p>
            </div>

            <div className="grid md:grid-cols-3 gap-6 mt-12">
              <Card className="text-center p-6">
                <Bug className="w-12 h-12 text-red-500 mx-auto mb-4" />
                <h3 className="mb-2">
                  AI-generated code hides issues and security bugs
                </h3>
              </Card>
              <Card className="text-center p-6">
                <Clock className="w-12 h-12 text-orange-500 mx-auto mb-4" />
                <h3 className="mb-2">
                  PR reviews bottleneck on senior engineers
                </h3>
              </Card>
              <Card className="text-center p-6">
                <AlertTriangle className="w-12 h-12 text-yellow-500 mx-auto mb-4" />
                <h3 className="mb-2">
                  Bugs and vulnerabilities can be hard to spot, especially from
                  AI generated code
                </h3>
              </Card>
            </div>
          </div>
        </div>
        {/* Down arrow indicator */}
        <div className="flex justify-center mt-12">
          <ChevronDown className="w-8 h-8 text-muted-foreground animate-bounce" />
        </div>
      </section>

      {/* How It Works Section */}
      <section className="py-20 lg:py-32 ">
        <div className="max-w-[1320px] mx-auto px-4 md:px-6">
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl lg:text-7xl font-semibold leading-tight mb-4">
              How it works?
            </h2>
            <p className="text-lg text-muted-foreground">
              50–70% faster merges, fewer bugs, and consistent quality reducing
              review bottlenecks.
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
            {howItWorksSteps.map((step, index) => (
              <Card key={index} className="relative">
                <CardHeader>
                  <Badge variant="outline" className="w-fit mb-2">
                    {step.step}
                  </Badge>
                  <CardTitle className="text-lg">{step.title}</CardTitle>
                </CardHeader>
                {step.description && (
                  <CardContent>
                    <p className="text-sm text-muted-foreground">
                      {step.description}
                    </p>
                  </CardContent>
                )}
              </Card>
            ))}
          </div>
        </div>
        {/* Down arrow indicator */}
        <div className="flex justify-center mt-12">
          <ChevronDown className="w-8 h-8 text-muted-foreground animate-bounce" />
        </div>
      </section>

      {/* Security-first Architecture */}
      <section className="pt-20 lg:py-32 ">
        <div className="max-w-[1320px] mx-auto px-4 md:px-6">
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl lg:text-7xl font-semibold leading-tight mb-4">
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
        {/* Down arrow indicator */}
        <div className="flex justify-center mt-12">
          <ChevronDown className="w-8 h-8 text-muted-foreground animate-bounce" />
        </div>
      </section>

      {/* Installation Section */}
      <section className="py-20 lg:py-20 ">
        <div className="max-w-[1320px] mx-auto px-4 md:px-6">
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl lg:text-7xl font-semibold leading-tight mb-4">
              Installation in 10 minutes
            </h2>
            <p className="text-lg text-muted-foreground mb-4">
              Self-hosted with minimal infrastructure (any 1 GB RAM Linux
              server).
            </p>
          </div>

          <div className="max-w-4xl mx-auto">
            <div className="space-y-8">
              {installationSteps.map((step, index) => (
                <div key={index} className="flex gap-6">
                  <div className="flex flex-col items-center">
                    <div className="w-12 h-12 bg-primary rounded-full flex items-center justify-center text-primary-foreground font-medium">
                      {index + 1}
                    </div>
                    {index < installationSteps.length - 1 && (
                      <div className="w-px h-16 bg-border mt-4" />
                    )}
                  </div>
                  <div className="flex-1 pb-8">
                    <Badge variant="outline" className="mb-2">
                      {step.step}
                    </Badge>
                    <h3 className="text-lg mb-2">{step.title}</h3>
                    <p className="text-muted-foreground">{step.description}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
        {/* Down arrow indicator */}
        <div className="flex justify-center mt-12">
          <ChevronDown className="w-8 h-8 text-muted-foreground animate-bounce" />
        </div>
      </section>

      {/* Dependency Vulnerability Scanning */}
      <section className="py-20 lg:py-32 ">
        <div className="max-w-[1320px] mx-auto px-4 md:px-6">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div>
              <h2 className="text-4xl md:text-5xl lg:text-7xl font-semibold leading-tight mb-6">
                Dependency vulnerability scanning
              </h2>
              <p className="text-lg text-muted-foreground mb-8">
                Continuous checks across multiple databases with actionable
                alerts and compliance mapping.
              </p>
              <div className="space-y-4">
                <div className="flex items-center gap-3">
                  <CheckCircle className="w-5 h-5 text-green-500" />
                  <span>Cross-checks GitHub Advisories, OSV.dev, and NVD</span>
                </div>
                <div className="flex items-center gap-3">
                  <CheckCircle className="w-5 h-5 text-green-500" />
                  <span>Alerts on vulnerable dependencies added in PRs</span>
                </div>
                <div className="flex items-center gap-3">
                  <CheckCircle className="w-5 h-5 text-green-500" />
                  <span>Dashboard visibility for existing vulnerabilities</span>
                </div>
                <div className="flex items-center gap-3">
                  <CheckCircle className="w-5 h-5 text-green-500" />
                  <span>Optional GitHub Issues or Slack alerts</span>
                </div>
                <div className="flex items-center gap-3">
                  <CheckCircle className="w-5 h-5 text-green-500" />
                  <span>CWE mapping for compliance</span>
                </div>
              </div>
            </div>
            <div className="bg-muted/50 rounded-2xl p-8 text-center">
              <Shield className="w-20 h-20 mx-auto mb-4 text-blue-500" />
              <h3 className="text-lg mb-2">Security First</h3>
              <p className="text-muted-foreground">
                Comprehensive vulnerability detection
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Production Debugging */}
      <section className="py-20 lg:py-32 ">
        <div className="max-w-[1320px] mx-auto px-4 md:px-6">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div>
              <h2 className="text-4xl md:text-5xl lg:text-7xl font-semibold leading-tight mb-6">
                Blame analysis for production issues
              </h2>
              <p className="text-lg text-muted-foreground mb-8">
                Trace incidents to the offending commit and resolve production
                issues faster.
              </p>
              <div className="space-y-4">
                <div className="flex items-center gap-3">
                  <CheckCircle className="w-5 h-5 text-green-500" />
                  <span>Trace errors back to specific PRs/commits</span>
                </div>
                <div className="flex items-center gap-3">
                  <CheckCircle className="w-5 h-5 text-green-500" />
                  <span>Faster root cause analysis and reduced MTTR</span>
                </div>
                <div className="flex items-center gap-3">
                  <CheckCircle className="w-5 h-5 text-green-500" />
                  <span>
                    Visibility into when and where regressions were introduced
                  </span>
                </div>
              </div>
            </div>
            <div className="bg-muted/50 rounded-2xl p-8 text-center">
              <Bug className="w-20 h-20 mx-auto mb-4 text-red-500" />
              <h3 className="text-lg mb-2">Debug Faster</h3>
              <p className="text-muted-foreground">
                Trace issues to their source
              </p>
            </div>
          </div>
        </div>
      </section>

      <FooterSection />
    </div>
  );
}
