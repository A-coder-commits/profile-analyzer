/**
 * API client for the Developer Profile Analyzer backend.
 *
 * All functions target the FastAPI server at http://localhost:8000.
 * Uses native fetch — no external dependencies needed.
 */

const API_BASE = "http://localhost:8000";

// ── Types ───────────────────────────────────────────────────────────────────

export interface ResumeUploadResponse {
  success: boolean;
  filename: string;
  pages_extracted: number;
  chunks_stored: number;
  text_preview: string;
}

export interface RepoSummary {
  name: string;
  description: string | null;
  language: string | null;
  stars: number;
  forks: number;
  last_updated: string | null;
}

export interface GitHubUploadResponse {
  success: boolean;
  username: string;
  total_repos: number;
  top_languages: Record<string, number>;
  repos: RepoSummary[];
  chunks_stored: number;
}

export interface StrengthItem {
  title: string;
  description: string;
}

export interface WeaknessItem {
  title: string;
  description: string;
}

export interface TopProject {
  name: string;
  reason: string;
}

export interface RoadmapStep {
  week: string;
  title: string;
  description: string;
  resources: string[];
}

export interface AnalysisResponse {
  strengths: StrengthItem[];
  weaknesses: WeaknessItem[];
  top_projects: TopProject[];
  roadmap: RoadmapStep[];
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

// ── API Functions ───────────────────────────────────────────────────────────

/**
 * Upload a PDF resume file.
 */
export async function uploadResume(file: File): Promise<ResumeUploadResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(`${API_BASE}/upload/resume`, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Upload failed" }));
    throw new Error(err.detail || `Upload failed (${res.status})`);
  }

  return res.json();
}

/**
 * Submit a GitHub profile URL for scraping.
 */
export async function uploadGitHub(
  githubUrl: string
): Promise<GitHubUploadResponse> {
  const res = await fetch(`${API_BASE}/upload/github`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ github_url: githubUrl }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "GitHub fetch failed" }));
    throw new Error(err.detail || `GitHub fetch failed (${res.status})`);
  }

  return res.json();
}

/**
 * Trigger full profile analysis.
 */
export async function analyzeProfile(): Promise<AnalysisResponse> {
  const res = await fetch(`${API_BASE}/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Analysis failed" }));
    throw new Error(err.detail || `Analysis failed (${res.status})`);
  }

  return res.json();
}

/**
 * Stream a chat response from the backend via SSE.
 *
 * @param message  - The user's message
 * @param history  - Previous conversation messages
 * @param onToken  - Callback invoked for each token received
 * @param onDone   - Callback invoked when the stream ends
 * @param onError  - Callback invoked on errors
 */
export async function streamChat(
  message: string,
  history: ChatMessage[],
  onToken: (token: string) => void,
  onDone: () => void,
  onError: (error: string) => void
): Promise<void> {
  try {
    const res = await fetch(`${API_BASE}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, history }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: "Chat failed" }));
      onError(err.detail || `Chat failed (${res.status})`);
      return;
    }

    const reader = res.body?.getReader();
    if (!reader) {
      onError("No response body");
      return;
    }

    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() || "";

      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed || !trimmed.startsWith("data: ")) continue;

        const data = trimmed.slice(6);
        if (data === "[DONE]") {
          onDone();
          return;
        }

        try {
          const parsed = JSON.parse(data);
          if (parsed.error) {
            onError(parsed.error);
            return;
          }
          if (parsed.token) {
            onToken(parsed.token);
          }
        } catch {
          // Skip malformed JSON lines
        }
      }
    }

    onDone();
  } catch (err) {
    onError(err instanceof Error ? err.message : "Network error");
  }
}
