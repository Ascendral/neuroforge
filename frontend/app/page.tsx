'use client';

import { useEffect, useState } from 'react';

import { NeuronInspector } from '@/components/inspector/NeuronInspector';
import { BrainCanvas, type NeuronMarker } from '@/components/viewer/BrainCanvas';
import { NeuronCanvas } from '@/components/viewer/NeuronCanvas';
import {
  fetchBrainMesh,
  fetchBrainRegions,
  fetchCA3Sample,
  fetchHippocampalSample,
  fetchNeuron,
  fetchV1NeuronSample,
} from '@/lib/api';
import { NeuronSelectionCtx } from '@/lib/neuron-context';
import type {
  BrainMeshResponse,
  BrainRegionsResponse,
  NeuronResponse,
} from '@/lib/types';

const DEFAULT_NEURON_ID = 1;
type ViewMode = 'brain' | 'neuron';

interface SelectedPoint {
  id: number;
  type: number;
  parentId: number;
}

export default function Page() {
  const [view, setView] = useState<ViewMode>('brain');
  const [neuronId, setNeuronId] = useState<number>(DEFAULT_NEURON_ID);
  const [neuron, setNeuron] = useState<NeuronResponse | null>(null);
  const [brain, setBrain] = useState<BrainMeshResponse | null>(null);
  const [regions, setRegions] = useState<BrainRegionsResponse | null>(null);
  const [markers, setMarkers] = useState<NeuronMarker[]>([]);
  const [neuronError, setNeuronError] = useState<string | null>(null);
  const [brainError, setBrainError] = useState<string | null>(null);
  const [selected, setSelected] = useState<SelectedPoint | null>(null);

  // Fetch brain mesh + regions once
  useEffect(() => {
    let cancelled = false;
    Promise.all([fetchBrainMesh(), fetchBrainRegions()])
      .then(([mesh, regs]) => {
        if (cancelled) return;
        setBrain(mesh);
        setRegions(regs);
      })
      .catch((err: unknown) => {
        if (!cancelled) setBrainError(err instanceof Error ? err.message : String(err));
      });
    return () => {
      cancelled = true;
    };
  }, []);

  // After regions arrive, fetch neuron samples from each anchored region
  // and convert them into placeable markers at their region centroids.
  useEffect(() => {
    if (!regions) return;
    let cancelled = false;

    const lookupCentroid = (label: string): [number, number, number] | null => {
      const sub = regions.subcortical.find((r) => r.label === label);
      if (sub?.centroid_mni_mm) {
        return sub.centroid_mni_mm as [number, number, number];
      }
      const cort = regions.cortical.find((r) => r.label === label);
      if (cort?.centroid_mni_mm) {
        return cort.centroid_mni_mm as [number, number, number];
      }
      return null;
    };

    Promise.all([
      fetchV1NeuronSample(5).catch(() => null),
      fetchHippocampalSample(5).catch(() => null),
      fetchCA3Sample(5).catch(() => null),
    ])
      .then(([v1, hippo, ca3]) => {
        if (cancelled) return;
        const out: NeuronMarker[] = [];
        const v1Centroid = lookupCentroid('Intracalcarine Cortex');
        if (v1 && v1Centroid) {
          v1.results.forEach((n) =>
            out.push({ neuron: n, centroid_mni_mm: v1Centroid, module: 'hubel_wiesel', color: '#9bd2ff' }),
          );
        }
        const hippoLeft = lookupCentroid('Left Hippocampus');
        if (hippo && hippoLeft) {
          hippo.results.forEach((n, i) =>
            out.push({
              neuron: n,
              centroid_mni_mm: i % 2 === 0 ? hippoLeft : (lookupCentroid('Right Hippocampus') ?? hippoLeft),
              module: 'hebbian',
              color: '#7fff9b',
            }),
          );
        }
        const ca3Left = lookupCentroid('Left Hippocampus');
        if (ca3 && ca3Left) {
          ca3.results.forEach((n, i) =>
            out.push({
              neuron: n,
              centroid_mni_mm: i % 2 === 0 ? ca3Left : (lookupCentroid('Right Hippocampus') ?? ca3Left),
              module: 'hopfield',
              color: '#ff2d2d',
            }),
          );
        }
        setMarkers(out);
      })
      .catch(() => {
        // Sample fetches are non-fatal; brain still renders without them.
      });

    return () => {
      cancelled = true;
    };
  }, [regions]);

  // Fetch neuron when neuronId changes
  useEffect(() => {
    let cancelled = false;
    setNeuronError(null);
    setSelected(null);
    fetchNeuron(neuronId)
      .then((data) => {
        if (!cancelled) setNeuron(data);
      })
      .catch((err: unknown) => {
        if (!cancelled) setNeuronError(err instanceof Error ? err.message : String(err));
      });
    return () => {
      cancelled = true;
    };
  }, [neuronId]);

  const selectNeuron = (id: number) => {
    setNeuronId(id);
    setView('neuron');
  };

  return (
    <NeuronSelectionCtx.Provider value={{ selectNeuron, selectedId: neuronId }}>
      <main className="flex h-screen w-screen flex-col bg-black text-white">
        <header className="flex items-baseline justify-between border-b border-white/10 px-6 py-4">
          <div className="flex items-baseline gap-3">
            <h1 className="text-xl font-semibold tracking-tight">NeuroForge</h1>
            <span className="text-xs text-white/40">
              fsaverage5 + harvard-oxford + 6 modules
            </span>
          </div>
          <div className="flex items-center gap-3 text-xs">
            <button
              onClick={() => setView('brain')}
              className={`rounded border px-3 py-1 font-mono ${
                view === 'brain'
                  ? 'border-accent text-white'
                  : 'border-white/20 text-white/50 hover:bg-white/5'
              }`}
            >
              brain
            </button>
            <button
              onClick={() => setView('neuron')}
              className={`rounded border px-3 py-1 font-mono ${
                view === 'neuron'
                  ? 'border-accent text-white'
                  : 'border-white/20 text-white/50 hover:bg-white/5'
              }`}
            >
              neuron
            </button>
            {view === 'neuron' && neuron && (
              <div className="text-white/60">
                <span className="text-white">{neuron.neuron_name}</span>
                {' · '}
                <span>{neuron.species}</span>
                {' · '}
                <span>{neuron.brain_region.join(' / ')}</span>
              </div>
            )}
            {view === 'brain' && brain && (
              <div className="text-white/60">
                fsaverage5 ·{' '}
                {(brain.left.vertex_count + brain.right.vertex_count).toLocaleString()} vertices
                {markers.length > 0 && (
                  <>
                    {' · '}
                    <span className="text-white">{markers.length}</span> neurons (schematic
                    placement at region centroids)
                  </>
                )}
              </div>
            )}
          </div>
        </header>

        <div className="flex flex-1 overflow-hidden">
          <div className="relative flex-1">
            {view === 'brain' && (
              <>
                {brainError && (
                  <div className="absolute inset-0 flex items-center justify-center px-6 text-center text-sm text-accent">
                    error fetching brain mesh: {brainError}
                  </div>
                )}
                {!brain && !brainError && (
                  <div className="absolute inset-0 flex items-center justify-center text-sm text-white/40">
                    loading fsaverage5 cortical mesh…
                  </div>
                )}
                {brain && <BrainCanvas mesh={brain} markers={markers} />}
              </>
            )}
            {view === 'neuron' && (
              <>
                {neuronError && (
                  <div className="absolute inset-0 flex items-center justify-center px-6 text-center text-sm text-accent">
                    error fetching neuron {neuronId}: {neuronError}
                  </div>
                )}
                {!neuron && !neuronError && (
                  <div className="absolute inset-0 flex items-center justify-center text-sm text-white/40">
                    loading neuron {neuronId} from neuromorpho.org…
                  </div>
                )}
                {neuron && <NeuronCanvas neuron={neuron} onSegmentClick={setSelected} />}
              </>
            )}
          </div>

          {neuron && <NeuronInspector neuron={neuron} selected={selected} />}
        </div>
      </main>
    </NeuronSelectionCtx.Provider>
  );
}
