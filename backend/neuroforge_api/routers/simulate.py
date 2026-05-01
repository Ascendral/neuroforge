"""POST /api/simulate/hh — run a Hodgkin-Huxley step-current simulation."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from neuroforge_api.models.simulation import (
    HHRequest,
    HHResponse,
    STDPRequest,
    STDPResponse,
)
from neuroforge_api.simulators.hodgkin_huxley import simulate_hh
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
