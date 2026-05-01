'use client';

import { useEffect, useState } from 'react';

import { NeuronCanvas } from '@/components/viewer/NeuronCanvas';
import { fetchNeuron } from '@/lib/api';
import type { NeuronResponse } from '@/lib/types';
import { swcTypeLabel } from '@/lib/types';

const DEFAULT_NEURON_ID = 1;

interface ClickedInfo {
  id: number;
  type: number;
  parentId: number;
}

export default function Page() {
  const [neuron, setNeuron] = useState<NeuronResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [clicked, setClicked] = useState<ClickedInfo | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetchNeuron(DEFAULT_NEURON_ID)
      .then((data) => {
        if (!cancelled) setNeuron(data);
      })
      .catch((err: unknown) => {
        if (!cancelled) setError(err instanceof Error ? err.message : String(err));
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <main className="flex h-screen w-screen flex-col bg-black text-white">
      <header className="flex items-baseline justify-between border-b border-white/10 px-6 py-4">
        <div className="flex items-baseline gap-3">
          <h1 className="text-xl font-semibold tracking-tight">NeuroForge</h1>
          <span className="text-xs text-white/40">phase 2 — 3d viewer</span>
        </div>
        {neuron && (
          <div className="text-xs text-white/60">
            <span className="text-white">{neuron.neuron_name}</span>
            {' · '}
            <span>{neuron.species}</span>
            {' · '}
            <span>{neuron.brain_region.join(' / ')}</span>
            {' · '}
            <span>{neuron.point_count.toLocaleString()} points</span>
          </div>
        )}
      </header>

      <div className="relative flex-1">
        {error && (
          <div className="absolute inset-0 flex items-center justify-center text-sm text-accent">
            error: {error}
          </div>
        )}
        {!neuron && !error && (
          <div className="absolute inset-0 flex items-center justify-center text-sm text-white/40">
            loading neuron {DEFAULT_NEURON_ID} from neuromorpho.org…
          </div>
        )}
        {neuron && <NeuronCanvas neuron={neuron} onSegmentClick={setClicked} />}

        {clicked && (
          <div className="pointer-events-none absolute bottom-4 left-4 rounded border border-white/10 bg-black/80 p-3 font-mono text-xs">
            <div>
              point id <span className="text-accent">{clicked.id}</span>
            </div>
            <div>
              type <span className="text-white">{swcTypeLabel(clicked.type)}</span>{' '}
              <span className="text-white/40">({clicked.type})</span>
            </div>
            <div>
              parent <span className="text-white/70">{clicked.parentId}</span>
            </div>
          </div>
        )}

        {neuron && (
          <div className="pointer-events-none absolute bottom-4 right-4 max-w-sm rounded border border-white/10 bg-black/80 p-3 text-xs">
            <div className="mb-1 text-white/40">source</div>
            <div className="font-mono text-white/80">
              neuromorpho.org · {neuron.archive} · neuron {neuron.neuron_id}
            </div>
            {neuron.reference_doi.length > 0 && (
              <div className="mt-1 font-mono text-white/50">
                doi: {neuron.reference_doi[0]}
              </div>
            )}
          </div>
        )}
      </div>
    </main>
  );
}
