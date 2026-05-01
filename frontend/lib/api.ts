import type { HHRequest, HHResponse, NeuronResponse } from './types';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? 'http://localhost:8000';

export async function fetchNeuron(id: number): Promise<NeuronResponse> {
  const response = await fetch(`${API_BASE}/api/neurons/${id}`);
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`fetchNeuron(${id}): ${response.status} ${text.slice(0, 200)}`);
  }
  return (await response.json()) as NeuronResponse;
}

export async function simulateHH(request: HHRequest = {}): Promise<HHResponse> {
  const response = await fetch(`${API_BASE}/api/simulate/hh`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`simulateHH: ${response.status} ${text.slice(0, 200)}`);
  }
  return (await response.json()) as HHResponse;
}
