import { FormEvent, useEffect, useState } from "react";

const placeholders = [
  "Paste a news headline or claim...",
  "Verify a viral message...",
  "Check if this article is true...",
  "Search a fact-checked claim...",
  "Verify a political statement..."
];

type SearchBarProps = {
  initialValue: string;
  compact?: boolean;
  disabled?: boolean;
  onSearch: (claim: string) => void;
};

export function SearchBar({ initialValue, compact = false, disabled = false, onSearch }: SearchBarProps) {
  const [value, setValue] = useState(initialValue);
  const [placeholderIndex, setPlaceholderIndex] = useState(0);

  useEffect(() => {
    setValue(initialValue);
  }, [initialValue]);

  useEffect(() => {
    const timer = window.setInterval(() => {
      setPlaceholderIndex((current) => (current + 1) % placeholders.length);
    }, 3500);
    return () => window.clearInterval(timer);
  }, []);

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    onSearch(value);
  }

  return (
    <form className={compact ? "search-form compact" : "search-form"} onSubmit={handleSubmit}>
      <label className="sr-only" htmlFor={compact ? "results-search" : "landing-search"}>Search</label>
      <div className="search-input-shell">
        <span className="search-icon-left" aria-hidden="true">⌕</span>
        <input
          id={compact ? "results-search" : "landing-search"}
          type="text"
          value={value}
          disabled={disabled}
          placeholder={placeholders[placeholderIndex]}
          onChange={(event) => setValue(event.target.value)}
        />
        <button className="search-btn-right" type="submit" disabled={disabled} title="Search">
          ⌕
        </button>
      </div>
    </form>
  );
}
