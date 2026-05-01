'use client';

import { useEffect, useState } from 'react';

import { NeuronInspector } from '@/components/inspector/NeuronInspector';
import { NeuronCanvas } from '@/components/viewer/NeuronCanvas';
import { fetchNeuron } from '@/lib/api';
import { NeuronSelectionCtx } from '@/lib/neuron-context';
import type { NeuronResponse } from '@/lib/types';

const DEFAULT_NEURON_ID = 1;

interface SelectedPoint {
  id: number;
  type: number;
  parentId: number;
}

export default function Page() {
  const [neuronId, setNeuronId] = useState<number>(DEFAULT_NEURON_ID);
  const [neuron, setNeuron] = useState<NeuronResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<SelectedPoint | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    setSelected(null);
    fetchNeuron(neuronId)
      .then((data) => {
        if (!cancelled) {
          setNeuron(data);
          setLoading(false);
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : String(err));
          setLoading(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [neuronId]);

  return (
    <NeuronSelectionCtx.Provider value={{ selectNeuron: setNeuronId, selectedId: neuronId }}>
      <main className="flex h-screen w-screen flex-col bg-black text-white">
        <header className="flex items-baseline justify-between border-b border-white/10 px-6 py-4">
          <div className="flex items-baseline gap-3">
            <h1 className="text-xl font-semibold tracking-tight">NeuroForge</h1>
            <span className="text-xs text-white/40">six modules · click any panel neuron to render its swc</span>
          </div>
          {neuron && (
            <div className="text-xs text-white/60">
              <span className="text-white">{neuron.neuron_name}</span>
              {' · '}
              <span>{neuron.species}</span>
              {' · '}
              <span>{neuron.brain_region.join(' / ')}</span>
            </div>
          )}
        </header>

        <div className="flex flex-1 overflow-hidden">
          <div className="relative flex-1">
            {error && (
              <div className="absolute inset-0 flex items-center justify-center px-6 text-center text-sm text-accent">
                error fetching neuron {neuronId}: {error}
              </div>
            )}
            {loading && !error && (
              <div className="absolute inset-0 flex items-center justify-center text-sm text-white/40">
                loading neuron {neuronId} from neuromorpho.org…
              </div>
            )}
            {neuron && !loading && <NeuronCanvas neuron={neuron} onSegmentClick={setSelected} />}
          </div>

          {neuron && <NeuronInspector neuron={neuron} selected={selected} />}
        </div>
      </main>
    </NeuronSelectionCtx.Provider>
  );
}
