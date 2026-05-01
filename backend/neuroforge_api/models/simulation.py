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
