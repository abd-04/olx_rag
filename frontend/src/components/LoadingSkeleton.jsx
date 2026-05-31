export default function LoadingSkeleton() {
  return (
    <div className="results-grid" aria-label="Loading results">
      {[0, 1, 2].map((item) => (
        <div className="listing-card skeleton-card" key={item}>
          <span className="skeleton skeleton--pill" />
          <span className="skeleton skeleton--title" />
          <span className="skeleton skeleton--price" />
          <span className="skeleton skeleton--line" />
          <span className="skeleton skeleton--line" />
          <span className="skeleton skeleton--button" />
        </div>
      ))}
    </div>
  );
}
