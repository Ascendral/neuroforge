'use client';

import { useState } from 'react';

import { simulateHH } from '@/lib/api';
import type { HHResponse, NeuronResponse } from '@/lib/types';
import { swcTypeLabel } from '@/lib/types';

import { CitationCard } from './CitationCard';
import { FiringPlot } from './FiringPlot';
import { HebbianPanel } from './HebbianPanel';
import { HopfieldPanel } from './HopfieldPanel';
import { HubelWieselPanel } from './HubelWieselPanel';
import { McCullochPittsPanel } from './McCullochPittsPanel';
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
      <dt className="meta-xs w-24 shrink-0 self-center">{label}</dt>
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
      className="hairline-l flex h-full w-[400px] shrink-0 flex-col gap-7 overflow-y-auto bg-canvas p-6 text-[14px]"
    >
      <section className="space-y-3">
        <h2 className="kicker">Neuron</h2>
        <dl className="space-y-1.5 text-[13px]">
          <MetaRow label="name" value={neuron.neuron_name} />
          <MetaRow label="id" value={`#${neuron.neuron_id}`} />
          <MetaRow label="species" value={neuron.species || '—'} />
          <MetaRow
            label="scientific"
            value={
              neuron.scientific_name ? (
                <em className="not-italic">{neuron.scientific_name}</em>
              ) : (
                '—'
              )
            }
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
        <h2 className="kicker">Selection</h2>
        {selected === null ? (
          <p className="text-xs text-white/40">click any segment to inspect</p>
        ) : (
          <dl className="space-y-1.5 text-[13px]">
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

          {simError && <p className="text-accent">{simError}</p>}

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
              <div className="flex gap-2">
                <dt className="meta-xs w-24 self-center">trough mV</dt>
                <dd className="text-white">{Math.min(...trace.voltage_mV).toFixed(2)}</dd>
              </div>
              <div className="flex gap-2">
                <dt className="meta-xs w-24 self-center">samples</dt>
                <dd className="text-white">{trace.times_ms.length}</dd>
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

      <McCullochPittsPanel />

      <STDPPanel />

      <HebbianPanel />

      <HopfieldPanel />

      <HubelWieselPanel />

      <CitationCard neuron={neuron} />
    </aside>
  );
}
