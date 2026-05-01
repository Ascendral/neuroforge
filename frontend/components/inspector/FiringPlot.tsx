'use client';

import { useMemo } from 'react';

import type { HHResponse } from '@/lib/types';

// Anti-theater: this component renders ONLY data from a real HHResponse
// produced by the backend Brian2 simulator. The empty state is honest about
// having no data — no synthetic curve is ever drawn.

interface FiringPlotProps {
  trace: HHResponse | null;
  selectedPointId: number | null;
}

const PLOT_W = 320;
const PLOT_H = 140;
const PAD_L = 36;
const PAD_R = 8;
const PAD_T = 10;
const PAD_B = 22;

const V_MIN = -90; // mV — below canonical AHP trough
const V_MAX = 60; // mV — above canonical AP peak

function buildPath(times: number[], voltages: number[], duration: number): string {
  const innerW = PLOT_W - PAD_L - PAD_R;
  const innerH = PLOT_H - PAD_T - PAD_B;
  let d = '';
  for (let i = 0; i < times.length; i++) {
    const x = PAD_L + (times[i] / duration) * innerW;
    const y = PAD_T + ((V_MAX - voltages[i]) / (V_MAX - V_MIN)) * innerH;
    d += (i === 0 ? 'M' : 'L') + x.toFixed(2) + ' ' + y.toFixed(2) + ' ';
  }
  return d.trim();
}

function buildStimulusPath(times: number[], stim: number[], duration: number): string {
  const innerW = PLOT_W - PAD_L - PAD_R;
  const innerH = PLOT_H - PAD_T - PAD_B;
  // Place stimulus indicator on the bottom 12px strip
  const bottom = PAD_T + innerH - 2;
  const stripH = 8;
  const peakAbs = Math.max(1e-9, ...stim.map((s) => Math.abs(s)));
  let d = '';
  for (let i = 0; i < times.length; i++) {
    const x = PAD_L + (times[i] / duration) * innerW;
    const norm = stim[i] / peakAbs;
    const y = bottom - norm * stripH;
    d += (i === 0 ? 'M' : 'L') + x.toFixed(2) + ' ' + y.toFixed(2) + ' ';
  }
  return d.trim();
}

export function FiringPlot({ trace, selectedPointId }: FiringPlotProps) {
  const innerW = PLOT_W - PAD_L - PAD_R;
  const innerH = PLOT_H - PAD_T - PAD_B;

  const computed = useMemo(() => {
    if (!trace || trace.times_ms.length === 0) return null;
    const duration = trace.times_ms[trace.times_ms.length - 1] || 1;
    return {
      duration,
      vPath: buildPath(trace.times_ms, trace.voltage_mV, duration),
      iPath: buildStimulusPath(trace.times_ms, trace.stimulus_uA, duration),
      spikeXs: trace.spike_times_ms.map((t) => PAD_L + (t / duration) * innerW),
      vMaxObserved: Math.max(...trace.voltage_mV),
      vMinObserved: Math.min(...trace.voltage_mV),
    };
  }, [trace, innerW]);

  // Y-axis grid: -90, -65 (rest), 0 (threshold), +50 (overshoot reference)
  const ticks = [-90, -65, 0, 50];

  return (
    <section aria-label="Firing plot" className="space-y-2">
      <div className="flex items-baseline justify-between">
        <h3 className="text-xs uppercase tracking-widest text-white/40">Membrane potential</h3>
        <span className="font-mono text-[10px] text-white/30">
          {selectedPointId === null ? 'no point selected' : `point ${selectedPointId}`}
        </span>
      </div>
      <svg
        width={PLOT_W}
        height={PLOT_H}
        viewBox={`0 0 ${PLOT_W} ${PLOT_H}`}
        className="rounded border border-white/10 bg-black"
      >
        {/* Y axis */}
        <line x1={PAD_L} x2={PAD_L} y1={PAD_T} y2={PAD_T + innerH} stroke="rgba(255,255,255,0.3)" />
        {/* X axis */}
        <line x1={PAD_L} x2={PAD_L + innerW} y1={PAD_T + innerH} y2={PAD_T + innerH} stroke="rgba(255,255,255,0.3)" />
        {/* Grid + ticks */}
        {ticks.map((mv) => {
          const y = PAD_T + ((V_MAX - mv) / (V_MAX - V_MIN)) * innerH;
          return (
            <g key={mv}>
              <line
                x1={PAD_L}
                x2={PAD_L + innerW}
                y1={y}
                y2={y}
                stroke="rgba(255,255,255,0.07)"
                strokeDasharray="2 3"
              />
              <text x={PAD_L - 4} y={y + 3} fontSize={9} textAnchor="end" fill="rgba(255,255,255,0.5)" fontFamily="monospace">
                {mv}
              </text>
            </g>
          );
        })}

        {/* Axis labels */}
        <text x={4} y={PAD_T + 8} fontSize={9} fill="rgba(255,255,255,0.5)" fontFamily="monospace">mV</text>
        <text x={PLOT_W - 14} y={PAD_T + innerH + 14} fontSize={9} fill="rgba(255,255,255,0.5)" fontFamily="monospace">ms</text>

        {!computed && (
          <text
            x={PAD_L + innerW / 2}
            y={PAD_T + innerH / 2 + 4}
            fontSize={10}
            textAnchor="middle"
            fill="rgba(255,255,255,0.35)"
            fontFamily="monospace"
          >
            no simulation yet — click run hh
          </text>
        )}

        {computed && (
          <>
            {/* Spike markers */}
            {computed.spikeXs.map((x, i) => (
              <line
                key={i}
                x1={x}
                x2={x}
                y1={PAD_T}
                y2={PAD_T + innerH}
                stroke="rgba(255,45,45,0.4)"
                strokeWidth={1}
              />
            ))}
            {/* Stimulus current indicator (bottom strip) */}
            <path d={computed.iPath} fill="none" stroke="rgba(155,210,255,0.7)" strokeWidth={1} />
            {/* Membrane potential trace */}
            <path d={computed.vPath} fill="none" stroke="#ffffff" strokeWidth={1.2} />
          </>
        )}
      </svg>
    </section>
  );
}
