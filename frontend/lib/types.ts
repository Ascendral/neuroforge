// Mirror of backend NeuronResponse / NeuronPoint pydantic models.
// Source of truth lives in backend/neuroforge_api/models/neuron.py.

export interface NeuronPoint {
  id: number;
  type: number; // 1=soma, 2=axon, 3=basal dendrite, 4=apical dendrite, 0/7+=other
  x: number;
  y: number;
  z: number;
  radius: number;
  parent_id: number; // -1 for root
}

export interface NeuronResponse {
  neuron_id: number;
  neuron_name: string;
  archive: string;
  species: string;
  scientific_name: string;
  brain_region: string[];
  cell_type: string[];
  reference_pmid: string[];
  reference_doi: string[];
  png_url: string | null;
  points: NeuronPoint[];
  point_count: number;
  source_url: string;
  swc_url: string;
}

export const SWC_TYPE_LABELS: Record<number, string> = {
  0: 'undefined',
  1: 'soma',
  2: 'axon',
  3: 'basal dendrite',
  4: 'apical dendrite',
  5: 'fork point',
  6: 'end point',
};

export function swcTypeLabel(type: number): string {
  return SWC_TYPE_LABELS[type] ?? `custom (${type})`;
}
