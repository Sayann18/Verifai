export type SearchResult = {
  title: string;
  url: string;
  snippet: string;
  source_api: string;
  published_date: string | null;
  relevance_score: number;
  authority_score: number;
  combined_score: number;
  claim_rating: string | null;
  fact_checker: string | null;
};

export type FactCheckReport = {
  verdict: string;
  confidence: number;
  summary: string;
  detailed_explanation: string;
  supporting_evidence: string;
  contradicting_evidence: string;
  professional_fact_checks: string;
  latest_news_summary: string;
  sources: string;
  raw_response: string;
};

export type VerifyResponse = {
  ok: boolean;
  error: string | null;
  message: string;
  claim: string;
  results: SearchResult[];
  report: FactCheckReport;
  stats: Record<string, unknown> | null;
};

export async function verifyClaim(claim: string): Promise<VerifyResponse> {
  const response = await fetch("/api/verify", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ claim })
  });

  if (!response.ok) {
    throw new Error("Verification request failed.");
  }

  return response.json();
}
