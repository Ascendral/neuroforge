'use client';

import { useMemo, useState } from 'react';

import { simulateSTDP } from '@/lib/api';
import type { STDPResponse } from '@/lib/types';

// Anti-theater: this panel renders ONLY the curve and observed point returned
// by the backend Brian2/kernel calculation. No synthetic curve is ever drawn
// before a real response arrives.

const PLOT_W = 320;
const PLOT_H = 160;
const PAD_L = 32;
const PAD_R = 8;
const PAD_T = 14;
const PAD_B = 22;

function buildPath(
  xs: number[],
  ys: number[],
  xMin: number,
  xMax: number,
  yMin: number,
  yMax: number,
): string {
  const innerW = PLOT_W - PAD_L - PAD_R;
  const innerH = PLOT_H - PAD_T - PAD_B;
  let d = '';
  for (let i = 0; i < xs.length; i++) {
    const x = PAD_L + ((xs[i] - xMin) / (xMax - xMin)) * innerW;
    const y = PAD_T + ((yMax - ys[i]) / (yMax - yMin)) * innerH;
    d += (i === 0 ? 'M' : 'L') + x.toFixed(2) + ' ' + y.toFixed(2) + ' ';
  }
  return d.trim();
}

export function STDPPanel() {
  const [dt, setDt] = useState(10);
  const [response, setResponse] = useState<STDPResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [running, setRunning] = useState(false);

  const onRun = async () => {
    setRunning(true);
    setError(null);
    try {
      setResponse(await simulateSTDP({ dt_ms: dt }));
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setRunning(false);
    }
  };

  const computed = useMemo(() => {
    if (!response) return null;
    const innerW = PLOT_W - PAD_L - PAD_R;
    const innerH = PLOT_H - PAD_T - PAD_B;
    const xMin = response.curve_dt_ms[0];
    const xMax = response.curve_dt_ms[response.curve_dt_ms.length - 1];
    const yPeak = Math.max(response.a_plus, response.a_minus) * 1.1;
    const yMin = -yPeak;
    const yMax = yPeak;
    const path = buildPath(response.curve_dt_ms, response.curve_delta_w, xMin, xMax, yMin, yMax);
    const px = PAD_L + ((response.dt_ms - xMin) / (xMax - xMin)) * innerW;
    const py = PAD_T + ((yMax - response.observed_delta_w) / (yMax - yMin)) * innerH;
    const zeroY = PAD_T + ((yMax - 0) / (yMax - yMin)) * innerH;
    return { path, px, py, xMin, xMax, yMin, yMax, zeroY };
  }, [response]);

  const innerW = PLOT_W - PAD_L - PAD_R;
  const innerH = PLOT_H - PAD_T - PAD_B;

  return (
    <section className="space-y-3">
      <div className="flex items-baseline justify-between">
        <h2 className="kicker">STDP — Bi & Poo 1998</h2>
        <span className="mono text-[11px] text-white/35">Δt = t_post − t_pre</span>
      </div>

      <svg width={PLOT_W} height={PLOT_H} viewBox={`0 0 ${PLOT_W} ${PLOT_H}`} className="plot">
        {/* Y axis */}
        <line x1={PAD_L} x2={PAD_L} y1={PAD_T} y2={PAD_T + innerH} stroke="rgba(255,255,255,0.3)" />
        {/* X axis (dynamic at zero) */}
        <line
          x1={PAD_L}
          x2={PAD_L + innerW}
          y1={computed ? computed.zeroY : PAD_T + innerH / 2}
          y2={computed ? computed.zeroY : PAD_T + innerH / 2}
          stroke="rgba(255,255,255,0.3)"
        />
        {/* Vertical zero-Δt line */}
        {computed && (
          <line
            x1={PAD_L + ((0 - computed.xMin) / (computed.xMax - computed.xMin)) * innerW}
            x2={PAD_L + ((0 - computed.xMin) / (computed.xMax - computed.xMin)) * innerW}
            y1={PAD_T}
            y2={PAD_T + innerH}
            stroke="rgba(255,255,255,0.15)"
            strokeDasharray="2 3"
          />
        )}

        <text
          x={4}
          y={PAD_T + 8}
          fontSize={9}
          fill="rgba(255,255,255,0.5)"
          fontFamily="var(--font-text)"
        >
          Δw
        </text>
        <text
          x={PLOT_W - 14}
          y={PAD_T + innerH + 14}
          fontSize={9}
          fill="rgba(255,255,255,0.5)"
          fontFamily="var(--font-text)"
        >
          ms
        </text>

        {!computed && (
          <text
            x={PAD_L + innerW / 2}
            y={PAD_T + innerH / 2 + 4}
            fontSize={10}
            textAnchor="middle"
            fill="rgba(255,255,255,0.35)"
            fontFamily="var(--font-text)"
          >
            no run yet — click compute
          </text>
        )}

        {computed && (
          <>
            <path d={computed.path} fill="none" stroke="#ffffff" strokeWidth={1.4} />
            <circle cx={computed.px} cy={computed.py} r={4} fill="#ff2d2d" />
          </>
        )}
      </svg>

      <div className="space-y-3 text-[13px]">
        <label className="flex items-baseline gap-2">
          <span className="meta-xs w-16 self-center">Δt ms</span>
          <input
            type="number"
            step="1"
            value={dt}
            onChange={(e) => setDt(parseFloat(e.target.value) || 0)}
            className="w-20 field"
          />
          <button onClick={onRun} disabled={running} className="btn btn-sm btn-red ml-auto">
            {running ? 'running…' : 'compute Δw'}
          </button>
        </label>

        {error && <p className="text-accent">{error}</p>}

        {response && (
          <dl className="space-y-1 text-white/70">
            <div className="flex gap-2">
              <dt className="meta-xs w-24 self-center">observed Δw</dt>
              <dd className={response.observed_delta_w >= 0 ? 'text-accent' : 'text-white'}>
                {response.observed_delta_w >= 0 ? '+' : ''}
                {response.observed_delta_w.toFixed(4)}
              </dd>
            </div>
            <div className="flex gap-2">
              <dt className="meta-xs w-24 self-center">kernel Δw</dt>
              <dd className="text-white/80">
                {response.kernel_delta_w >= 0 ? '+' : ''}
                {response.kernel_delta_w.toFixed(4)}
              </dd>
            </div>
            <div className="flex gap-2">
              <dt className="meta-xs w-24 self-center">pre / post</dt>
              <dd className="text-white/80">
                {response.pre_spike_ms.toFixed(1)} / {response.post_spike_ms.toFixed(1)} ms
              </dd>
            </div>
            <div className="flex gap-2">
              <dt className="meta-xs w-24 self-center">τ_+ / τ_-</dt>
              <dd className="text-white/80">
                {response.tau_plus_ms} / {response.tau_minus_ms} ms
              </dd>
            </div>
            <div className="flex gap-2">
              <dt className="meta-xs w-24 self-center">A_+ / A_-</dt>
              <dd className="text-white/80">
                {response.a_plus} / {response.a_minus}
              </dd>
            </div>
          </dl>
        )}

        {response && (
          <p className="hairline-t pt-3 text-[11.5px] leading-snug text-white/40">
            {response.citation}
          </p>
        )}
      </div>
    </section>
  );
}
