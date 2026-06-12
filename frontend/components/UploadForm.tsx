"use client";

import { useCallback, useRef, useState } from "react";

interface UploadFormProps {
  onSubmit: (file: File | null, githubUrl: string) => void;
  isLoading: boolean;
}

export default function UploadForm({ onSubmit, isLoading }: UploadFormProps) {
  const [file, setFile] = useState<File | null>(null);
  const [githubUrl, setGithubUrl] = useState("");
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    const droppedFile = e.dataTransfer.files?.[0];
    if (droppedFile && droppedFile.type === "application/pdf") {
      setFile(droppedFile);
    }
  }, []);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selected = e.target.files?.[0];
    if (selected) {
      setFile(selected);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!file && !githubUrl.trim()) return;
    onSubmit(file, githubUrl.trim());
  };

  const canSubmit = (file || githubUrl.trim()) && !isLoading;

  return (
    <form onSubmit={handleSubmit} className="w-full max-w-lg mx-auto space-y-6">
      {/* PDF Dropzone */}
      <div
        className={`dropzone p-8 text-center transition-all ${
          dragActive ? "active" : ""
        }`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        id="resume-dropzone"
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf"
          onChange={handleFileChange}
          className="hidden"
          id="resume-file-input"
        />

        {file ? (
          <div className="space-y-2">
            <div className="text-3xl">📄</div>
            <p className="text-foreground font-medium">{file.name}</p>
            <p className="text-muted text-sm">
              {(file.size / 1024 / 1024).toFixed(2)} MB
            </p>
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                setFile(null);
              }}
              className="text-danger text-sm hover:underline mt-1"
            >
              Remove
            </button>
          </div>
        ) : (
          <div className="space-y-2">
            <div className="text-4xl opacity-50">📎</div>
            <p className="text-muted">
              <span className="text-accent font-medium">Click to upload</span>{" "}
              or drag & drop your resume
            </p>
            <p className="text-muted/60 text-xs">PDF only, max 10MB</p>
          </div>
        )}
      </div>

      {/* GitHub URL Input */}
      <div className="space-y-2">
        <label
          htmlFor="github-url-input"
          className="block text-sm font-medium text-muted"
        >
          GitHub Profile
        </label>
        <div className="relative">
          <span className="absolute left-3 top-1/2 -translate-y-1/2 text-muted/60 text-sm font-mono">
            github.com/
          </span>
          <input
            id="github-url-input"
            type="text"
            value={githubUrl}
            onChange={(e) => setGithubUrl(e.target.value)}
            placeholder="username"
            className="w-full bg-card-bg border border-card-border rounded-lg px-3 py-3 pl-28
                       text-foreground placeholder:text-muted/40 font-mono text-sm
                       focus:outline-none focus:border-accent focus:ring-1 focus:ring-accent/30
                       transition-all"
          />
        </div>
      </div>

      {/* Submit Button */}
      <button
        type="submit"
        disabled={!canSubmit}
        id="submit-analysis-btn"
        className={`w-full py-3.5 rounded-lg font-semibold text-sm tracking-wide
                   transition-all duration-300 ${
                     canSubmit
                       ? "bg-accent hover:bg-accent-hover text-white cursor-pointer animate-pulse-glow"
                       : "bg-card-bg text-muted/50 cursor-not-allowed border border-card-border"
                   }`}
      >
        {isLoading ? (
          <span className="flex items-center justify-center gap-2">
            <svg
              className="animate-spin h-4 w-4"
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
            Analyzing your profile...
          </span>
        ) : (
          "Analyze My Profile →"
        )}
      </button>
    </form>
  );
}
