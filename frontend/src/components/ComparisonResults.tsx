import type { DishComparisonResponse, CompetitorPrice } from '../types/comparison';

interface ComparisonResultsProps {
  readonly result: DishComparisonResponse;
}

function StarRating({ rating }: { readonly rating: number }) {
  const full = Math.floor(rating);
  const half = rating - full >= 0.3;
  return (
    <span className="star-rating" title={`${rating} stars`}>
      {'★'.repeat(full)}
      {half ? '½' : ''}
      <span className="rating-num">{rating}</span>
    </span>
  );
}

function PriceTierBadge({ tier }: { readonly tier: string }) {
  const cls = tier === '$' ? 'tier-budget' : tier === '$$' ? 'tier-mid' : 'tier-upscale';
  return <span className={`tier-badge ${cls}`}>{tier}</span>;
}

function PriceBar({
  price,
  low,
  high,
  median,
  yourPrice,
}: {
  readonly price: number;
  readonly low: number;
  readonly high: number;
  readonly median: number;
  readonly yourPrice: number | null;
}) {
  const range = high - low || 1;
  const pct = ((price - low) / range) * 100;
  const medianPct = ((median - low) / range) * 100;

  return (
    <div className="price-bar-container">
      <div className="price-bar">
        <div className="price-bar-fill" style={{ width: `${Math.min(100, pct)}%` }} />
        <div className="median-marker" style={{ left: `${medianPct}%` }} title={`Median: $${median}`} />
      </div>
    </div>
  );
}

function CompetitorRow({
  comp,
  stats,
  yourPrice,
}: {
  readonly comp: CompetitorPrice;
  readonly stats: DishComparisonResponse['stats'];
  readonly yourPrice: number | null;
}) {
  const vsMedian = comp.price - stats.median;
  const vsLabel =
    Math.abs(vsMedian) < 0.50
      ? 'at market'
      : vsMedian > 0
        ? `+$${vsMedian.toFixed(2)} above`
        : `-$${Math.abs(vsMedian).toFixed(2)} below`;
  const vsClass =
    Math.abs(vsMedian) < 0.50 ? 'vs-at' : vsMedian > 0 ? 'vs-above' : 'vs-below';

  return (
    <div className="competitor-row">
      <div className="comp-info">
        <div className="comp-name-row">
          <span className="comp-name">{comp.restaurant_name}</span>
          <PriceTierBadge tier={comp.price_tier} />
        </div>
        <div className="comp-meta">
          <StarRating rating={comp.rating} />
          <span className="comp-reviews">({comp.review_count.toLocaleString()})</span>
          <span className="comp-distance">{comp.distance_miles} mi</span>
        </div>
        <span className="comp-address">{comp.address}</span>
      </div>
      <div className="comp-pricing">
        <span className="comp-price">${comp.price.toFixed(2)}</span>
        <span className={`comp-vs ${vsClass}`}>{vsLabel}</span>
        <PriceBar
          price={comp.price}
          low={stats.low}
          high={stats.high}
          median={stats.median}
          yourPrice={yourPrice}
        />
      </div>
    </div>
  );
}

export default function ComparisonResults({ result }: ComparisonResultsProps) {
  const { dish_name, stats, competitors, your_price, your_percentile, radius_miles, location_label } = result;

  if (competitors.length === 0) {
    return (
      <div className="no-results">
        <h3>No results found for "{dish_name}"</h3>
        <p>Try a different dish name or increase the search radius.</p>
        <p className="available-dishes">
          Available dishes: Butter Chicken, Chicken Tikka Masala, Palak Paneer,
          Lamb Rogan Josh, Naan, Garlic Naan, Chicken Biryani, Samosa,
          Dal Makhani, Chana Masala, Gulab Jamun, Tandoori Chicken, Mango Lassi
        </p>
      </div>
    );
  }

  return (
    <div className="comparison-results">
      {/* Stats summary */}
      <div className="stats-banner">
        <div className="stats-title">
          <h2>{dish_name}</h2>
          <span className="stats-subtitle">
            {stats.count} restaurants within {radius_miles} mi · {location_label}
          </span>
        </div>
        <div className="stats-grid">
          <div className="stat-card">
            <span className="stat-value">${stats.median.toFixed(2)}</span>
            <span className="stat-label">Median</span>
          </div>
          <div className="stat-card">
            <span className="stat-value">${stats.low.toFixed(2)}</span>
            <span className="stat-label">Lowest</span>
          </div>
          <div className="stat-card">
            <span className="stat-value">${stats.high.toFixed(2)}</span>
            <span className="stat-label">Highest</span>
          </div>
          <div className="stat-card">
            <span className="stat-value">
              ${(stats.high - stats.low).toFixed(2)}
            </span>
            <span className="stat-label">Range</span>
          </div>
        </div>
      </div>

      {/* Your benchmarking */}
      {your_price != null && your_percentile != null && (
        <div className="your-benchmark">
          <div className="benchmark-header">
            <h3>Your Price: ${your_price.toFixed(2)}</h3>
            <span className="percentile-badge">
              {your_percentile < 30
                ? '📉 Below most competitors'
                : your_percentile > 70
                  ? '📈 Above most competitors'
                  : '✅ Competitive range'}
            </span>
          </div>
          <p className="benchmark-detail">
            Your price is higher than {your_percentile.toFixed(0)}% of competitors.
            {your_price < stats.median
              ? ` You're $${(stats.median - your_price).toFixed(2)} below the median — there may be room to increase.`
              : your_price > stats.median
                ? ` You're $${(your_price - stats.median).toFixed(2)} above the median.`
                : ' You\'re right at the median.'}
          </p>
        </div>
      )}

      {/* Competitor list */}
      <div className="competitors-list">
        <h3>Competitor Pricing</h3>
        {competitors.map((comp, idx) => (
          <CompetitorRow
            key={idx}
            comp={comp}
            stats={stats}
            yourPrice={your_price}
          />
        ))}
      </div>
    </div>
  );
}
