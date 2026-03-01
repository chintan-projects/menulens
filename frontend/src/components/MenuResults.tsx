import type { ExtractionResponse } from '../types/menu';

interface MenuResultsProps {
  readonly result: ExtractionResponse;
  readonly elapsed: number;
}

function ConfidenceBadge({ score }: { readonly score: number }) {
  const pct = Math.round(score * 100);
  const level = pct >= 90 ? 'high' : pct >= 70 ? 'medium' : 'low';
  return <span className={`badge confidence-${level}`}>{pct}%</span>;
}

function DietaryTag({ tag }: { readonly tag: string }) {
  const colorMap: Record<string, string> = {
    vegetarian: '#22c55e',
    vegan: '#16a34a',
    'gluten-free': '#eab308',
    halal: '#3b82f6',
    spicy: '#ef4444',
  };
  const color = colorMap[tag.toLowerCase()] ?? '#6b7280';
  return (
    <span className="dietary-tag" style={{ borderColor: color, color }}>
      {tag}
    </span>
  );
}

export default function MenuResults({ result, elapsed }: MenuResultsProps) {
  const { menu, confidence, total_items, total_sections } = result;

  return (
    <div className="results">
      <div className="results-header">
        <div>
          <h2>{menu.restaurant_name}</h2>
          <p className="results-meta">
            {total_sections} sections · {total_items} items · {elapsed.toFixed(1)}s
          </p>
        </div>
        <div className="confidence-display">
          <span className="confidence-label">Confidence</span>
          <ConfidenceBadge score={confidence} />
        </div>
      </div>

      {menu.menu_sections.map((section, si) => (
        <div key={si} className="menu-section">
          <h3 className="section-name">{section.section_name}</h3>
          <div className="items-grid">
            {section.items.map((item, ii) => (
              <div key={ii} className="menu-item-card">
                <div className="item-header">
                  <span className="item-name">{item.dish_name}</span>
                  <span className="item-price">
                    ${item.price.toFixed(2)}
                  </span>
                </div>
                {item.description && (
                  <p className="item-description">{item.description}</p>
                )}
                {item.dietary_tags.length > 0 && (
                  <div className="item-tags">
                    {item.dietary_tags.map((tag) => (
                      <DietaryTag key={tag} tag={tag} />
                    ))}
                  </div>
                )}
                {item.price_variants.length > 0 && (
                  <div className="item-variants">
                    {item.price_variants.map((v) => (
                      <span key={v.label} className="variant">
                        {v.label}: ${v.price.toFixed(2)}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      ))}

      {menu.extraction_notes && (
        <p className="extraction-notes">
          <strong>Notes:</strong> {menu.extraction_notes}
        </p>
      )}
    </div>
  );
}
