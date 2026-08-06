export function LoadingState() {
  return (
    <div className="skeleton-wrapper" aria-live="polite">
      <div className="skeleton-title skeleton-line" />
      <div className="skeleton-line" />
      <div className="skeleton-line" />
      <div className="skeleton-line short" />
      <div className="loading-message">Analyzing claim context and evidence...</div>
    </div>
  );
}
