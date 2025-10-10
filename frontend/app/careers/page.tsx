'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { FooterSection } from '@/components/footer-section';
import { Mail, MapPin, Clock } from 'lucide-react';

const jobs = [
  {
    title: 'Founding Engineer',
    description: 'Join our founding team to build the future of AI-powered code review. You\'ll work on core product features, architecture, and help shape the technical direction of BlameGPT. Please send an email introducing yourself, along with cool things you\'ve built or sold.',
  },
  {
    title: 'Sales Development Representative (SDR)',
    description: 'Drive growth by identifying and engaging with potential customers. You\'ll be responsible for generating leads, qualifying prospects, and building our sales pipeline. Please send an email introducing yourself, along with your sales experience and revenue you\'ve generated.',
  },
];

export default function CareersPage() {
  return (
    <div className="min-h-screen bg-background">
      <section className="py-20 lg:py-32">
        <div className="max-w-[1320px] mx-auto px-4 md:px-6">
          <div className="max-w-4xl mx-auto text-center mb-16">
            <h1 className="text-4xl md:text-5xl lg:text-7xl font-semibold leading-tight mb-8">
              Careers
            </h1>
            <p className="text-lg text-muted-foreground">
              Join us in building the future of AI-powered code review and security analysis.
            </p>
          </div>

          <div className="max-w-4xl mx-auto space-y-8">
            {jobs.map((job, index) => (
              <Card key={index} className="p-6">
                <CardHeader className="pb-4">
                  <CardTitle className="text-2xl mb-4">{job.title}</CardTitle>
                  <div className="flex flex-wrap gap-4 text-sm text-muted-foreground">
                    <div className="flex items-center gap-2">
                      <MapPin className="w-4 h-4" />
                      <span>Remote</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Clock className="w-4 h-4" />
                      <span>Full time</span>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <p className="text-muted-foreground mb-6">
                    {job.description}
                  </p>
                  <div className="flex items-center gap-2">
                    <Mail className="w-4 h-4" />
                    <span className="text-sm text-muted-foreground">Apply:</span>
                    <a 
                      href="mailto:hello@blamegpt.io" 
                      className="text-sm text-primary hover:underline"
                    >
                      hello@blamegpt.io
                    </a>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      <FooterSection />
    </div>
  );
}