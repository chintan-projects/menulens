import type { DishComparisonResponse } from '../types/comparison';

export async function fetchDishes(): Promise<string[]> {
  const res = await fetch('/api/demo/dishes');
  if (!res.ok) throw new Error('Failed to load dishes');
  return res.json() as Promise<string[]>;
}

export async function compareDish(
  dish: string,
  yourPrice?: number,
  radius: number = 15,
): Promise<DishComparisonResponse> {
  const params = new URLSearchParams({
    dish,
    radius: String(radius),
    // Default to SF center
    lat: '37.7749',
    lng: '-122.4194',
  });
  if (yourPrice !== undefined && yourPrice > 0) {
    params.set('your_price', String(yourPrice));
  }

  const res = await fetch(`/api/demo/compare?${params}`);
  if (!res.ok) throw new Error('Comparison failed');
  return res.json() as Promise<DishComparisonResponse>;
}
