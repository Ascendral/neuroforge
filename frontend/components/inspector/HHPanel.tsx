'use client';

import { useState } from 'react';

import { simulateHH } from '@/lib/api';
import type { HHResponse } from '@/lib/types';

import { FiringPlot } from './FiringPlot';

// Standalone Hodgkin-Huxley runner (the same call NeuronInspector makes),
// so the HH model can be opened from the scale explorer without a neuron loaded.

export function HHPanel() {
  const [trace, setTrace] = useState<HHResponse | null>(null);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [stimulus, setStimulus] = useState(10.0);

  const onRun = async () => {
    setRunning(true);
    setError(null);
    try {
      setTrace(
        await simulateHH({
          duration_ms: 80,
          stimulus_uA: stimulus,
          stimulus_start_ms: 10,
          stimulus_end_ms: 70,
        }),
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setRunning(false);
    }
  };

  return (
    <section className="space-y-3">
      <FiringPlot trace={trace} selectedPointId={null} />
      <div className="space-y-2 font-mono text-xs">
        <label className="flex items-baseline gap-2">
          <span className="w-16 text-white/40">stim µA</span>
          <input
            type="number"
            step="0.5"
            value={stimulus}
            onChange={(e) => setStimulus(parseFloat(e.target.value) || 0)}
            className="w-20 rounded border border-white/10 bg-black px-2 py-1 text-white outline-none focus:border-white/40"
          />
          <button
            onClick={onRun}
            disabled={running}
            className="ml-auto rounded border border-white/30 px-3 py-1 text-white hover:bg-white/10 disabled:cursor-not-allowed disabled:opacity-40"
          >
            {running ? 'running…' : 'run hh'}
          </button>
        </label>
        {error && <p className="text-accent">{error}</p>}
        {trace && (
          <dl className="space-y-1 text-white/70">
            <div className="flex gap-2">
              <dt className="w-24 text-white/40">spikes</dt>
              <dd className="text-white">{trace.spike_times_ms.length}</dd>
            </div>
            <div className="flex gap-2">
              <dt className="w-24 text-white/40">peak mV</dt>
              <dd className="text-white">{Math.max(...trace.voltage_mV).toFixed(2)}</dd>
            </div>
          </dl>
        )}
        {trace && (
          <p className="border-t border-white/10 pt-2 text-[10px] leading-snug text-white/40">
            {trace.citation}
          </p>
        )}
      </div>
    </section>
  );
}
