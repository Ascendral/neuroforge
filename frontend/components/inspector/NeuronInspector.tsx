'use client';

import { useState } from 'react';

import { simulateHH } from '@/lib/api';
import type { HHResponse, NeuronResponse } from '@/lib/types';
import { swcTypeLabel } from '@/lib/types';

import { CitationCard } from './CitationCard';
import { FiringPlot } from './FiringPlot';
import { HubelWieselPanel } from './HubelWieselPanel';
import { STDPPanel } from './STDPPanel';

interface SelectedPoint {
  id: number;
  type: number;
  parentId: number;
}

interface NeuronInspectorProps {
  neuron: NeuronResponse;
  selected: SelectedPoint | null;
}

function MetaRow({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex gap-3">
      <dt className="w-24 shrink-0 text-white/40">{label}</dt>
      <dd className="text-white">{value}</dd>
    </div>
  );
}

export function NeuronInspector({ neuron, selected }: NeuronInspectorProps) {
  const [trace, setTrace] = useState<HHResponse | null>(null);
  const [running, setRunning] = useState(false);
  const [simError, setSimError] = useState<string | null>(null);
  const [stimulus, setStimulus] = useState(10.0);

  const onRun = async () => {
    setRunning(true);
    setSimError(null);
    try {
      const result = await simulateHH({
        duration_ms: 80,
        stimulus_uA: stimulus,
        stimulus_start_ms: 10,
        stimulus_end_ms: 70,
      });
      setTrace(result);
    } catch (err) {
      setSimError(err instanceof Error ? err.message : String(err));
    } finally {
      setRunning(false);
    }
  };

  return (
    <aside
      aria-label="Neuron inspector"
      className="flex h-full w-[360px] shrink-0 flex-col gap-6 overflow-y-auto border-l border-white/10 bg-black p-5 text-sm"
    >
      <section className="space-y-3">
        <h2 className="text-xs uppercase tracking-widest text-white/40">Neuron</h2>
        <dl className="space-y-1 font-mono text-xs">
          <MetaRow label="name" value={neuron.neuron_name} />
          <MetaRow label="id" value={`#${neuron.neuron_id}`} />
          <MetaRow label="species" value={neuron.species || '—'} />
          <MetaRow
            label="scientific"
            value={neuron.scientific_name ? <em className="not-italic">{neuron.scientific_name}</em> : '—'}
          />
          <MetaRow
            label="region"
            value={neuron.brain_region.length ? neuron.brain_region.join(' / ') : '—'}
          />
          <MetaRow
            label="cell type"
            value={neuron.cell_type.length ? neuron.cell_type.join(', ') : '—'}
          />
          <MetaRow label="points" value={neuron.point_count.toLocaleString()} />
        </dl>
      </section>

      <section className="space-y-3">
        <h2 className="text-xs uppercase tracking-widest text-white/40">Selection</h2>
        {selected === null ? (
          <p className="text-xs text-white/40">click any segment to inspect</p>
        ) : (
          <dl className="space-y-1 font-mono text-xs">
            <MetaRow label="point id" value={<span className="text-accent">{selected.id}</span>} />
            <MetaRow
              label="type"
              value={
                <>
                  <span className="text-white">{swcTypeLabel(selected.type)}</span>{' '}
                  <span className="text-white/40">({selected.type})</span>
                </>
              }
            />
            <MetaRow
              label="parent"
              value={
                selected.parentId === -1 ? (
                  <span className="text-white/60">root</span>
                ) : (
                  <span>{selected.parentId}</span>
                )
              }
            />
          </dl>
        )}
      </section>

      <section className="space-y-3">
        <FiringPlot trace={trace} selectedPointId={selected?.id ?? null} />

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

          {simError && <p className="text-accent">{simError}</p>}

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
              <div className="flex gap-2">
                <dt className="w-24 text-white/40">trough mV</dt>
                <dd className="text-white">{Math.min(...trace.voltage_mV).toFixed(2)}</dd>
              </div>
              <div className="flex gap-2">
                <dt className="w-24 text-white/40">samples</dt>
                <dd className="text-white">{trace.times_ms.length}</dd>
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

      <STDPPanel />

      <HubelWieselPanel />

      <CitationCard neuron={neuron} />
    </aside>
  );
}
