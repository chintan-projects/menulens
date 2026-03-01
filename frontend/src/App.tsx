import { useEffect, useState } from 'react';
import { checkHealth } from './api/extract';
import { compareDish } from './api/compare';
import DishSearch from './components/DishSearch';
import ComparisonResults from './components/ComparisonResults';
import type { DishComparisonResponse } from './types/comparison';
import './App.css';

export default function App() {
  const [result, setResult] = useState<DishComparisonResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [apiStatus, setApiStatus] = useState<'checking' | 'online' | 'offline'>('checking');

  useEffect(() => {
    checkHealth().then((ok) => setApiStatus(ok ? 'online' : 'offline'));
  }, []);

  const handleSearch = async (dish: string, yourPrice: number | undefined, radius: number) => {
    setIsLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await compareDish(dish, yourPrice, radius);
      setResult(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Search failed');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-content">
          <h1>
            <span className="logo-icon">🔍</span> MenuLens
          </h1>
          <p className="tagline">Know what your competitors charge — before you set your price</p>
        </div>
        <div className="status-indicators">
          <span className={`status-dot ${apiStatus}`} />
          <span className="status-label">
            {apiStatus === 'checking' ? '...' : apiStatus}
          </span>
        </div>
      </header>

      <main className="app-main">
        <div className="hero">
          <h2>How should you price your menu?</h2>
          <p>
            Search any dish to see what restaurants in your neighborhood charge for it.
            Compare ratings, price tiers, and find your competitive sweet spot.
          </p>
        </div>

        <DishSearch onSearch={handleSearch} isLoading={isLoading} />

        {error && (
          <div className="error-banner">
            <strong>Error:</strong> {error}
          </div>
        )}

        {result && <ComparisonResults result={result} />}
      </main>

      <footer className="app-footer">
        <p>MenuLens v0.1 · Demo data: Indian restaurants, SF Bay Area</p>
      </footer>
    </div>
  );
}
