import { ArticleCard } from "../components/ArticleCard";
import { EmptyState } from "../components/EmptyState";
import { LoadingState } from "../components/LoadingState";
import { SearchBar } from "../components/SearchBar";
import { VerifyResponse } from "../services/api";

type ResultsPageProps = {
  query: string;
  loading: boolean;
  response: VerifyResponse | null;
  error: string | null;
  onSearch: (claim: string) => void;
};

function verdictSentence(verdict: string): { className: string; text: string } {
  const value = verdict.toUpperCase();
  if (value === "TRUE") {
    return {
      className: "status-true",
      text: "According to verified fact-check organizations, this claim is supported by available evidence."
    };
  }
  if (value === "FALSE") {
    return {
      className: "status-false",
      text: "According to multiple verified fact-check articles, this claim is false."
    };
  }
  if (["PARTLY TRUE", "MISLEADING", "MIXED"].includes(value)) {
    return {
      className: "status-partly",
      text: "Current fact-check articles indicate that this claim is misleading or missing context."
    };
  }
  return {
    className: "status-unverified",
    text: "Verified sources do not currently provide sufficient evidence to confirm this claim."
  };
}

function shortSummary(summary: string): string {
  const sentences = summary.split(".").map((sentence) => sentence.trim()).filter(Boolean);
  return sentences.length ? `${sentences.slice(0, 3).join(". ")}.` : summary;
}

export function ResultsPage({ query, loading, response, error, onSearch }: ResultsPageProps) {
  const results = response?.results ?? [];
  const report = response?.report;
  const factChecks = results.filter((result) => result.source_api === "factcheck");
  const relatedNews = results.filter((result) => result.source_api !== "factcheck");

  const hasNoVerifiedCoverage =
    response?.ok &&
    !factChecks.length &&
    !report?.professional_fact_checks &&
    (report?.verdict ?? "UNVERIFIABLE") === "UNVERIFIABLE";

  const verdict = verdictSentence(report?.verdict ?? "UNVERIFIABLE");

  return (
    <>
      <div className="sticky-search-row">
        <span className="sticky-logo">Verif<span className="accent">AI</span></span>
      </div>
      <SearchBar initialValue={query} compact disabled={loading} onSearch={onSearch} />

      {loading ? <LoadingState /> : null}
      {error ? <EmptyState title="Request Error" description={error} /> : null}
      {!loading && response && !response.ok ? <EmptyState title={response.error ?? "Error"} description={response.message} /> : null}
      {!loading && hasNoVerifiedCoverage ? (
        <EmptyState
          title="No Verified Coverage Found"
          description="No verified fact-check articles were found for this claim. This does not necessarily mean the claim is true or false. Try searching using different keywords or a more specific claim."
        />
      ) : null}

      {!loading && response?.ok && !hasNoVerifiedCoverage ? (
        <section className="results-content">
          <h3 className={`verdict-sentence ${verdict.className}`}>{verdict.text}</h3>
          <div className="claim-box">
            <div className="claim-label">Claim</div>
            <div className="claim-text">{response.claim}</div>
          </div>

          {report?.summary ? (
            <>
              <div className="section-eyebrow">Summary</div>
              <div className="summary-text">{shortSummary(report.summary)}</div>
            </>
          ) : null}

          {factChecks.length ? (
            <section>
              <h2>Supporting Articles</h2>
              {factChecks.map((result) => <ArticleCard key={result.url} result={result} factCheck />)}
            </section>
          ) : null}

          {relatedNews.length ? (
            <section>
              <h2>Related News</h2>
              <div className="related-news-note">Additional context from news coverage — not verified fact-checks.</div>
              {relatedNews.map((result) => <ArticleCard key={result.url} result={result} />)}
            </section>
          ) : null}
        </section>
      ) : null}
    </>
  );
}
