'use client';

import { useState } from 'react';

import { LinePlot } from '@/components/scales/LinePlot';
import { simulateSynapse } from '@/lib/api';
import type { SynapseResponse } from '@/lib/types';

// Anti-theater: traces are the backend's Destexhe 1994 dual-exponential
// conductances × Jahr-Stevens 1990 Mg block × driving force. The I-V curve is
// computed by the backend for 1 nS peak conductance. No sketching.

const COLORS: Record<string, string> = {
  AMPA: '#ffffff',
  NMDA: '#ff2d2d',
  GABA_A: '#9bd2ff',
};

export function SynapsePanel() {
  const [holding, setHolding] = useState(-65);
  const [mg, setMg] = useState(1.0);
  const [response, setResponse] = useState<SynapseResponse | null>(null);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const onRun = async () => {
    setRunning(true);
    setError(null);
    try {
      setResponse(
        await simulateSynapse({ holding_mV: holding, mg_mM: mg, duration_ms: 150, dt_ms: 0.2 }),
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setRunning(false);
    }
  };

  return (
    <section className="space-y-3">
      <div className="flex items-baseline justify-between">
        <h2 className="text-xs uppercase tracking-widest text-white/40">
          Synapse: AMPA · NMDA · GABA-A
        </h2>
        <span className="font-mono text-[10px] text-white/30">I = g(t)·B(V)·(V − E)</span>
      </div>

      <div className="font-mono text-[9px] uppercase tracking-widest text-white/50">
        postsynaptic current, 1 nS peak
      </div>
      <LinePlot
        width={320}
        height={120}
        xLabel="ms"
        yLabel="pA"
        zeroLine
        series={
          response
            ? response.traces.map((t) => ({
                xs: response.times_ms,
                ys: t.current_pA,
                color: COLORS[t.key] ?? '#fff',
                label: t.key,
              }))
            : []
        }
        empty="no run yet — click release"
      />

      <div className="font-mono text-[9px] uppercase tracking-widest text-white/50">
        NMDA peak current vs voltage (Jahr-Stevens)
      </div>
      <LinePlot
        width={320}
        height={110}
        xLabel="mV"
        yLabel="pA"
        zeroLine
        markers={
          response
            ? [{ x: response.holding_mV, label: 'V hold', color: 'rgba(255,255,255,0.5)' }]
            : []
        }
        series={
          response
            ? [
                {
                  xs: response.nmda_iv_voltage_mV,
                  ys: response.nmda_iv_with_mg_pA,
                  color: '#ff2d2d',
                  label: `Mg ${response.mg_mM} mM`,
                },
                {
                  xs: response.nmda_iv_voltage_mV,
                  ys: response.nmda_iv_without_mg_pA,
                  color: 'rgba(255,255,255,0.4)',
                  dash: '3 3',
                  label: 'no Mg',
                },
              ]
            : []
        }
        empty=""
      />

      <div className="space-y-2 font-mono text-xs">
        <label className="flex items-baseline gap-2">
          <span className="w-16 text-white/40">V hold</span>
          <input
            type="range"
            min={-90}
            max={40}
            step={1}
            value={holding}
            onChange={(e) => setHolding(parseInt(e.target.value))}
            className="w-32"
          />
          <span className="text-white">{holding} mV</span>
        </label>
        <label className="flex items-baseline gap-2">
          <span className="w-16 text-white/40">[Mg²⁺]</span>
          <input
            type="number"
            min={0}
            max={10}
            step={0.1}
            value={mg}
            onChange={(e) => setMg(Math.max(0, parseFloat(e.target.value) || 0))}
            className="w-24 rounded border border-white/10 bg-black px-2 py-1 text-white outline-none focus:border-white/40"
          />
          <span className="text-white/30">mM</span>
          <button
            onClick={onRun}
            disabled={running}
            className="ml-auto rounded border border-white/30 px-3 py-1 text-white hover:bg-white/10 disabled:cursor-not-allowed disabled:opacity-40"
          >
            {running ? 'running…' : 'release'}
          </button>
        </label>
        {error && <p className="text-accent">{error}</p>}
        {response && (
          <div className="space-y-1 text-white/70">
            {response.receptors.map((r) => {
              const t = response.traces.find((x) => x.key === r.key);
              return (
                <div key={r.key} className="flex items-baseline gap-2 text-[10px]">
                  <span
                    className="inline-block h-2 w-3 rounded"
                    style={{ background: COLORS[r.key] }}
                  />
                  <span className="w-14 text-white">{r.key}</span>
                  <span className="text-white/50">
                    τ↑{r.tau_rise_ms} / τ↓{r.tau_decay_ms} ms · E {r.e_rev_mV} mV
                    {r.mg_block && t ? ` · unblocked ${(t.block_fraction * 100).toFixed(0)}%` : ''}
                  </span>
                </div>
              );
            })}
          </div>
        )}
        {response && (
          <p className="border-t border-white/10 pt-2 text-[10px] leading-snug text-white/40">
            {response.citation}
          </p>
        )}
      </div>
    </section>
  );
}
