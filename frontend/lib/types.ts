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

// Mirror of backend HHRequest / HHResponse pydantic models.
export interface HHRequest {
  duration_ms?: number;
  stimulus_uA?: number;
  stimulus_start_ms?: number;
  stimulus_end_ms?: number | null;
  dt_ms?: number;
  record_every_n?: number;
}

export interface HHResponse {
  times_ms: number[];
  voltage_mV: number[];
  stimulus_uA: number[];
  spike_times_ms: number[];
  dt_ms: number;
  citation: string;
}

export interface STDPRequest {
  dt_ms?: number;
  dt_min_ms?: number;
  dt_max_ms?: number;
  curve_points?: number;
}

export interface STDPResponse {
  dt_ms: number;
  observed_delta_w: number;
  kernel_delta_w: number;
  pre_spike_ms: number;
  post_spike_ms: number;
  curve_dt_ms: number[];
  curve_delta_w: number[];
  tau_plus_ms: number;
  tau_minus_ms: number;
  a_plus: number;
  a_minus: number;
  citation: string;
}

export interface V1Request {
  preferred_orientation_deg?: number;
  spatial_frequency_cyc_per_px?: number;
  image_size?: number;
  n_orientations?: number;
  sigma_px?: number;
}

export interface V1Response {
  preferred_orientation_deg: number;
  spatial_frequency_cyc_per_px: number;
  image_size: number;
  sigma_px: number;
  gabor_even: number[][];
  gabor_odd: number[][];
  tuning_orientations_deg: number[];
  tuning_simple: number[];
  tuning_complex: number[];
  citation: string;
}

export interface NeuronSummary {
  neuron_id: number;
  neuron_name: string;
  archive: string;
  species: string;
  scientific_name: string;
  brain_region: string[];
  cell_type: string[];
  reference_doi: string[];
  reference_pmid: string[];
  png_url: string | null;
  source_url: string;
  swc_url: string;
}

export interface NeuronSearchResponse {
  region_query: string[];
  total_matching: number;
  page: number;
  size: number;
  results: NeuronSummary[];
  citation_note: string;
}

export interface HebbianRequest {
  n_iterations?: number;
  learning_rate?: number;
  correlation?: number;
  input_dim?: number;
  seed?: number;
}

export interface HebbianResponse {
  iterations: number[];
  hebb_norm: number[];
  hebb_angle_deg: number[];
  oja_norm: number[];
  oja_angle_deg: number[];
  principal_direction: number[];
  final_hebb_weight: number[];
  final_oja_weight: number[];
  citation: string;
}

export interface HopfieldRequest {
  n_neurons?: number;
  n_patterns?: number;
  corruption_fraction?: number;
  target_index?: number;
  max_sweeps?: number;
  seed?: number;
}

export interface HopfieldResponse {
  n_neurons: number;
  n_patterns: number;
  target_index: number;
  target_capacity_alpha: number;
  critical_capacity: number;
  target_pattern: number[];
  corrupted_input: number[];
  final_state: number[];
  energies: number[];
  overlaps_with_target: number[];
  final_overlap: number;
  converged: boolean;
  citation: string;
}
