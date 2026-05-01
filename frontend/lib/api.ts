import type {
  HebbianRequest,
  HebbianResponse,
  HHRequest,
  HHResponse,
  HopfieldRequest,
  HopfieldResponse,
  NeuronResponse,
  NeuronSearchResponse,
  STDPRequest,
  STDPResponse,
  V1Request,
  V1Response,
} from './types';

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

export async function simulateSTDP(request: STDPRequest = {}): Promise<STDPResponse> {
  const response = await fetch(`${API_BASE}/api/simulate/stdp`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`simulateSTDP: ${response.status} ${text.slice(0, 200)}`);
  }
  return (await response.json()) as STDPResponse;
}

export async function simulateV1(request: V1Request = {}): Promise<V1Response> {
  const response = await fetch(`${API_BASE}/api/simulate/v1`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`simulateV1: ${response.status} ${text.slice(0, 200)}`);
  }
  return (await response.json()) as V1Response;
}

export async function fetchV1NeuronSample(size = 5): Promise<NeuronSearchResponse> {
  const response = await fetch(`${API_BASE}/api/neurons/v1/sample?size=${size}`);
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`fetchV1NeuronSample: ${response.status} ${text.slice(0, 200)}`);
  }
  return (await response.json()) as NeuronSearchResponse;
}

export async function fetchHippocampalSample(size = 5): Promise<NeuronSearchResponse> {
  const response = await fetch(`${API_BASE}/api/neurons/hippocampus/sample?size=${size}`);
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`fetchHippocampalSample: ${response.status} ${text.slice(0, 200)}`);
  }
  return (await response.json()) as NeuronSearchResponse;
}

export async function simulateHebbian(request: HebbianRequest = {}): Promise<HebbianResponse> {
  const response = await fetch(`${API_BASE}/api/simulate/hebbian`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`simulateHebbian: ${response.status} ${text.slice(0, 200)}`);
  }
  return (await response.json()) as HebbianResponse;
}

export async function simulateHopfield(request: HopfieldRequest = {}): Promise<HopfieldResponse> {
  const response = await fetch(`${API_BASE}/api/simulate/hopfield`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`simulateHopfield: ${response.status} ${text.slice(0, 200)}`);
  }
  return (await response.json()) as HopfieldResponse;
}

export async function fetchCA3Sample(size = 5): Promise<NeuronSearchResponse> {
  const response = await fetch(`${API_BASE}/api/neurons/ca3/sample?size=${size}`);
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`fetchCA3Sample: ${response.status} ${text.slice(0, 200)}`);
  }
  return (await response.json()) as NeuronSearchResponse;
}
