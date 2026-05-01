'use client';

import type { NeuronResponse } from '@/lib/types';
import { swcTypeLabel } from '@/lib/types';

import { CitationCard } from './CitationCard';
import { FiringPlot } from './FiringPlot';

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

      <FiringPlot selectedPointId={selected?.id ?? null} />

      <CitationCard neuron={neuron} />
    </aside>
  );
}
