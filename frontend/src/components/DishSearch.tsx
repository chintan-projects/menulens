import { useEffect, useState } from 'react';
import { fetchDishes } from '../api/compare';

interface DishSearchProps {
  readonly onSearch: (dish: string, yourPrice: number | undefined, radius: number) => void;
  readonly isLoading: boolean;
}

export default function DishSearch({ onSearch, isLoading }: DishSearchProps) {
  const [dish, setDish] = useState('');
  const [yourPrice, setYourPrice] = useState('');
  const [radius, setRadius] = useState(15);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [allDishes, setAllDishes] = useState<string[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);

  useEffect(() => {
    fetchDishes().then(setAllDishes).catch(() => {});
  }, []);

  useEffect(() => {
    if (dish.length >= 2) {
      const lower = dish.toLowerCase();
      const matches = allDishes.filter((d) =>
        d.toLowerCase().includes(lower)
      );
      setSuggestions(matches);
      setShowSuggestions(matches.length > 0);
    } else {
      setShowSuggestions(false);
    }
  }, [dish, allDishes]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (dish.trim()) {
      setShowSuggestions(false);
      const price = yourPrice ? parseFloat(yourPrice) : undefined;
      onSearch(dish.trim(), price, radius);
    }
  };

  const selectSuggestion = (name: string) => {
    setDish(name);
    setShowSuggestions(false);
  };

  return (
    <form onSubmit={handleSubmit} className="dish-search">
      <div className="search-row">
        <div className="field dish-field">
          <label htmlFor="dish-name">What dish do you want to price?</label>
          <div className="autocomplete-wrapper">
            <input
              id="dish-name"
              type="text"
              placeholder="e.g. Butter Chicken, Palak Paneer, Naan..."
              value={dish}
              onChange={(e) => setDish(e.target.value)}
              onFocus={() => dish.length >= 2 && setSuggestions(
                allDishes.filter(d => d.toLowerCase().includes(dish.toLowerCase()))
              )}
              autoComplete="off"
            />
            {showSuggestions && (
              <ul className="suggestions">
                {suggestions.map((s) => (
                  <li key={s}>
                    <button type="button" onClick={() => selectSuggestion(s)}>
                      {s}
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>

        <div className="field price-field">
          <label htmlFor="your-price">Your price (optional)</label>
          <div className="price-input-wrapper">
            <span className="dollar-sign">$</span>
            <input
              id="your-price"
              type="number"
              step="0.01"
              min="0"
              placeholder="17.99"
              value={yourPrice}
              onChange={(e) => setYourPrice(e.target.value)}
            />
          </div>
        </div>
      </div>

      <div className="search-row-bottom">
        <div className="radius-selector">
          <label>Radius</label>
          <div className="radius-chips">
            {[5, 10, 15, 25].map((r) => (
              <button
                key={r}
                type="button"
                className={`radius-chip ${radius === r ? 'active' : ''}`}
                onClick={() => setRadius(r)}
              >
                {r} mi
              </button>
            ))}
          </div>
        </div>

        <button
          type="submit"
          className="btn-primary search-btn"
          disabled={isLoading || !dish.trim()}
        >
          {isLoading ? (
            <>
              <span className="spinner" />
              Searching...
            </>
          ) : (
            'Search Competitors →'
          )}
        </button>
      </div>
    </form>
  );
}
