"use client";

import type { RoadmapStep } from "@/lib/api";

interface RoadmapTimelineProps {
  steps: RoadmapStep[];
}

export default function RoadmapTimeline({ steps }: RoadmapTimelineProps) {
  if (!steps.length) return null;

  return (
    <div className="relative" id="roadmap-timeline">
      {/* Vertical line */}
      <div className="absolute left-5 top-0 bottom-0 w-px bg-gradient-to-b from-accent via-accent/40 to-transparent" />

      <div className="space-y-8">
        {steps.map((step, index) => (
          <div
            key={index}
            className="relative pl-14 animate-slide-up"
            style={{
              animationDelay: `${index * 150}ms`,
              animationFillMode: "both",
            }}
            id={`roadmap-step-${index}`}
          >
            {/* Timeline node */}
            <div className="absolute left-3 top-1 w-5 h-5 rounded-full bg-background border-2 border-accent flex items-center justify-center">
              <div className="w-2 h-2 rounded-full bg-accent" />
            </div>

            {/* Content card */}
            <div className="group bg-card-bg border border-card-border rounded-xl p-5 transition-all duration-300 hover:border-accent/30 hover:shadow-lg hover:shadow-accent/5">
              {/* Week badge */}
              <div className="flex items-center gap-3 mb-3">
                <span className="inline-flex items-center px-2.5 py-1 rounded-full bg-accent/10 text-accent text-xs font-semibold font-mono tracking-wide">
                  {step.week}
                </span>
                <h3 className="font-semibold text-foreground text-sm">
                  {step.title}
                </h3>
              </div>

              <p className="text-foreground/70 text-sm leading-relaxed mb-3">
                {step.description}
              </p>

              {/* Resources */}
              {step.resources.length > 0 && (
                <div className="space-y-1.5">
                  <p className="text-muted text-xs font-medium uppercase tracking-wider">
                    Resources
                  </p>
                  <ul className="space-y-1">
                    {step.resources.map((resource, rIdx) => (
                      <li
                        key={rIdx}
                        className="text-accent/80 text-xs flex items-center gap-1.5"
                      >
                        <span className="text-accent/40">→</span>
                        <span className="font-mono">{resource}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
