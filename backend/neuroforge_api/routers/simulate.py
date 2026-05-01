"""POST /api/simulate/hh — run a Hodgkin-Huxley step-current simulation."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from neuroforge_api.models.simulation import HHRequest, HHResponse
from neuroforge_api.simulators.hodgkin_huxley import simulate_hh

router = APIRouter(prefix="/api/simulate", tags=["simulate"])

HH_CITATION = (
    "Hodgkin AL, Huxley AF. A quantitative description of membrane current and "
    "its application to conduction and excitation in nerve. "
    "J Physiol. 1952;117(4):500-44. doi:10.1113/jphysiol.1952.sp004764"
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
