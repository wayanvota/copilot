export type Citation = {
  id: string;
  title: string;
  agency: string;
  url: string;
  effective_date?: string | null;
  publication_date?: string | null;
  retrieved_at: string;
  excerpt: string;
};

export type CitedClaim = { text: string; citations: string[] };

export type CopilotAnswer = {
  id: string;
  conversation_id: string;
  short_answer: CitedClaim[];
  why: CitedClaim[];
  rules: CitedClaim[];
  documentation: CitedClaim[];
  related_questions: string[];
  applicability: { level: "high" | "medium" | "low" | "unknown"; explanation: string };
  evidence_status: "verified" | "insufficient" | "conflicting";
  limitations: string[];
  citations: Citation[];
  created_at: string;
};

export type ChatMessage = {
  role: "user" | "assistant";
  question?: string;
  answer?: CopilotAnswer;
};
