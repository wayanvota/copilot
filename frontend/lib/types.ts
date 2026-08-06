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

export type FarmContext = {
  county?: string;
  operation_type: "confinement" | "open_feedlot" | "mixed" | "unknown";
  animal_unit_capacity?: number;
  manure_storage: "formed" | "unformed" | "lagoon" | "dry" | "unknown";
  workers: "family" | "nonfamily" | "both" | "unknown";
  sells_into_california: "yes" | "no" | "unknown";
};

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
  missing_facts: string[];
  limitations: string[];
  citations: Citation[];
  created_at: string;
};

export type SourceSummary = {
  id: string;
  title: string;
  agency: string;
  url: string;
  topic: string;
  source_tier: number;
  jurisdiction: string;
  status: string;
  publication_date?: string | null;
  effective_date?: string | null;
  retrieved_at: string;
};

export type SourceUpdate = {
  document_id: string;
  title: string;
  agency: string;
  url: string;
  version_count: number;
  latest_retrieved_at: string;
  previous_retrieved_at: string;
};

export type ChatMessage = {
  role: "user" | "assistant";
  question?: string;
  answer?: CopilotAnswer;
};
