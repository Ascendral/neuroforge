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
      <div className="space-y-3 text-[13px]">
        <label className="flex items-baseline gap-2">
          <span className="meta-xs w-16 self-center">stim µA</span>
          <input
            type="number"
            step="0.5"
            value={stimulus}
            onChange={(e) => setStimulus(parseFloat(e.target.value) || 0)}
            className="w-20 field"
          />
          <button onClick={onRun} disabled={running} className="btn btn-sm btn-red ml-auto">
            {running ? 'running…' : 'run hh'}
          </button>
        </label>
        {error && <p className="text-accent">{error}</p>}
        {trace && (
          <dl className="space-y-1 text-white/70">
            <div className="flex gap-2">
              <dt className="meta-xs w-24 self-center">spikes</dt>
              <dd className="text-white">{trace.spike_times_ms.length}</dd>
            </div>
            <div className="flex gap-2">
              <dt className="meta-xs w-24 self-center">peak mV</dt>
              <dd className="text-white">{Math.max(...trace.voltage_mV).toFixed(2)}</dd>
            </div>
          </dl>
        )}
        {trace && (
          <p className="hairline-t pt-3 text-[11.5px] leading-snug text-white/40">
            {trace.citation}
          </p>
        )}
      </div>
    </section>
  );
}
