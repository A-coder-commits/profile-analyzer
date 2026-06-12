"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import InsightCard from "@/components/InsightCard";
import RoadmapTimeline from "@/components/RoadmapTimeline";
import type { AnalysisResponse } from "@/lib/api";

function SkeletonSection() {
  return (
    <div className="space-y-4">
      <div className="skeleton h-6 w-40" />
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="skeleton h-28 w-full" />
        ))}
      </div>
    </div>
  );
}

export default function AnalyzePage() {
  const router = useRouter();
  const [results, setResults] = useState<AnalysisResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const stored = localStorage.getItem("analysisResults");
    if (stored) {
      try {
        setResults(JSON.parse(stored));
      } catch {
        router.push("/");
        return;
      }
    } else {
      router.push("/");
      return;
    }
    setLoading(false);
  }, [router]);

  if (loading || !results) {
    return (
      <main className="flex-1 max-w-4xl mx-auto px-6 py-12 w-full">
        <div className="skeleton h-10 w-64 mb-2" />
        <div className="skeleton h-5 w-96 mb-12" />
        <div className="space-y-12">
          <SkeletonSection />
          <SkeletonSection />
          <SkeletonSection />
        </div>
      </main>
    );
  }

  return (
    <main className="flex-1 max-w-4xl mx-auto px-6 py-12 w-full">
      {/* Background gradient */}
      <div className="fixed inset-0 -z-10">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_rgba(99,102,241,0.06)_0%,_transparent_50%)]" />
      </div>

      {/* Header */}
      <div className="mb-12 animate-fade-in">
        <Link
          href="/"
          className="inline-flex items-center gap-1 text-muted text-sm hover:text-accent transition-colors mb-6"
          id="back-to-home"
        >
          ← Back
        </Link>

        <h1 className="text-3xl font-bold tracking-tight mb-2">
          Your Profile{" "}
          <span className="bg-gradient-to-r from-accent to-purple-400 bg-clip-text text-transparent">
            Analysis
          </span>
        </h1>
        <p className="text-muted">
          Here&apos;s what we found — the good, the gaps, and the plan.
        </p>
      </div>

      <div className="space-y-14">
        {/* ── Strengths ── */}
        {results.strengths.length > 0 && (
          <section id="strengths-section">
            <div className="flex items-center gap-2 mb-5">
              <span className="text-xl">💪</span>
              <h2 className="text-xl font-semibold">Strengths</h2>
              <span className="text-xs text-muted ml-auto font-mono">
                {results.strengths.length} identified
              </span>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {results.strengths.map((item, idx) => (
                <InsightCard
                  key={idx}
                  title={item.title}
                  description={item.description}
                  variant="strength"
                  index={idx}
                />
              ))}
            </div>
          </section>
        )}

        {/* ── Weaknesses / Gaps ── */}
        {results.weaknesses.length > 0 && (
          <section id="weaknesses-section">
            <div className="flex items-center gap-2 mb-5">
              <span className="text-xl">⚠️</span>
              <h2 className="text-xl font-semibold">Skill Gaps</h2>
              <span className="text-xs text-muted ml-auto font-mono">
                {results.weaknesses.length} identified
              </span>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {results.weaknesses.map((item, idx) => (
                <InsightCard
                  key={idx}
                  title={item.title}
                  description={item.description}
                  variant="weakness"
                  index={idx}
                />
              ))}
            </div>
          </section>
        )}

        {/* ── Top Projects ── */}
        {results.top_projects.length > 0 && (
          <section id="projects-section">
            <div className="flex items-center gap-2 mb-5">
              <span className="text-xl">🚀</span>
              <h2 className="text-xl font-semibold">Top Projects</h2>
              <span className="text-xs text-muted ml-auto font-mono">
                {results.top_projects.length} highlighted
              </span>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {results.top_projects.map((item, idx) => (
                <InsightCard
                  key={idx}
                  title={item.name}
                  description={item.reason}
                  variant="project"
                  index={idx}
                />
              ))}
            </div>
          </section>
        )}

        {/* ── Roadmap ── */}
        {results.roadmap.length > 0 && (
          <section id="roadmap-section">
            <div className="flex items-center gap-2 mb-5">
              <span className="text-xl">🗺️</span>
              <h2 className="text-xl font-semibold">
                3-Month Learning Roadmap
              </h2>
            </div>
            <RoadmapTimeline steps={results.roadmap} />
          </section>
        )}
      </div>

      {/* Chat CTA */}
      <div className="mt-16 text-center animate-fade-in" style={{ animationDelay: "800ms", animationFillMode: "both" }}>
        <div className="inline-block p-px rounded-xl bg-gradient-to-r from-accent to-purple-500">
          <Link
            href="/chat"
            className="block bg-background px-8 py-4 rounded-xl hover:bg-card-bg transition-colors"
            id="go-to-chat-btn"
          >
            <span className="text-foreground font-semibold">
              💬 Chat with your profile
            </span>
            <p className="text-muted text-xs mt-1">
              Ask follow-up questions, get deeper insights
            </p>
          </Link>
        </div>
      </div>
    </main>
  );
}
