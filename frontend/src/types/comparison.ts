export interface CompetitorPrice {
  readonly restaurant_name: string;
  readonly address: string;
  readonly price: number;
  readonly price_tier: string;
  readonly rating: number;
  readonly review_count: number;
  readonly section_name: string;
  readonly distance_miles: number;
}

export interface PriceStats {
  readonly median: number;
  readonly mean: number;
  readonly low: number;
  readonly high: number;
  readonly count: number;
  readonly p25: number;
  readonly p75: number;
}

export interface DishComparisonResponse {
  readonly dish_name: string;
  readonly category: string;
  readonly location_label: string;
  readonly radius_miles: number;
  readonly stats: PriceStats;
  readonly competitors: readonly CompetitorPrice[];
  readonly your_price: number | null;
  readonly your_percentile: number | null;
}
