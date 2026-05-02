'use client';

import { useEffect, useState } from 'react';

import { NeuronInspector } from '@/components/inspector/NeuronInspector';
import { CollapsibleSection } from '@/components/ui/CollapsibleSection';
import {
  BrainCanvas,
  type FunctionHighlight,
  type NeuronMarker,
  type RegionIntensity,
  type TractCurve,
} from '@/components/viewer/BrainCanvas';
import type {
  FunctionalNetworksResponse,
  PauliNucleiResponse,
  SchaeferParcelsResponse,
} from '@/lib/types';
import { NeuronCanvas } from '@/components/viewer/NeuronCanvas';
import {
  fetchBrainMesh,
  fetchBrainRegions,
  fetchCA3Sample,
  fetchCognitiveFunctions,
  fetchHippocampalSample,
  fetchNeuron,
  fetchFunctionalNetworks,
  fetchPauliNuclei,
  fetchReceptorMap,
  fetchReceptors,
  fetchRegionSample,
  fetchSchaeferParcels,
  fetchSubcorticalMeshes,
  fetchV1NeuronSample,
  fetchWhiteMatterTracts,
} from '@/lib/api';
import { NeuronSelectionCtx } from '@/lib/neuron-context';
import type {
  BrainMeshResponse,
  BrainRegionsResponse,
  CognitiveFunction,
  CognitiveFunctionsResponse,
  NeuronResponse,
  ReceptorListResponse,
  ReceptorMapResponse,
  SubcorticalMeshResponse,
  WhiteMatterTractsResponse,
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
  const [swcMap, setSwcMap] = useState<Map<number, NeuronResponse>>(new Map());
  const [neuronError, setNeuronError] = useState<string | null>(null);
  const [brainError, setBrainError] = useState<string | null>(null);
  const [selected, setSelected] = useState<SelectedPoint | null>(null);
  const [clickedRegion, setClickedRegion] = useState<{
    label: string;
    point: [number, number, number];
    nearestModule?: { module: string; ho_label: string; distance_mm: number } | null;
  } | null>(null);
  const [functions, setFunctions] = useState<CognitiveFunctionsResponse | null>(null);
  const [activeFunction, setActiveFunction] = useState<CognitiveFunction | null>(null);
  const [receptors, setReceptors] = useState<ReceptorListResponse | null>(null);
  const [activeReceptor, setActiveReceptor] = useState<ReceptorMapResponse | null>(null);
  const [receptorLoading, setReceptorLoading] = useState(false);
  const [tracts, setTracts] = useState<WhiteMatterTractsResponse | null>(null);
  const [tractsVisible, setTractsVisible] = useState(false);
  const [subcortical, setSubcortical] = useState<SubcorticalMeshResponse | null>(null);
  const [yeoNetworks, setYeoNetworks] = useState<FunctionalNetworksResponse | null>(null);
  const [networksVisible, setNetworksVisible] = useState(false);
  const [schaefer, setSchaefer] = useState<SchaeferParcelsResponse | null>(null);
  const [schaeferVisible, setSchaeferVisible] = useState(false);
  const [pauli, setPauli] = useState<PauliNucleiResponse | null>(null);
  const [pauliVisible, setPauliVisible] = useState(false);

  // Fetch brain mesh + regions + cognitive functions + receptor list once
  useEffect(() => {
    let cancelled = false;
    Promise.all([
      fetchBrainMesh(),
      fetchBrainRegions(),
      fetchCognitiveFunctions(),
      fetchReceptors(),
      fetchWhiteMatterTracts(),
      fetchSubcorticalMeshes(),
      fetchFunctionalNetworks().catch(() => null),
      fetchSchaeferParcels().catch(() => null),
      fetchPauliNuclei().catch(() => null),
    ])
      .then(([mesh, regs, funs, recs, trks, sub, nets, sch, pau]) => {
        if (cancelled) return;
        setBrain(mesh);
        setRegions(regs);
        setFunctions(funs);
        setReceptors(recs);
        setTracts(trks);
        setSubcortical(sub);
        if (nets) setYeoNetworks(nets);
        if (sch) setSchaefer(sch);
        if (pau) setPauli(pau);
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

    // 8 anatomical populations to surface inside the brain shell. Each
    // entry pairs a NeuroMorpho query with its Harvard-Oxford anchor label
    // (left/right hemisphere split for bilateral structures).
    const populations: Array<{
      label: string;
      module: string;
      color: string;
      bilateral: boolean;
      leftLabel: string;
      rightLabel?: string;
      fetcher: () => Promise<{ results: typeof v1Cells extends infer T ? T : never } | null>;
    }> = [];

    const fetchSafe = (p: Promise<unknown>) =>
      p.catch(() => null) as Promise<{
        results: { neuron_id: number; neuron_name: string; archive: string; species: string; scientific_name: string; brain_region: string[]; cell_type: string[]; reference_doi: string[]; reference_pmid: string[]; png_url: string | null; source_url: string; swc_url: string }[];
      } | null>;
    let v1Cells: unknown;
    void v1Cells;

    // Schematic MNI centroids for structures not in Harvard-Oxford.
    // Approximate from Mai JK, Majtanik M, Paxinos G. Atlas of the Human
    // Brain, 4th ed. Academic Press, 2015. Labeled "schematic" in legend.
    const cerebellum: [number, number, number] = [0, -60, -30];
    const olfactoryL: [number, number, number] = [-5, 30, -25];
    const olfactoryR: [number, number, number] = [5, 30, -25];
    const substantiaNigraL: [number, number, number] = [-10, -15, -10];
    const substantiaNigraR: [number, number, number] = [10, -15, -10];

    Promise.all([
      fetchSafe(fetchV1NeuronSample(10)),
      fetchSafe(fetchHippocampalSample(10)),
      fetchSafe(fetchCA3Sample(10)),
      fetchSafe(fetchRegionSample('primary motor', { cell_type: 'pyramidal', size: 10 })),
      fetchSafe(fetchRegionSample('prefrontal', { cell_type: 'pyramidal', size: 10 })),
      fetchSafe(fetchRegionSample('thalamus', { size: 10 })),
      fetchSafe(fetchRegionSample('amygdala', { size: 10 })),
      fetchSafe(fetchRegionSample('striatum', { size: 10 })),
      fetchSafe(fetchRegionSample('cerebellum', { cell_type: 'Purkinje', size: 10 })),
      fetchSafe(fetchRegionSample('dentate gyrus', { cell_type: 'granule', size: 10 })),
      fetchSafe(fetchRegionSample('main olfactory bulb', { cell_type: 'mitral', size: 10 })),
      fetchSafe(fetchRegionSample('substantia nigra', { cell_type: 'dopaminergic', size: 10 })),
    ])
      .then(([v1, hippo, ca3, motor, pfc, thal, amyg, stri, purk, dg, olf, sn]) => {
        if (cancelled) return;

        const out: NeuronMarker[] = [];
        // Per-population glyph scale. Small subcortical regions need smaller
        // scale so the rendered cell stays within the region's real anatomical
        // bounds. Cortex has more room; cortical pyramidals can stay bigger.
        // Hippocampus / amygdala / thalamus / striatum are tight subcortical
        // structures (~13-22 mm wide) so we use 0.006 → cells ~2-6 mm.
        const SCALE_CORTICAL = 0.012;     // V1, motor, prefrontal
        const SCALE_SUBCORTICAL = 0.006;  // hippocampus, amygdala, thalamus, striatum
        const SCALE_SCHEMATIC = 0.008;    // cerebellum, olfactory, SN, dentate

        const push = (
          sample: { results: NeuronMarker['neuron'][] } | null,
          leftLabel: string,
          color: string,
          module: string,
          scale: number,
          rightLabel?: string,
        ) => {
          if (!sample) return;
          const left = lookupCentroid(leftLabel);
          const right = rightLabel ? lookupCentroid(rightLabel) : null;
          sample.results.forEach((n, i) => {
            const c = right && i % 2 === 1 ? right : left;
            if (!c) return;
            out.push({ neuron: n, centroid_mni_mm: c, module, color, scale });
          });
        };

        // Schematic-anchor variant: uses hardcoded MNI centroids from Mai 2015
        const pushSchematic = (
          sample: { results: NeuronMarker['neuron'][] } | null,
          leftCentroid: [number, number, number],
          color: string,
          module: string,
          scale: number,
          rightCentroid?: [number, number, number],
        ) => {
          if (!sample) return;
          sample.results.forEach((n, i) => {
            const c = rightCentroid && i % 2 === 1 ? rightCentroid : leftCentroid;
            out.push({ neuron: n, centroid_mni_mm: c, module, color, scale });
          });
        };

        push(v1 as { results: NeuronMarker['neuron'][] } | null, 'Intracalcarine Cortex', '#9bd2ff', 'hubel_wiesel', SCALE_CORTICAL);
        push(hippo as { results: NeuronMarker['neuron'][] } | null, 'Left Hippocampus', '#7fff9b', 'hebbian', SCALE_SUBCORTICAL, 'Right Hippocampus');
        push(ca3 as { results: NeuronMarker['neuron'][] } | null, 'Left Hippocampus', '#ff2d2d', 'hopfield', SCALE_SUBCORTICAL, 'Right Hippocampus');
        push(motor as { results: NeuronMarker['neuron'][] } | null, 'Precentral Gyrus', '#ffd86b', 'motor_cortex', SCALE_CORTICAL);
        push(pfc as { results: NeuronMarker['neuron'][] } | null, 'Frontal Pole', '#d99bff', 'prefrontal', SCALE_CORTICAL);
        push(thal as { results: NeuronMarker['neuron'][] } | null, 'Left Thalamus', '#ff9b6b', 'thalamus', SCALE_SUBCORTICAL, 'Right Thalamus');
        push(amyg as { results: NeuronMarker['neuron'][] } | null, 'Left Amygdala', '#ff6bd4', 'amygdala', SCALE_SUBCORTICAL, 'Right Amygdala');
        push(stri as { results: NeuronMarker['neuron'][] } | null, 'Left Caudate', '#6bffd4', 'striatum', SCALE_SUBCORTICAL, 'Right Caudate');

        // Schematic placements (no Harvard-Oxford label exists for these).
        pushSchematic(purk as { results: NeuronMarker['neuron'][] } | null, cerebellum, '#ff8c5e', 'cerebellum_purkinje', SCALE_SCHEMATIC);
        push(dg as { results: NeuronMarker['neuron'][] } | null, 'Left Hippocampus', '#b5e85b', 'dentate_granule', SCALE_SUBCORTICAL, 'Right Hippocampus');
        pushSchematic(olf as { results: NeuronMarker['neuron'][] } | null, olfactoryL, '#ff6bb5', 'olfactory_mitral', SCALE_SCHEMATIC, olfactoryR);
        pushSchematic(sn as { results: NeuronMarker['neuron'][] } | null, substantiaNigraL, '#c45eff', 'substantia_nigra_dopa', SCALE_SUBCORTICAL, substantiaNigraR);

        setMarkers(out);
      })
      .catch(() => {
        // Sample fetches are non-fatal; brain still renders without them.
      });

    return () => {
      cancelled = true;
    };
  }, [regions]);

  // Once markers are placed, fetch each neuron's SWC in parallel so the
  // brain shell can replace dots with actual reconstructed morphology.
  // Backend's SQLite cache makes warm refetches fast; cold first run hits
  // neuromorpho.org (slow but populates the cache).
  useEffect(() => {
    if (markers.length === 0) return;
    let cancelled = false;
    Promise.all(
      markers.map((m) =>
        fetchNeuron(m.neuron.neuron_id)
          .then((data) => [m.neuron.neuron_id, data] as const)
          .catch(() => null),
      ),
    ).then((entries) => {
      if (cancelled) return;
      const map = new Map<number, NeuronResponse>();
      for (const e of entries) {
        if (e !== null) map.set(e[0], e[1]);
      }
      setSwcMap(map);
    });
    return () => {
      cancelled = true;
    };
  }, [markers]);

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

  const handleRegionClick = (info: {
    destrieuxId: number;
    label: string;
    point: [number, number, number];
  }) => {
    if (!regions) {
      setClickedRegion({ label: info.label, point: info.point, nearestModule: null });
      return;
    }
    // Find the nearest anchored module by Euclidean distance from the click
    // point (MNI mm) to each module's region centroid (HO labels).
    let best: { module: string; ho_label: string; distance_mm: number } | null = null;
    for (const m of regions.module_mapping) {
      if (!m.has_anatomical_anchor) continue;
      for (const lbl of m.labels) {
        const candidate =
          regions.subcortical.find((r) => r.label === lbl) ??
          regions.cortical.find((r) => r.label === lbl);
        if (!candidate?.centroid_mni_mm) continue;
        const c = candidate.centroid_mni_mm;
        const d = Math.sqrt(
          (c[0] - info.point[0]) ** 2 +
            (c[1] - info.point[1]) ** 2 +
            (c[2] - info.point[2]) ** 2,
        );
        if (!best || d < best.distance_mm) {
          best = { module: m.module, ho_label: lbl, distance_mm: d };
        }
      }
    }
    setClickedRegion({
      label: info.label,
      point: info.point,
      nearestModule: best,
    });
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
                {brain && (
                  <BrainCanvas
                    mesh={brain}
                    markers={markers}
                    swcMap={swcMap}
                    subcorticalMeshes={subcortical?.meshes ?? []}
                    networks={networksVisible && yeoNetworks ? yeoNetworks.networks : []}
                    schaeferParcels={schaeferVisible && schaefer ? schaefer.parcels : []}
                    pauliNuclei={pauliVisible && pauli ? pauli.nuclei : []}
                    onRegionClick={handleRegionClick}
                    functionHighlights={
                      activeFunction
                        ? (activeFunction.region_centroids
                            .filter((r) => r.found && r.centroid_mni_mm)
                            .map((r) => ({
                              label: r.label,
                              centroid_mni_mm: r.centroid_mni_mm as [number, number, number],
                            })) as FunctionHighlight[])
                        : []
                    }
                    tracts={
                      tractsVisible && tracts
                        ? (tracts.tracts
                            .filter((t) => t.start_mni_mm && t.end_mni_mm && t.midpoint_mni_mm)
                            .map(
                              (t) =>
                                ({
                                  name: t.name,
                                  color: t.color,
                                  start: t.start_mni_mm as [number, number, number],
                                  midpoint: t.midpoint_mni_mm as [number, number, number],
                                  end: t.end_mni_mm as [number, number, number],
                                }) as TractCurve,
                            ) as TractCurve[])
                        : []
                    }
                    regionIntensities={
                      activeReceptor
                        ? ([...activeReceptor.cortical, ...activeReceptor.subcortical]
                            .filter((r) => r.centroid_mni_mm)
                            .map(
                              (r) =>
                                ({
                                  label: r.label,
                                  centroid_mni_mm: r.centroid_mni_mm as [
                                    number,
                                    number,
                                    number,
                                  ],
                                  normalized: r.normalized,
                                }) as RegionIntensity,
                            ) as RegionIntensity[])
                        : []
                    }
                  />
                )}
                {functions && view === 'brain' && (
                  <div className="absolute left-4 top-4 w-[280px] max-h-[calc(100vh-3rem)] space-y-2 overflow-y-auto pr-1">
                    <CollapsibleSection
                      title="cognitive functions"
                      subtitle={`${functions.functions.length}`}
                      defaultOpen
                    >
                      <p className="font-mono text-[10px] leading-snug text-white/50">
                        Click any function. Brain regions associated with it will glow yellow.
                        Each entry cites its foundational discovery paper.
                      </p>
                      <div className="flex flex-wrap gap-1">
                        {functions.functions.map((f) => {
                          const isActive = activeFunction?.name === f.name;
                          return (
                            <button
                              key={f.name}
                              onClick={() => setActiveFunction(isActive ? null : f)}
                              className={`rounded border px-2 py-1 font-mono text-[10px] ${
                                isActive
                                  ? 'border-[#ffe45e] bg-[#ffe45e]/10 text-white'
                                  : 'border-white/20 text-white/60 hover:bg-white/5'
                              }`}
                            >
                              {f.name}
                            </button>
                          );
                        })}
                      </div>
                      {activeFunction && (
                        <div className="rounded border border-[#ffe45e]/40 bg-black/60 p-2 font-mono text-[10px] leading-snug">
                          <div className="mb-1 text-white">{activeFunction.name}</div>
                          <div className="mb-2 text-white/60">{activeFunction.description}</div>
                          <div className="mb-1 text-white/40">
                            regions (
                            {activeFunction.region_centroids.filter((r) => r.found).length}/
                            {activeFunction.atlas_labels.length}):
                          </div>
                          <ul className="mb-2 space-y-0.5">
                            {activeFunction.region_centroids.map((r) => (
                              <li
                                key={r.label}
                                className={
                                  r.found ? 'text-white/80' : 'text-white/30 line-through'
                                }
                              >
                                {r.label}
                              </li>
                            ))}
                          </ul>
                          <div className="border-t border-white/10 pt-2 text-white/40">
                            {activeFunction.citation}
                          </div>
                        </div>
                      )}
                    </CollapsibleSection>

                    {pauli && (
                      <CollapsibleSection
                        title="deep nuclei (Pauli 2017)"
                        subtitle={`${pauli.nuclei.length}`}
                        rightSlot={
                          <span
                            onClick={(e) => {
                              e.stopPropagation();
                              setPauliVisible((v) => !v);
                            }}
                            className={`rounded border px-2 py-0.5 font-mono text-[9px] ${
                              pauliVisible
                                ? 'border-[#ff2d2d] bg-[#ff2d2d]/10 text-white'
                                : 'border-white/20 text-white/60 hover:bg-white/5'
                            }`}
                          >
                            {pauliVisible ? 'hide on brain' : 'show on brain'}
                          </span>
                        }
                      >
                        <p className="font-mono text-[10px] leading-snug text-white/50">
                          16 deep subcortical nuclei. <span className="text-white/80">VTA</span> makes
                          the dopamine for reward; <span className="text-white/80">SNc</span> makes the
                          dopamine for movement (degenerates in Parkinson&apos;s).{' '}
                          <span className="text-white/80">GPi/GPe</span> are the basal ganglia output;{' '}
                          <span className="text-white/80">HTH</span> is the hypothalamus (sleep,
                          appetite, hormones); <span className="text-white/80">MN</span> is the
                          mammillary nucleus in the Papez memory circuit.
                        </p>
                        <div className="space-y-0.5 font-mono text-[10px]">
                          {pauli.nuclei.map((n) => (
                            <div key={n.abbrev} className="flex items-baseline gap-2">
                              <span
                                className="inline-block h-2 w-3 rounded"
                                style={{ background: n.color }}
                              />
                              <span className="text-white/80">{n.abbrev}</span>
                              <span className="text-white/50">{n.full_name}</span>
                            </div>
                          ))}
                        </div>
                        <p className="border-t border-white/10 pt-2 font-mono text-[10px] text-white/40">
                          Pauli et al. Sci Data. 2018. doi:10.1038/sdata.2018.63
                        </p>
                      </CollapsibleSection>
                    )}

                    {schaefer && (
                      <CollapsibleSection
                        title="schaefer 100 parcels (2018)"
                        subtitle={`${schaefer.n_parcels}`}
                        rightSlot={
                          <span
                            onClick={(e) => {
                              e.stopPropagation();
                              setSchaeferVisible((v) => !v);
                            }}
                            className={`rounded border px-2 py-0.5 font-mono text-[9px] ${
                              schaeferVisible
                                ? 'border-[#7fff9b] bg-[#7fff9b]/10 text-white'
                                : 'border-white/20 text-white/60 hover:bg-white/5'
                            }`}
                          >
                            {schaeferVisible ? 'hide on brain' : 'show on brain'}
                          </span>
                        }
                      >
                        <p className="font-mono text-[10px] leading-snug text-white/50">
                          The cortex split into 100 fine-grained parcels, each colored by which of
                          the 7 Yeo functional networks it belongs to. Useful for seeing functional
                          subdivisions within each network.
                        </p>
                        <p className="font-mono text-[10px] text-white/40">
                          Schaefer et al. Cereb Cortex. 2018. doi:10.1093/cercor/bhx179
                        </p>
                      </CollapsibleSection>
                    )}

                    {yeoNetworks && (
                      <CollapsibleSection
                        title="functional networks (Yeo 2011)"
                        subtitle={`${yeoNetworks.networks.length}`}
                        rightSlot={
                          <span
                            onClick={(e) => {
                              e.stopPropagation();
                              setNetworksVisible((v) => !v);
                            }}
                            className={`rounded border px-2 py-0.5 font-mono text-[9px] ${
                              networksVisible
                                ? 'border-[#cd3e4e] bg-[#cd3e4e]/10 text-white'
                                : 'border-white/20 text-white/60 hover:bg-white/5'
                            }`}
                          >
                            {networksVisible ? 'hide on brain' : 'show on brain'}
                          </span>
                        }
                      >
                        <p className="font-mono text-[10px] leading-snug text-white/50">
                          7 large-scale brain systems discovered by clustering resting-state activity
                          across 1,000 subjects. Each network has a clear function:
                        </p>
                        <div className="space-y-1 font-mono text-[10px]">
                          {yeoNetworks.networks.map((n) => (
                            <div key={n.id} className="flex items-baseline gap-2">
                              <span
                                className="mt-1 inline-block h-2 w-3 shrink-0 rounded"
                                style={{ background: n.color }}
                              />
                              <span className="flex-1 leading-snug">
                                <span className="text-white/85">{n.name}</span>{' '}
                                <span className="text-white/45">— {n.description}</span>
                              </span>
                            </div>
                          ))}
                        </div>
                        <p className="border-t border-white/10 pt-2 font-mono text-[10px] text-white/40">
                          Yeo et al. J Neurophysiol. 2011. doi:10.1152/jn.00338.2011
                        </p>
                      </CollapsibleSection>
                    )}

                    {tracts && (
                      <CollapsibleSection
                        title="white matter tracts"
                        subtitle={`${tracts.tracts.length}`}
                        rightSlot={
                          <span
                            onClick={(e) => {
                              e.stopPropagation();
                              setTractsVisible((v) => !v);
                            }}
                            className={`rounded border px-2 py-0.5 font-mono text-[9px] ${
                              tractsVisible
                                ? 'border-[#9bd2ff] bg-[#9bd2ff]/10 text-white'
                                : 'border-white/20 text-white/60 hover:bg-white/5'
                            }`}
                          >
                            {tractsVisible ? 'hide on brain' : 'show on brain'}
                          </span>
                        }
                      >
                        <p className="font-mono text-[10px] leading-snug text-white/50">
                          The major fiber bundles connecting brain regions. Each carries a specific
                          kind of information; damage produces predictable deficits.
                        </p>
                        <div className="space-y-1 font-mono text-[10px]">
                          {tracts.tracts.map((t) => (
                            <div key={t.name} className="flex items-baseline gap-2">
                              <span
                                className="mt-1 inline-block h-2 w-3 shrink-0 rounded"
                                style={{ background: t.color }}
                              />
                              <span className="flex-1 leading-snug">
                                <span className="text-white/85">{t.name}</span>{' '}
                                <span className="text-white/45">— {t.description}</span>
                              </span>
                            </div>
                          ))}
                        </div>
                        <p className="border-t border-white/10 pt-2 font-mono text-[10px] text-white/40">
                          schematic Bezier centerlines (not fiber-resolved). Catani &amp; Thiebaut de
                          Schotten. Cortex. 2008. doi:10.1016/j.cortex.2008.05.004
                        </p>
                      </CollapsibleSection>
                    )}

                    <CollapsibleSection
                      title="neuron color key"
                      subtitle="120 cells"
                    >
                      <p className="font-mono text-[10px] leading-snug text-white/50">
                        Each color = one anatomical population. Every cell is a real reconstruction
                        from neuromorpho.org rendered at its region&apos;s MNI centroid.
                      </p>
                      <div className="space-y-1 font-mono text-[10px]">
                        {[
                          ['#9bd2ff', 'V1 cortical pyramidal', 'Hubel-Wiesel'],
                          ['#7fff9b', 'Hippocampus pyramidal', 'Hebbian / LTP'],
                          ['#ff2d2d', 'CA3 pyramidal', 'Hopfield'],
                          ['#ffd86b', 'Motor cortex pyramidal', 'Precentral'],
                          ['#d99bff', 'Prefrontal pyramidal', 'Frontal Pole'],
                          ['#ff9b6b', 'Thalamic relay neuron', ''],
                          ['#ff6bd4', 'Amygdala', ''],
                          ['#6bffd4', 'Striatum', 'Caudate'],
                          ['#ff8c5e', 'Cerebellum Purkinje cell', 'schematic'],
                          ['#b5e85b', 'Dentate gyrus granule cell', ''],
                          ['#ff6bb5', 'Olfactory bulb mitral cell', 'schematic'],
                          ['#c45eff', 'Substantia nigra dopaminergic', 'schematic'],
                        ].map(([color, name, note]) => (
                          <div key={name} className="flex items-baseline gap-2">
                            <span
                              className="mt-1 inline-block h-2 w-3 shrink-0 rounded"
                              style={{ background: color }}
                            />
                            <span className="text-white/85">{name}</span>
                            {note && <span className="text-white/30">({note})</span>}
                          </div>
                        ))}
                      </div>
                      <div className="space-y-0.5 border-t border-white/10 pt-2 font-mono text-[10px] text-white/40">
                        <p>
                          neuron scale: cortical ×12, subcortical ×6 (small regions like hippocampus
                          would otherwise contain cells exceeding their real bounds)
                        </p>
                        <p>
                          &quot;schematic&quot; = MNI centroid from Mai et al. 2015 stereotaxic atlas
                          (structure not in Harvard-Oxford)
                        </p>
                        <p>
                          firing animation: pulse propagates from soma at 250 µm/ms, 600 ms ISI
                          (real APs ~500 µm/ms, ~15 ms ISI; scaled for sight)
                        </p>
                      </div>
                    </CollapsibleSection>

                    {receptors && (
                      <CollapsibleSection
                        title="neurotransmitter receptors"
                        subtitle={`${receptors.receptors.length}`}
                      >
                        <p className="font-mono text-[10px] leading-snug text-white/50">
                          Where each neurotransmitter system acts in the brain, measured with
                          radioactive tracers (PET / SPECT) in living healthy subjects. Click any
                          receptor to highlight regions where it&apos;s densely expressed and read
                          what it does + which drugs target it.
                        </p>
                        {(() => {
                          const systemOrder = ['dopamine', 'serotonin', 'GABA', 'opioid'];
                          const systemLabels: Record<string, string> = {
                            dopamine: 'Dopamine',
                            serotonin: 'Serotonin',
                            GABA: 'GABA (inhibition)',
                            opioid: 'Opioid (analgesia / reward)',
                          };
                          const grouped: Record<string, typeof receptors.receptors> = {};
                          for (const r of receptors.receptors) {
                            (grouped[r.system] ??= []).push(r);
                          }
                          return (
                            <div className="space-y-2">
                              {systemOrder
                                .filter((s) => grouped[s]?.length)
                                .map((sys) => (
                                  <div key={sys} className="space-y-1">
                                    <div className="font-mono text-[9px] uppercase tracking-widest text-white/40">
                                      {systemLabels[sys] ?? sys}
                                    </div>
                                    <div className="flex flex-wrap gap-1">
                                      {grouped[sys].map((r) => {
                                        const isActive =
                                          activeReceptor?.receptor.key === r.key;
                                        return (
                                          <button
                                            key={r.key}
                                            disabled={receptorLoading}
                                            onClick={async () => {
                                              if (isActive) {
                                                setActiveReceptor(null);
                                                return;
                                              }
                                              setReceptorLoading(true);
                                              try {
                                                setActiveReceptor(
                                                  await fetchReceptorMap(r.key),
                                                );
                                              } catch {
                                                /* ignore */
                                              } finally {
                                                setReceptorLoading(false);
                                              }
                                            }}
                                            className={`rounded border px-2 py-1 font-mono text-[10px] disabled:cursor-not-allowed disabled:opacity-50 ${
                                              isActive
                                                ? 'border-[#5eebff] bg-[#5eebff]/10 text-white'
                                                : 'border-white/20 text-white/60 hover:bg-white/5'
                                            }`}
                                            title={r.name}
                                          >
                                            {r.key}
                                          </button>
                                        );
                                      })}
                                    </div>
                                  </div>
                                ))}
                            </div>
                          );
                        })()}
                        {activeReceptor && (
                          <div className="space-y-2 rounded border border-[#5eebff]/30 bg-black/60 p-2 font-mono text-[10px] leading-snug">
                            <div>
                              <div className="text-white">{activeReceptor.receptor.name}</div>
                              <div className="text-white/40">
                                {activeReceptor.receptor.system} system · tracer{' '}
                                {activeReceptor.receptor.tracer} · n=
                                {activeReceptor.receptor.n_subjects}
                              </div>
                            </div>
                            <div>
                              <div className="text-[9px] uppercase tracking-widest text-white/40">
                                what it does
                              </div>
                              <p className="text-white/75">{activeReceptor.receptor.role}</p>
                            </div>
                            <div>
                              <div className="text-[9px] uppercase tracking-widest text-white/40">
                                pharmacology
                              </div>
                              <p className="text-white/75">
                                {activeReceptor.receptor.pharmacology}
                              </p>
                            </div>
                            <div>
                              <div className="text-[9px] uppercase tracking-widest text-white/40">
                                top regions (mean PET signal)
                              </div>
                              <ul className="mt-0.5 space-y-0.5">
                                {[
                                  ...activeReceptor.cortical,
                                  ...activeReceptor.subcortical,
                                ]
                                  .sort((a, b) => b.mean - a.mean)
                                  .slice(0, 6)
                                  .map((r) => (
                                    <li key={r.label} className="text-white/70">
                                      {r.label}{' '}
                                      <span className="text-white/40">
                                        ({r.mean.toFixed(2)})
                                      </span>
                                    </li>
                                  ))}
                              </ul>
                            </div>
                            <div className="border-t border-white/10 pt-2 text-white/40">
                              {activeReceptor.receptor.citation}
                            </div>
                          </div>
                        )}
                      </CollapsibleSection>
                    )}
                  </div>
                )}
                {clickedRegion && (
                  <div className="absolute right-4 top-4 max-w-[300px] rounded border border-white/10 bg-black/85 p-3 font-mono text-[10px] leading-tight">
                    <div className="text-white/40">destrieux region</div>
                    <div className="mb-2 break-words text-white">{clickedRegion.label}</div>
                    <div className="text-white/40">click @ MNI mm</div>
                    <div className="mb-2 text-white/80">
                      ({clickedRegion.point[0].toFixed(1)},{' '}
                      {clickedRegion.point[1].toFixed(1)},{' '}
                      {clickedRegion.point[2].toFixed(1)})
                    </div>
                    {clickedRegion.nearestModule ? (
                      <>
                        <div className="text-white/40">nearest module anchor</div>
                        <div className="text-accent">
                          {clickedRegion.nearestModule.module} ·{' '}
                          {clickedRegion.nearestModule.ho_label}
                        </div>
                        <div className="text-white/50">
                          {clickedRegion.nearestModule.distance_mm.toFixed(1)} mm away
                        </div>
                      </>
                    ) : (
                      <div className="text-white/50">no anchored module nearby</div>
                    )}
                    <button
                      onClick={() => setClickedRegion(null)}
                      className="mt-2 text-white/40 underline-offset-2 hover:text-white hover:underline"
                    >
                      dismiss
                    </button>
                  </div>
                )}
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
