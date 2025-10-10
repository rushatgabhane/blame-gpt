"use client"

import { FileText, Bot, Shield, GitBranch, Bug, Server } from "lucide-react"

interface BentoCardProps {
  title: string
  shortTitle: string
  description: string
  icon: React.ComponentType<any>
}

const BentoCard = ({ title, shortTitle, description, icon: Icon }: BentoCardProps) => {
  return (
    <div className="rounded-3xl p-6 border border-white/20 bg-card/30 backdrop-blur-sm hover:bg-card/40 transition-all duration-300 hover:-translate-y-1 group cursor-pointer">
      {/* Icon and label section */}
      <div className="flex items-center justify-between mb-6">
        <div className="w-12 h-12 bg-white/10 rounded-xl flex items-center justify-center">
          <Icon size={24} className="text-muted-foreground" />
        </div>
        <span className="text-sm font-medium text-muted-foreground bg-white/5 px-3 py-1 rounded-full">
          {shortTitle}
        </span>
      </div>
      
      {/* Title */}
      <h3 className="text-xl font-semibold text-foreground mb-3">
        {title}
      </h3>
      
      {/* Description */}
      <p className="text-muted-foreground leading-relaxed text-sm">
        {description}
      </p>
    </div>
  )
}

export function BentoSection() {
  const cards: BentoCardProps[] = [    
    {
      title: "PR summaries & incremental reviews",
      shortTitle: "Smart Reviews",
      description: "Concise overviews to assist you review a PR.",
      icon: FileText
    },
    {
      title: "Identify issues in PRs instantly",
      shortTitle: "PR review",
      description: "Automatically identify potential bugs and performance bottlenecks during code review. Receive actionable suggestions.",
      icon: Bot
    },
    {
      title: "Vulnerability scanning",
      shortTitle: "Code Security",
      description: "SAST analysis, AI security reviews, and dependency vulnerability scanning.",
      icon: Shield
    },
    {
      title: "Contextual code analysis",
      shortTitle: "Code Analysis",
      description: "Understands relationships across files with code graphs.",
      icon: GitBranch
    },
    {
      title: "Blame analysis for production bugs",
      shortTitle: "Debug Fast",
      description: "From error logs to offending commit in seconds, not hours.",
      icon: Bug
    },
    {
      title: "Self-hosted deployment",
      shortTitle: "Self Hosted",
      description: "Code is processed locally. Only relevant snippets are sent to a LLM. All on your infra.",
      icon: Server
    },
  ]

  return (
    <section className="w-full px-5 flex flex-col justify-center items-center overflow-visible bg-transparent">
      <div className="w-full py-6 md:py-10 relative flex flex-col justify-start items-start gap-4">
        <div className="w-[547px] h-[938px] absolute top-[614px] left-[80px] origin-top-left rotate-[-33.39deg] bg-primary/10 blur-[130px] z-0" />
        <div className="self-stretch py-6 md:py-10 flex flex-col justify-center items-center gap-2 z-10">
          <div className="flex flex-col justify-start items-center gap-3">
            <h2 className="w-full max-w-[655px] text-center text-foreground text-4xl md:text-6xl font-semibold leading-tight md:leading-[66px]">
              Merge PRs faster with fewer bugs.
            </h2>
            {/* <p className="w-full max-w-[600px] text-center text-muted-foreground text-lg md:text-xl font-medium leading-relaxed">
              BlameGPT brings speed, consistency, and security into your code review process. It analyzes every pull
              request, comments line by line, and surfaces vulnerabilities before they reach production.
            </p> */}
          </div>
        </div>
        <div className="self-stretch grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 items-stretch z-10">
          {cards.map((card, index) => {
            // On mobile, only show "Identify issues in PRs instantly" and "Vulnerability scanning"
            const isMobileVisible = index === 1 || index === 2; // Bot and Shield cards
            return (
              <div key={card.title} className={`${isMobileVisible ? 'block' : 'hidden md:block'}`}>
                <BentoCard {...card} />
              </div>
            );
          })}
        </div>
      </div>
    </section>
  )
}
