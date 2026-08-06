export type TrendingItem = {
  img: string;
  category: string;
  catClass: string;
  headline: string;
  time: string;
};

type TrendingListProps = {
  items: TrendingItem[];
  onSelect: (claim: string) => void;
};

export function TrendingList({ items, onSelect }: TrendingListProps) {
  return (
    <section className="trending-card">
      <div className="trending-header">
        <div className="trending-title">Trending Now</div>
        <a className="trending-viewall" href="#trending">View all ›</a>
      </div>
      {items.map((item) => (
        <button className="trend-row" key={item.headline} type="button" onClick={() => onSelect(item.headline)}>
          <span className="trend-row-inner">
            <img className="trend-thumb" src={item.img} alt="" />
            <span className="trend-body">
              <span className={`trend-category ${item.catClass}`}>{item.category}</span>
              <span className="trend-headline">{item.headline}</span>
            </span>
            <span className="trend-time">{item.time}</span>
          </span>
        </button>
      ))}
    </section>
  );
}
