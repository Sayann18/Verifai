import { SearchBar } from "../components/SearchBar";
import { TrendingItem, TrendingList } from "../components/TrendingList";

const trendingItems: TrendingItem[] = [
  {
    img: "https://images.unsplash.com/photo-1517976487492-5750f3195933?w=100&q=80",
    category: "Science",
    catClass: "cat-science",
    headline: "ISRO successfully launches SSLV-D3 mission",
    time: "2h ago"
  },
  {
    img: "https://images.unsplash.com/photo-1541872703-74c5e44368f9?w=100&q=80",
    category: "Politics",
    catClass: "cat-politics",
    headline: "Parliament passes new digital data protection bill",
    time: "3h ago"
  },
  {
    img: "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=100&q=80",
    category: "Business",
    catClass: "cat-business",
    headline: "Sensex hits all-time high; Nifty closes above 24,500",
    time: "5h ago"
  },
  {
    img: "https://images.unsplash.com/photo-1529107386315-e1a2ed48a620?w=100&q=80",
    category: "World",
    catClass: "cat-world",
    headline: "G20 leaders call for global cooperation on AI regulation",
    time: "6h ago"
  },
  {
    img: "https://images.unsplash.com/photo-1554224155-8d04cb21cd6c?w=100&q=80",
    category: "World",
    catClass: "cat-world",
    headline: "US Federal Reserve keeps interest rates unchanged",
    time: "7h ago"
  }
];

type LandingPageProps = {
  initialQuery: string;
  loading: boolean;
  onSearch: (claim: string) => void;
};

export function LandingPage({ initialQuery, loading, onSearch }: LandingPageProps) {
  return (
    <>
      <h1 className="hero-heading">
        Verify. Trust. Share. <span className="accent">Truth.</span>
      </h1>
      <div className="hero-tagline">
        Search any claim, headline, or statement and get verified fact-checks from trusted sources.
      </div>
      <SearchBar initialValue={initialQuery} disabled={loading} onSearch={onSearch} />
      <div className="search-hint">
        <span className="accent-icon">↗</span> Tip: Try searching a claim or headline to get started
      </div>
      <TrendingList items={trendingItems} onSelect={onSearch} />
      <div className="footer-note">Powered by Google Fact Check</div>
    </>
  );
}
