import type { CopilotAnswer, FarmContext, SourceSummary, SourceUpdate } from "./types";

const API_BASE_URL = (process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000").replace(/\/$/, "");

function headers(): HeadersInit {
  return {
    "Content-Type": "application/json",
  };
}

export async function askCopilot(payload: {
  question: string;
  conversation_id?: string;
  source_tiers?: number[];
  topics?: string[];
  farm_context?: FarmContext;
}): Promise<CopilotAnswer> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}/api/chat`, {
      method: "POST",
      headers: headers(),
      body: JSON.stringify(payload),
    });
  } catch {
    throw new Error("The copilot could not reach the source service. Check your connection and try again.");
  }
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail || "The copilot could not answer right now.");
  }
  return response.json();
}

export async function getSources(): Promise<SourceSummary[]> {
  const response = await fetch(`${API_BASE_URL}/api/sources`);
  if (!response.ok) throw new Error("Source status could not be loaded.");
  return response.json();
}

export async function getSourceUpdates(): Promise<SourceUpdate[]> {
  const response = await fetch(`${API_BASE_URL}/api/updates`);
  if (!response.ok) throw new Error("Source updates could not be loaded.");
  return response.json();
}

export async function sendFeedback(answerId: string, rating: "helpful" | "not_helpful", comment?: string) {
  const response = await fetch(`${API_BASE_URL}/api/feedback`, {
    method: "POST",
    headers: headers(),
    body: JSON.stringify({ answer_id: answerId, rating, comment }),
  });
  if (!response.ok) throw new Error("Feedback could not be saved.");
}

export async function bookmarkAnswer(answerId: string) {
  const response = await fetch(`${API_BASE_URL}/api/bookmarks`, {
    method: "POST",
    headers: headers(),
    body: JSON.stringify({ answer_id: answerId }),
  });
  if (!response.ok) throw new Error("Bookmark could not be saved.");
}
