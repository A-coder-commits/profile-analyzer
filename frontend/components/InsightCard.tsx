"use client";

interface InsightCardProps {
  title: string;
  description: string;
  variant: "strength" | "weakness" | "project";
  index: number;
}

const VARIANT_CONFIG = {
  strength: {
    icon: "💪",
    borderColor: "border-green-accent/30",
    bgColor: "bg-green-bg",
    titleColor: "text-green-accent",
    accentDot: "bg-green-accent",
  },
  weakness: {
    icon: "⚠️",
    borderColor: "border-amber-accent/30",
    bgColor: "bg-amber-bg",
    titleColor: "text-amber-accent",
    accentDot: "bg-amber-accent",
  },
  project: {
    icon: "🚀",
    borderColor: "border-accent/30",
    bgColor: "bg-accent-glow",
    titleColor: "text-accent",
    accentDot: "bg-accent",
  },
};

export default function InsightCard({
  title,
  description,
  variant,
  index,
}: InsightCardProps) {
  const config = VARIANT_CONFIG[variant];

  return (
    <div
      className={`group relative overflow-hidden rounded-xl border ${config.borderColor}
                  ${config.bgColor} p-5 transition-all duration-300
                  hover:scale-[1.02] hover:shadow-lg hover:shadow-black/20
                  animate-slide-up`}
      style={{ animationDelay: `${index * 100}ms`, animationFillMode: "both" }}
      id={`insight-card-${variant}-${index}`}
    >
      {/* Accent dot */}
      <div
        className={`absolute top-0 right-0 w-20 h-20 ${config.accentDot} opacity-5
                    rounded-full -translate-y-1/2 translate-x-1/2
                    group-hover:opacity-10 transition-opacity`}
      />

      <div className="flex items-start gap-3">
        <span className="text-xl flex-shrink-0 mt-0.5">{config.icon}</span>
        <div className="space-y-1.5 min-w-0">
          <h3 className={`font-semibold text-sm ${config.titleColor}`}>
            {title}
          </h3>
          <p className="text-foreground/70 text-sm leading-relaxed">
            {description}
          </p>
        </div>
      </div>
    </div>
  );
}
