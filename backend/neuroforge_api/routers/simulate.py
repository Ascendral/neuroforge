"""POST /api/simulate/hh — run a Hodgkin-Huxley step-current simulation."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from neuroforge_api.models.simulation import (
    HebbianRequest,
    HebbianResponse,
    HHRequest,
    HHResponse,
    STDPRequest,
    STDPResponse,
    V1Request,
    V1Response,
)
from neuroforge_api.simulators.hebbian import simulate_hebbian
from neuroforge_api.simulators.hodgkin_huxley import simulate_hh
from neuroforge_api.simulators.hubel_wiesel import (
    gabor_filter,
    orientation_tuning_curve,
)
from neuroforge_api.simulators.stdp import (
    A_MINUS,
    A_PLUS,
    TAU_MINUS_MS,
    TAU_PLUS_MS,
    simulate_stdp_pair,
    stdp_curve,
)

router = APIRouter(prefix="/api/simulate", tags=["simulate"])

HH_CITATION = (
    "Hodgkin AL, Huxley AF. A quantitative description of membrane current and "
    "its application to conduction and excitation in nerve. "
    "J Physiol. 1952;117(4):500-44. doi:10.1113/jphysiol.1952.sp004764"
)

STDP_CITATION = (
    "Bi GQ, Poo MM. Synaptic modifications in cultured hippocampal neurons: "
    "dependence on spike timing, synaptic strength, and postsynaptic cell type. "
    "J Neurosci. 1998;18(24):10464-72. doi:10.1523/JNEUROSCI.18-24-10464.1998"
)

V1_CITATION = (
    "Hubel DH, Wiesel TN. Receptive fields, binocular interaction and "
    "functional architecture in the cat's visual cortex. J Physiol. "
    "1962;160(1):106-54. doi:10.1113/jphysiol.1962.sp006837"
)

HEBBIAN_CITATION = (
    "Hebb DO. The Organization of Behavior. Wiley, 1949. "
    "Bliss TVP, Lømo T. Long-lasting potentiation of synaptic transmission "
    "in the dentate area of the anaesthetized rabbit following stimulation "
    "of the perforant path. J Physiol. 1973;232(2):331-356. "
    "doi:10.1113/jphysiol.1973.sp010273. "
    "Oja E. A simplified neuron model as a principal component analyzer. "
    "J Math Biol. 1982;15(3):267-273. doi:10.1007/BF00275687"
)


@router.post("/hh", response_model=HHResponse)
def run_hh(request: HHRequest) -> HHResponse:
    try:
        trace = simulate_hh(
            duration_ms=request.duration_ms,
            stimulus_uA=request.stimulus_uA,
            stimulus_start_ms=request.stimulus_start_ms,
            stimulus_end_ms=request.stimulus_end_ms,
            dt_ms=request.dt_ms,
            record_every_n=request.record_every_n,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return HHResponse(
        times_ms=trace.times_ms.tolist(),
        voltage_mV=trace.voltage_mV.tolist(),
        stimulus_uA=trace.stimulus_uA.tolist(),
        spike_times_ms=trace.spike_times_ms.tolist(),
        dt_ms=trace.dt_ms,
        citation=HH_CITATION,
    )


@router.post("/stdp", response_model=STDPResponse)
def run_stdp(request: STDPRequest) -> STDPResponse:
    if request.dt_max_ms <= request.dt_min_ms:
        raise HTTPException(status_code=422, detail="dt_max_ms must be > dt_min_ms")
    try:
        result = simulate_stdp_pair(request.dt_ms)
        grid, values = stdp_curve(
            dt_min_ms=request.dt_min_ms,
            dt_max_ms=request.dt_max_ms,
            points=request.curve_points,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return STDPResponse(
        dt_ms=result.dt_ms,
        observed_delta_w=result.delta_w,
        kernel_delta_w=result.kernel_dw,
        pre_spike_ms=result.pre_spike_ms,
        post_spike_ms=result.post_spike_ms,
        curve_dt_ms=grid.tolist(),
        curve_delta_w=values.tolist(),
        tau_plus_ms=TAU_PLUS_MS,
        tau_minus_ms=TAU_MINUS_MS,
        a_plus=A_PLUS,
        a_minus=A_MINUS,
        citation=STDP_CITATION,
    )


@router.post("/hebbian", response_model=HebbianResponse)
def run_hebbian(request: HebbianRequest) -> HebbianResponse:
    record_every_n = max(1, request.n_iterations // 200)
    try:
        hebb = simulate_hebbian(
            rule="hebb",
            n_iterations=request.n_iterations,
            learning_rate=request.learning_rate,
            correlation=request.correlation,
            input_dim=request.input_dim,
            seed=request.seed,
            record_every_n=record_every_n,
        )
        oja = simulate_hebbian(
            rule="oja",
            n_iterations=request.n_iterations,
            learning_rate=request.learning_rate,
            correlation=request.correlation,
            input_dim=request.input_dim,
            seed=request.seed,
            record_every_n=record_every_n,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return HebbianResponse(
        iterations=hebb.iterations.tolist(),
        hebb_norm=hebb.weight_norm.tolist(),
        hebb_angle_deg=hebb.weight_angle_deg.tolist(),
        oja_norm=oja.weight_norm.tolist(),
        oja_angle_deg=oja.weight_angle_deg.tolist(),
        principal_direction=hebb.principal_direction.tolist(),
        final_hebb_weight=hebb.final_weight.tolist(),
        final_oja_weight=oja.final_weight.tolist(),
        citation=HEBBIAN_CITATION,
    )


@router.post("/v1", response_model=V1Response)
def run_v1(request: V1Request) -> V1Response:
    sigma_px = request.sigma_px if request.sigma_px is not None else 1.0 / request.spatial_frequency_cyc_per_px
    try:
        even = gabor_filter(
            image_size=request.image_size,
            orientation_deg=request.preferred_orientation_deg,
            spatial_frequency_cyc_per_px=request.spatial_frequency_cyc_per_px,
            phase_deg=0.0,
            sigma_px=sigma_px,
        )
        odd = gabor_filter(
            image_size=request.image_size,
            orientation_deg=request.preferred_orientation_deg,
            spatial_frequency_cyc_per_px=request.spatial_frequency_cyc_per_px,
            phase_deg=90.0,
            sigma_px=sigma_px,
        )
        tc = orientation_tuning_curve(
            preferred_orientation_deg=request.preferred_orientation_deg,
            spatial_frequency_cyc_per_px=request.spatial_frequency_cyc_per_px,
            image_size=request.image_size,
            n_orientations=request.n_orientations,
            sigma_px=sigma_px,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return V1Response(
        preferred_orientation_deg=request.preferred_orientation_deg,
        spatial_frequency_cyc_per_px=request.spatial_frequency_cyc_per_px,
        image_size=request.image_size,
        sigma_px=float(sigma_px),
        gabor_even=even.tolist(),
        gabor_odd=odd.tolist(),
        tuning_orientations_deg=tc.orientations_deg.tolist(),
        tuning_simple=tc.simple_responses.tolist(),
        tuning_complex=tc.complex_responses.tolist(),
        citation=V1_CITATION,
    )
