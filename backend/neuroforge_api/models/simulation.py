"""Pydantic models for the /api/simulate endpoints."""

from __future__ import annotations

from pydantic import BaseModel, Field


class HHRequest(BaseModel):
    """Hodgkin-Huxley step-current simulation request."""

    duration_ms: float = Field(default=80.0, gt=0, le=2000)
    stimulus_uA: float = Field(default=10.0, ge=-50, le=50)
    stimulus_start_ms: float = Field(default=10.0, ge=0)
    stimulus_end_ms: float | None = Field(default=70.0, ge=0)
    dt_ms: float = Field(default=0.01, gt=0, le=1.0)
    record_every_n: int = Field(default=4, ge=1, le=100)


class HHResponse(BaseModel):
    """HH simulation result.

    All arrays are aligned: times_ms[i] is the sample time, voltage_mV[i] the
    membrane potential, stimulus_uA[i] the applied current at that instant.
    """

    times_ms: list[float]
    voltage_mV: list[float]
    stimulus_uA: list[float]
    spike_times_ms: list[float]
    dt_ms: float
    citation: str


class STDPRequest(BaseModel):
    """Spike-timing-dependent plasticity pair-pulse request."""

    dt_ms: float = Field(default=10.0, ge=-200.0, le=200.0)
    dt_min_ms: float = Field(default=-80.0, ge=-200.0, lt=0.0)
    dt_max_ms: float = Field(default=80.0, gt=0.0, le=200.0)
    curve_points: int = Field(default=161, ge=11, le=801)


class STDPResponse(BaseModel):
    dt_ms: float
    observed_delta_w: float
    kernel_delta_w: float
    pre_spike_ms: float
    post_spike_ms: float
    curve_dt_ms: list[float]
    curve_delta_w: list[float]
    tau_plus_ms: float
    tau_minus_ms: float
    a_plus: float
    a_minus: float
    citation: str


class V1Request(BaseModel):
    """Hubel-Wiesel V1 receptive-field tuning request."""

    preferred_orientation_deg: float = Field(default=45.0, ge=0.0, lt=180.0)
    spatial_frequency_cyc_per_px: float = Field(default=0.1, gt=0.0, le=0.5)
    image_size: int = Field(default=65, ge=15, le=129)
    n_orientations: int = Field(default=36, ge=8, le=180)
    sigma_px: float | None = Field(default=None, gt=0.0)


class V1Response(BaseModel):
    preferred_orientation_deg: float
    spatial_frequency_cyc_per_px: float
    image_size: int
    sigma_px: float
    gabor_even: list[list[float]]
    gabor_odd: list[list[float]]
    tuning_orientations_deg: list[float]
    tuning_simple: list[float]
    tuning_complex: list[float]
    citation: str


class HebbianRequest(BaseModel):
    n_iterations: int = Field(default=2000, ge=10, le=20000)
    learning_rate: float = Field(default=0.005, gt=0.0, le=0.1)
    correlation: float = Field(default=0.8, gt=-0.999, lt=0.999)
    input_dim: int = Field(default=2, ge=2, le=16)
    seed: int = Field(default=42, ge=0)


class HebbianResponse(BaseModel):
    iterations: list[int]
    hebb_norm: list[float]
    hebb_angle_deg: list[float]
    oja_norm: list[float]
    oja_angle_deg: list[float]
    principal_direction: list[float]
    final_hebb_weight: list[float]
    final_oja_weight: list[float]
    citation: str


class HopfieldRequest(BaseModel):
    n_neurons: int = Field(default=64, ge=16, le=400)
    n_patterns: int = Field(default=5, ge=1, le=80)
    corruption_fraction: float = Field(default=0.2, ge=0.0, le=1.0)
    target_index: int | None = Field(default=0, ge=0)
    max_sweeps: int = Field(default=6, ge=1, le=30)
    seed: int = Field(default=42, ge=0)


class HopfieldResponse(BaseModel):
    n_neurons: int
    n_patterns: int
    target_index: int
    target_capacity_alpha: float
    critical_capacity: float
    target_pattern: list[int]
    corrupted_input: list[int]
    final_state: list[int]
    energies: list[float]
    overlaps_with_target: list[float]
    final_overlap: float
    converged: bool
    citation: str


class ModernHopfieldRequest(BaseModel):
    d: int = Field(default=64, ge=16, le=256)
    n_patterns: int = Field(default=64, ge=1, le=1024)
    corruption_fraction: float = Field(default=0.2, ge=0.0, le=1.0)
    beta: float | None = Field(default=None, gt=0.0, le=50.0)
    n_updates: int = Field(default=3, ge=1, le=20)
    target_index: int = Field(default=0, ge=0)
    seed: int = Field(default=42, ge=0)
    sweep: bool = Field(default=True, description="also run the classic-vs-modern capacity sweep")
    sweep_trials: int = Field(default=6, ge=1, le=30)


class CapacitySweepResponse(BaseModel):
    d: int
    alphas: list[float]
    n_patterns: list[int]
    classic_success: list[float]
    modern_success: list[float]
    n_trials: int
    threshold: float
    corruption_fraction: float
    beta: float


class ModernHopfieldResponse(BaseModel):
    d: int
    n_patterns: int
    alpha: float
    beta: float
    classic_critical_alpha: float
    target_index: int
    target: list[float]
    corrupted: list[float]
    modern_final: list[float]
    modern_final_sign: list[int]
    modern_energies: list[float]
    modern_overlaps: list[float]
    modern_attention_weights: list[float]
    classic_final: list[int]
    classic_overlap: float
    attention_max_abs_diff: float
    sweep: CapacitySweepResponse | None
    citation: str


class DopamineRPERequest(BaseModel):
    n_steps: int = Field(default=30, ge=6, le=200)
    bin_ms: float = Field(default=100.0, gt=0, le=1000)
    cue_step: int = Field(default=5, ge=0)
    reward_step: int = Field(default=20, ge=1)
    reward: float = Field(default=1.0, gt=0, le=10)
    alpha: float = Field(default=0.1, gt=0, le=1.0)
    gamma: float = Field(default=0.98, gt=0, le=1.0)
    n_training_trials: int = Field(default=200, ge=1, le=2000)


class DopamineRPEResponse(BaseModel):
    n_steps: int
    bin_ms: float
    cue_step: int
    reward_step: int
    alpha: float
    gamma: float
    n_training_trials: int
    times_ms: list[float]
    delta_unpredicted: list[float]
    delta_predicted: list[float]
    delta_omitted: list[float]
    value_trained: list[float]
    delta_at_reward_per_trial: list[float]
    delta_at_cue_per_trial: list[float]
    parameter_note: str
    citation: str


class SynapseRequest(BaseModel):
    holding_mV: float = Field(default=-65.0, ge=-120.0, le=60.0)
    g_max_nS: float = Field(default=1.0, ge=0.0, le=100.0)
    mg_mM: float = Field(default=1.0, ge=0.0, le=10.0)
    duration_ms: float = Field(default=200.0, gt=0, le=2000)
    dt_ms: float = Field(default=0.1, gt=0, le=5.0)
    onset_ms: float = Field(default=5.0, ge=0)


class ReceptorKineticsModel(BaseModel):
    key: str
    name: str
    transmitter: str
    tau_rise_ms: float
    tau_decay_ms: float
    e_rev_mV: float
    mg_block: bool
    citation: str


class SynapseTraceModel(BaseModel):
    key: str
    conductance_nS: list[float]
    current_pA: list[float]
    block_fraction: float


class SynapseResponse(BaseModel):
    times_ms: list[float]
    holding_mV: float
    mg_mM: float
    g_max_nS: float
    receptors: list[ReceptorKineticsModel]
    traces: list[SynapseTraceModel]
    nmda_iv_voltage_mV: list[float]
    nmda_iv_with_mg_pA: list[float]
    nmda_iv_without_mg_pA: list[float]
    citation: str


class MCPGateResponse(BaseModel):
    name: str
    description: str
    n_inputs: int
    weights: list[float]
    threshold: float
    inputs_table: list[list[int]]
    expected: list[int]
    produced: list[int]
    passes: bool
    citation: str


class MCPXorSearchResponse(BaseModel):
    target: list[int]
    weight_range: list[int]
    threshold_range: list[int]
    step: float
    combinations_tried: int
    best_match_correct: int
    best_weights: list[float] | None
    best_threshold: float | None
    no_solution: bool
    citation: str
