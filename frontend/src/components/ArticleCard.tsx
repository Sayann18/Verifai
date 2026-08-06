import { SearchResult } from "../services/api";
import { formatRelativeTime, getDomain } from "../services/format";

type ArticleCardProps = {
  result: SearchResult;
  factCheck?: boolean;
};

export function ArticleCard({ result, factCheck = false }: ArticleCardProps) {
  const domain = getDomain(result.url);
  const publisher = factCheck ? result.fact_checker || "Fact Checker" : domain.split(".")[0] || "Source";
  const favicon = `https://www.google.com/s2/favicons?domain=${domain}&sz=32`;
  const rating = result.claim_rating;

  return (
    <a className={factCheck ? "article-card" : "article-card news-card"} href={result.url} target="_blank" rel="noreferrer">
      <span className="article-publisher">
        <img src={favicon} width="16" height="16" alt="" />
        {publisher}
      </span>
      <span className="article-title">{result.title}</span>
      <span className="article-meta-row">
        <span>{formatRelativeTime(result.published_date)}</span>
        {rating ? <span className="article-rating-pill">{rating}</span> : null}
      </span>
      <span className="article-cta">{factCheck ? "Read Article →" : "Open →"}</span>
    </a>
  );
}
