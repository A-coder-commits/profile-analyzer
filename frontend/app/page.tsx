"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import UploadForm from "@/components/UploadForm";
import { uploadResume, uploadGitHub, analyzeProfile } from "@/lib/api";

export default function HomePage() {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);
  const [status, setStatus] = useState("");
  const [error, setError] = useState("");

  const handleSubmit = async (file: File | null, githubUrl: string) => {
    setIsLoading(true);
    setError("");

    try {
      // Step 1: Upload resume if provided
      if (file) {
        setStatus("Extracting resume text...");
        await uploadResume(file);
      }

      // Step 2: Scrape GitHub if provided
      if (githubUrl) {
        setStatus("Scraping GitHub profile...");
        await uploadGitHub(githubUrl);
      }

      // Step 3: Run analysis
      setStatus("Running AI analysis — this may take a minute...");
      const results = await analyzeProfile();

      // Store results and redirect
      localStorage.setItem("analysisResults", JSON.stringify(results));
      router.push("/analyze");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
      setIsLoading(false);
      setStatus("");
    }
  };

  return (
    <main className="flex-1 flex flex-col items-center justify-center px-6 py-16">
      {/* Background subtle gradient */}
      <div className="fixed inset-0 -z-10">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_rgba(99,102,241,0.08)_0%,_transparent_60%)]" />
      </div>

      {/* Header */}
      <div className="text-center mb-12 animate-fade-in">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-accent/10 border border-accent/20 text-accent text-xs font-medium mb-6">
          <span className="w-1.5 h-1.5 rounded-full bg-accent animate-pulse" />
          AI-Powered Analysis
        </div>

        <h1 className="text-4xl md:text-5xl font-bold tracking-tight mb-4">
          Profile{" "}
          <span className="bg-gradient-to-r from-accent to-purple-400 bg-clip-text text-transparent">
            Analyzer
          </span>
        </h1>

        <p className="text-muted text-lg max-w-md mx-auto leading-relaxed">
          Drop your resume. Share your GitHub.
          <br />
          <span className="text-foreground/80 font-medium">
            Get brutal honesty.
          </span>
        </p>
      </div>

      {/* Upload Form */}
      <div
        className="w-full max-w-lg animate-slide-up"
        style={{ animationDelay: "200ms", animationFillMode: "both" }}
      >
        <UploadForm onSubmit={handleSubmit} isLoading={isLoading} />
      </div>

      {/* Status message */}
      {status && (
        <div className="mt-6 flex items-center gap-2 text-muted text-sm animate-fade-in">
          <svg
            className="animate-spin h-4 w-4 text-accent"
            viewBox="0 0 24 24"
            fill="none"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
            />
          </svg>
          {status}
        </div>
      )}

      {/* Error message */}
      {error && (
        <div className="mt-6 px-4 py-3 rounded-lg bg-danger/10 border border-danger/30 text-danger text-sm max-w-lg text-center animate-fade-in">
          {error}
        </div>
      )}

      {/* Footer hint */}
      <div
        className="mt-16 text-center text-muted/40 text-xs animate-fade-in"
        style={{ animationDelay: "600ms", animationFillMode: "both" }}
      >
        <p>
          Powered by Claude AI • Your data stays local • Open source
        </p>
      </div>
    </main>
  );
}
