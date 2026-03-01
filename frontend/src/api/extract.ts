import type { ExtractionRequest, ExtractionResponse } from '../types/menu';

export async function extractMenu(
  request: ExtractionRequest
): Promise<ExtractionResponse> {
  const response = await fetch('/api/extract', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail ?? `Extraction failed (${response.status})`);
  }

  return response.json() as Promise<ExtractionResponse>;
}

export async function checkHealth(): Promise<boolean> {
  try {
    const response = await fetch('/health');
    return response.ok;
  } catch {
    return false;
  }
}
