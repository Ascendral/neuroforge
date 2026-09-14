'use client';

import { useEffect, useState } from 'react';

import { Landing } from '@/components/home/Landing';
import { NeuronInspector } from '@/components/inspector/NeuronInspector';
import { AISchematic } from '@/components/scales/AISchematic';
import { NodeDetail } from '@/components/scales/NodeDetail';
import { ScaleExplorer } from '@/components/scales/ScaleExplorer';
import { TimelineView } from '@/components/scales/TimelineView';
import { CollapsibleSection } from '@/components/ui/CollapsibleSection';
import { Pills } from '@/components/ui/Pills';
import {
  BrainCanvas,
  type FunctionHighlight,
  type NeuronMarker,
  type RegionIntensity,
  type TractCurve,
} from '@/components/viewer/BrainCanvas';
import type {
  AllenGeneExpressionResponse,
  AllenGeneListResponse,
  CerebellumMeshResponse,
  DifumoResponse,
  FunctionalNetworksResponse,
  HCP1065Response,
  PauliNucleiResponse,
  ScaleNode,
  ScalesGraphResponse,
  SchaeferParcelsResponse,
  TimelineResponse,
  Yeo17Response,
} from '@/lib/types';
import { NeuronCanvas } from '@/components/viewer/NeuronCanvas';
import {
  fetchBrainMesh,
  fetchBrainRegions,
  fetchCA3Sample,
  fetchCognitiveFunctions,
  fetchHippocampalSample,
  fetchNeuron,
  fetchAllenGeneExpression,
  fetchAllenGenes,
  fetchCerebellumMesh,
  fetchDifumo,
  fetchFunctionalNetworks,
  fetchHCP1065,
  fetchPauliNuclei,
  fetchReceptorMap,
  fetchReceptors,
  fetchRegionSample,
  fetchScalesGraph,
  fetchSchaeferParcels,
  fetchSubcorticalMeshes,
  fetchTimeline,
  fetchV1NeuronSample,
  fetchWhiteMatterTracts,
  fetchYeo17,
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
type ViewMode = 'home' | 'brain' | 'scales' | 'ai' | 'timeline' | 'neuron';

const VIEW_LABELS: Record<ViewMode, string> = {
  home: 'home',
  brain: 'brain',
  scales: 'scales',
  ai: 'ai schematic',
  timeline: 'timeline',
  neuron: 'neuron',
};

// Left/right hemisphere centroids of a bilateral atlas mesh, from its real
// vertices (x < 0 = left in MNI). Used to place cells inside structures whose
// atlas label is a single bilateral mask (Pauli nuclei, Diedrichsen cerebellum).
function hemiCentroids(verticesFlat: number[]): {
  left: [number, number, number] | null;
  right: [number, number, number] | null;
} {
  const acc = { l: [0, 0, 0, 0], r: [0, 0, 0, 0] };
  for (let i = 0; i + 2 < verticesFlat.length; i += 3) {
    const x = verticesFlat[i];
    const t = x < 0 ? acc.l : acc.r;
    t[0] += x;
    t[1] += verticesFlat[i + 1];
    t[2] += verticesFlat[i + 2];
    t[3] += 1;
  }
  const mean = (t: number[]): [number, number, number] | null =>
    t[3] > 0 ? [t[0] / t[3], t[1] / t[3], t[2] / t[3]] : null;
  return { left: mean(acc.l), right: mean(acc.r) };
}

interface SelectedPoint {
  id: number;
  type: number;
  parentId: number;
}

const VIEW_MODES: ViewMode[] = ['home', 'brain', 'scales', 'ai', 'timeline', 'neuron'];

export default function Page() {
  const [view, setView] = useState<ViewMode>('home');

  // Deep link: ?view=brain|scales|ai|timeline|neuron (applied after hydration to avoid an SSR mismatch)
  useEffect(() => {
    const v = new URLSearchParams(window.location.search).get('view');
    if (v && VIEW_MODES.includes(v as ViewMode)) setView(v as ViewMode);
  }, []);
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
  const [cerebellum, setCerebellum] = useState<CerebellumMeshResponse | null>(null);
  const [difumo, setDifumo] = useState<DifumoResponse | null>(null);
  const [difumoVisible, setDifumoVisible] = useState(false);
  const [yeo17, setYeo17] = useState<Yeo17Response | null>(null);
  const [yeo17Visible, setYeo17Visible] = useState(false);
  const [hcp1065, setHcp1065] = useState<HCP1065Response | null>(null);
  const [hcp1065Visible, setHcp1065Visible] = useState(false);
  const [hcp1065Group, setHcp1065Group] = useState<string | null>(null);
  const [allenGenes, setAllenGenes] = useState<AllenGeneListResponse | null>(null);
  const [activeGene, setActiveGene] = useState<AllenGeneExpressionResponse | null>(null);
  const [activeGeneLoading, setActiveGeneLoading] = useState<string | null>(null);
  const [graph, setGraph] = useState<ScalesGraphResponse | null>(null);
  const [graphError, setGraphError] = useState<string | null>(null);
  const [timeline, setTimeline] = useState<TimelineResponse | null>(null);
  const [timelineError, setTimelineError] = useState<string | null>(null);
  const [scalesLevel, setScalesLevel] = useState(2);
  const [scalesSelected, setScalesSelected] = useState<string | null>(null);
  const [nodeHighlight, setNodeHighlight] = useState<{
    name: string;
    highlights: FunctionHighlight[];
  } | null>(null);

  // Multi-scale graph: fetched once, independent of the atlas payloads.
  useEffect(() => {
    let cancelled = false;
    fetchScalesGraph()
      .then((g) => {
        if (!cancelled) setGraph(g);
      })
      .catch((err: unknown) => {
        if (!cancelled) setGraphError(err instanceof Error ? err.message : String(err));
      });
    return () => {
      cancelled = true;
    };
  }, []);

  // Timeline: fetched the first time the view is opened.
  useEffect(() => {
    if (view !== 'timeline' || timeline || timelineError) return;
    let cancelled = false;
    fetchTimeline()
      .then((t) => {
        if (!cancelled) setTimeline(t);
      })
      .catch((err: unknown) => {
        if (!cancelled) setTimelineError(err instanceof Error ? err.message : String(err));
      });
    return () => {
      cancelled = true;
    };
  }, [view, timeline, timelineError]);

  const jumpToNode = (id: string) => {
    const n = graph?.nodes.find((x) => x.id === id);
    if (!n) return;
    setScalesLevel(n.level);
    setScalesSelected(id);
    setView('scales');
  };

  const showNodeOnBrain = (n: ScaleNode) => {
    setActiveFunction(null);
    setNodeHighlight({
      name: n.name,
      highlights: n.anchors.map((a) => ({
        label: `${a.label} (${a.source})`,
        centroid_mni_mm: a.centroid_mni_mm as [number, number, number],
      })),
    });
    setView('brain');
  };

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
      fetchCerebellumMesh().catch(() => null),
      fetchDifumo().catch(() => null),
      fetchYeo17().catch(() => null),
      fetchHCP1065().catch(() => null),
      fetchAllenGenes().catch(() => null),
    ])
      .then(([mesh, regs, funs, recs, trks, sub, nets, sch, pau, cer, dif, y17, hcp, allen]) => {
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
        if (cer) setCerebellum(cer);
        if (dif) setDifumo(dif);
        if (y17) setYeo17(y17);
        if (hcp) setHcp1065(hcp);
        if (allen) setAllenGenes(allen);
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
        results: {
          neuron_id: number;
          neuron_name: string;
          archive: string;
          species: string;
          scientific_name: string;
          brain_region: string[];
          cell_type: string[];
          reference_doi: string[];
          reference_pmid: string[];
          png_url: string | null;
          source_url: string;
          swc_url: string;
        }[];
      } | null>;
    let v1Cells: unknown;
    void v1Cells;

    // Olfactory bulb has no atlas in-tree — schematic MNI centroid from
    // Mai JK, Majtanik M, Paxinos G. Atlas of the Human Brain, 4th ed.
    // Academic Press, 2015. Labeled "schematic" in the legend.
    const olfactoryL: [number, number, number] = [-5, 30, -25];
    const olfactoryR: [number, number, number] = [5, 30, -25];
    // Cerebellum and substantia nigra use REAL per-hemisphere centroids
    // derived from the Diedrichsen 2009 and Pauli 2017 atlas meshes.
    const cbHemi = cerebellum
      ? hemiCentroids(cerebellum.vertices_flat)
      : { left: null, right: null };
    const snc = pauli?.nuclei.find((n) => n.abbrev === 'SNc');
    const snHemi = snc ? hemiCentroids(snc.vertices_flat) : { left: null, right: null };

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
        const SCALE_CORTICAL = 0.012; // V1, motor, prefrontal
        const SCALE_SUBCORTICAL = 0.006; // hippocampus, amygdala, thalamus, striatum
        const SCALE_SCHEMATIC = 0.008; // cerebellum, olfactory, SN, dentate

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

        // Explicit-centroid variant: used for the olfactory bulb (schematic,
        // Mai 2015) and for cerebellum / SNc (real per-hemisphere centroids
        // computed from the atlas meshes). Cells are skipped, not faked, if
        // the mesh has not arrived.
        const pushAt = (
          sample: { results: NeuronMarker['neuron'][] } | null,
          leftCentroid: [number, number, number] | null,
          color: string,
          module: string,
          scale: number,
          rightCentroid?: [number, number, number] | null,
        ) => {
          if (!sample || !leftCentroid) return;
          sample.results.forEach((n, i) => {
            const c = rightCentroid && i % 2 === 1 ? rightCentroid : leftCentroid;
            out.push({ neuron: n, centroid_mni_mm: c, module, color, scale });
          });
        };

        push(
          v1 as { results: NeuronMarker['neuron'][] } | null,
          'Intracalcarine Cortex',
          '#9bd2ff',
          'hubel_wiesel',
          SCALE_CORTICAL,
        );
        push(
          hippo as { results: NeuronMarker['neuron'][] } | null,
          'Left Hippocampus',
          '#7fff9b',
          'hebbian',
          SCALE_SUBCORTICAL,
          'Right Hippocampus',
        );
        push(
          ca3 as { results: NeuronMarker['neuron'][] } | null,
          'Left Hippocampus',
          '#ff2d2d',
          'hopfield',
          SCALE_SUBCORTICAL,
          'Right Hippocampus',
        );
        push(
          motor as { results: NeuronMarker['neuron'][] } | null,
          'Precentral Gyrus',
          '#ffd86b',
          'motor_cortex',
          SCALE_CORTICAL,
        );
        push(
          pfc as { results: NeuronMarker['neuron'][] } | null,
          'Frontal Pole',
          '#d99bff',
          'prefrontal',
          SCALE_CORTICAL,
        );
        push(
          thal as { results: NeuronMarker['neuron'][] } | null,
          'Left Thalamus',
          '#ff9b6b',
          'thalamus',
          SCALE_SUBCORTICAL,
          'Right Thalamus',
        );
        push(
          amyg as { results: NeuronMarker['neuron'][] } | null,
          'Left Amygdala',
          '#ff6bd4',
          'amygdala',
          SCALE_SUBCORTICAL,
          'Right Amygdala',
        );
        push(
          stri as { results: NeuronMarker['neuron'][] } | null,
          'Left Caudate',
          '#6bffd4',
          'striatum',
          SCALE_SUBCORTICAL,
          'Right Caudate',
        );

        // Structures without a Harvard-Oxford label.
        pushAt(
          purk as { results: NeuronMarker['neuron'][] } | null,
          cbHemi.left,
          '#ff8c5e',
          'cerebellum_purkinje',
          SCALE_SCHEMATIC,
          cbHemi.right,
        );
        push(
          dg as { results: NeuronMarker['neuron'][] } | null,
          'Left Hippocampus',
          '#b5e85b',
          'dentate_granule',
          SCALE_SUBCORTICAL,
          'Right Hippocampus',
        );
        pushAt(
          olf as { results: NeuronMarker['neuron'][] } | null,
          olfactoryL,
          '#ff6bb5',
          'olfactory_mitral',
          SCALE_SCHEMATIC,
          olfactoryR,
        );
        pushAt(
          sn as { results: NeuronMarker['neuron'][] } | null,
          snHemi.left,
          '#c45eff',
          'substantia_nigra_dopa',
          SCALE_SUBCORTICAL,
          snHemi.right,
        );

        setMarkers(out);
      })
      .catch(() => {
        // Sample fetches are non-fatal; brain still renders without them.
      });

    return () => {
      cancelled = true;
    };
  }, [regions, pauli, cerebellum]);

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
          (c[0] - info.point[0]) ** 2 + (c[1] - info.point[1]) ** 2 + (c[2] - info.point[2]) ** 2,
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
      <main className="flex h-screen w-screen flex-col bg-canvas text-white">
        <header className="hairline-b flex items-center justify-between gap-6 px-6 py-3">
          <div className="flex items-center gap-6">
            <div className="flex flex-col gap-1">
              <span className="kicker">ascendral</span>
              <h1 className="display text-white" style={{ fontSize: 22 }}>
                NeuroForge
              </h1>
            </div>
            <span className="hidden text-[12.5px] text-white/45 xl:block">
              brain ↔ AI on one ladder · 5 scales · 9 live models · every claim cited
            </span>
          </div>
          <div className="flex items-center gap-5">
            <div className="hidden text-[12.5px] text-white/50 lg:block">
              {view === 'scales' && graph && (
                <>
                  <span className="text-white">
                    {graph.nodes.filter((n) => n.side === 'brain').length}
                  </span>{' '}
                  brain ·{' '}
                  <span className="text-white">
                    {graph.nodes.filter((n) => n.side === 'ai').length}
                  </span>{' '}
                  AI nodes · {graph.nodes.reduce((s, n) => s + n.analogs.length, 0)} bridges
                </>
              )}
              {view === 'neuron' && neuron && (
                <>
                  <span className="text-white">{neuron.neuron_name}</span>
                  {' · '}
                  <span>{neuron.species}</span>
                  {' · '}
                  <span>{neuron.brain_region.join(' / ')}</span>
                </>
              )}
              {view === 'brain' && brain && (
                <>
                  fsaverage5 ·{' '}
                  {(brain.left.vertex_count + brain.right.vertex_count).toLocaleString()} vertices
                  {markers.length > 0 && (
                    <>
                      {' · '}
                      <span className="text-white">{markers.length}</span> real neurons at atlas
                      centroids
                    </>
                  )}
                </>
              )}
            </div>
            <Pills
              options={['home', 'brain', 'scales', 'ai', 'timeline', 'neuron'] as const}
              value={view}
              onChange={(v) => setView(v)}
              label={(v) => VIEW_LABELS[v]}
              size="sm"
            />
          </div>
        </header>

        <div className="flex flex-1 overflow-hidden">
          <div className="relative flex-1">
            {view === 'home' && <Landing graph={graph} onNavigate={(v) => setView(v)} />}
            {view === 'brain' && (
              <>
                {brainError && (
                  <div className="absolute inset-0 flex items-center justify-center px-6 text-center text-[13px] text-accent">
                    error fetching brain mesh: {brainError}
                  </div>
                )}
                {!brain && !brainError && (
                  <div className="absolute inset-0 flex items-center justify-center text-[13px] text-white/40">
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
                    cerebellum={cerebellum}
                    difumoComponents={difumoVisible && difumo ? difumo.components : []}
                    yeo17Networks={yeo17Visible && yeo17 ? yeo17.networks : []}
                    hcpTracts={
                      hcp1065Visible && hcp1065
                        ? hcp1065Group
                          ? hcp1065.tracts.filter((t) => t.group === hcp1065Group)
                          : hcp1065.tracts
                        : []
                    }
                    onRegionClick={handleRegionClick}
                    functionHighlights={
                      activeFunction
                        ? (activeFunction.region_centroids
                            .filter((r) => r.found && r.centroid_mni_mm)
                            .map((r) => ({
                              label: r.label,
                              centroid_mni_mm: r.centroid_mni_mm as [number, number, number],
                            })) as FunctionHighlight[])
                        : nodeHighlight
                          ? nodeHighlight.highlights
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
                      activeGene
                        ? (activeGene.regions
                            .filter((r) => r.centroid_mni_mm && r.centroid_mni_mm.length === 3)
                            .map(
                              (r) =>
                                ({
                                  label: r.label,
                                  centroid_mni_mm: r.centroid_mni_mm as [number, number, number],
                                  normalized: r.expression_normalized,
                                }) as RegionIntensity,
                            ) as RegionIntensity[])
                        : activeReceptor
                          ? ([...activeReceptor.cortical, ...activeReceptor.subcortical]
                              .filter((r) => r.centroid_mni_mm)
                              .map(
                                (r) =>
                                  ({
                                    label: r.label,
                                    centroid_mni_mm: r.centroid_mni_mm as [number, number, number],
                                    normalized: r.normalized,
                                  }) as RegionIntensity,
                              ) as RegionIntensity[])
                          : []
                    }
                    intensityColor={activeGene ? '#ff66cc' : '#5eebff'}
                  />
                )}
                {nodeHighlight && !activeFunction && (
                  <div className="float-panel rise absolute bottom-4 right-4 max-w-[320px] p-4 text-[12.5px]">
                    <div className="text-white/40">highlighting atlas anchors of</div>
                    <div className="text-white">{nodeHighlight.name}</div>
                    <ul className="mt-1 text-white/60">
                      {nodeHighlight.highlights.map((h) => (
                        <li key={h.label}>{h.label}</li>
                      ))}
                    </ul>
                    <div className="mt-1 flex gap-3">
                      <button
                        onClick={() => setView('scales')}
                        className="text-[#ffe45e] hover:underline"
                      >
                        back to scales
                      </button>
                      <button
                        onClick={() => setNodeHighlight(null)}
                        className="text-white/40 hover:text-white"
                      >
                        dismiss
                      </button>
                    </div>
                  </div>
                )}
                {functions && view === 'brain' && (
                  <div className="absolute left-5 top-5 w-[320px] max-h-[calc(100vh-6rem)] space-y-3 overflow-y-auto pr-1">
                    <CollapsibleSection
                      title="cognitive functions"
                      subtitle={`${functions.functions.length}`}
                      defaultOpen
                    >
                      <p className="text-[13px] leading-snug text-white/55">
                        Click any function. Brain regions associated with it will glow yellow. Each
                        entry cites its foundational discovery paper.
                      </p>
                      <div className="flex flex-wrap gap-1">
                        {functions.functions.map((f) => {
                          const isActive = activeFunction?.name === f.name;
                          return (
                            <button
                              key={f.name}
                              onClick={() => setActiveFunction(isActive ? null : f)}
                              className={`rounded border px-2 py-1 text-[12.5px] ${
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
                        <div className="glass tile rise p-3.5 text-[12.5px] leading-snug">
                          <div className="mb-1 text-white">{activeFunction.name}</div>
                          <div className="mb-2 text-white/60">{activeFunction.description}</div>
                          <div className="mb-1 text-white/40">
                            regions ({activeFunction.region_centroids.filter((r) => r.found).length}
                            /{activeFunction.atlas_labels.length}):
                          </div>
                          <ul className="mb-2 space-y-0.5">
                            {activeFunction.region_centroids.map((r) => (
                              <li
                                key={r.label}
                                className={r.found ? 'text-white/80' : 'text-white/30 line-through'}
                              >
                                {r.label}
                              </li>
                            ))}
                          </ul>
                          <div className="hairline-t pt-3 text-[12px] text-white/40">
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
                            className={`chip ${pauliVisible ? 'chip-on' : ''}`}
                          >
                            {pauliVisible ? 'hide on brain' : 'show on brain'}
                          </span>
                        }
                      >
                        <p className="text-[13px] leading-snug text-white/55">
                          16 deep subcortical nuclei. <span className="text-white/80">VTA</span>{' '}
                          makes the dopamine for reward; <span className="text-white/80">SNc</span>{' '}
                          makes the dopamine for movement (degenerates in Parkinson&apos;s).{' '}
                          <span className="text-white/80">GPi/GPe</span> are the basal ganglia
                          output; <span className="text-white/80">HTH</span> is the hypothalamus
                          (sleep, appetite, hormones); <span className="text-white/80">MN</span> is
                          the mammillary nucleus in the Papez memory circuit.
                        </p>
                        <div className="space-y-1 text-[12.5px]">
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
                        <p className="hairline-t pt-3 text-[11.5px] leading-snug text-white/40">
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
                            className={`chip ${schaeferVisible ? 'chip-on' : ''}`}
                          >
                            {schaeferVisible ? 'hide on brain' : 'show on brain'}
                          </span>
                        }
                      >
                        <p className="text-[13px] leading-snug text-white/55">
                          The cortex split into 100 fine-grained parcels, each colored by which of
                          the 7 Yeo functional networks it belongs to. Useful for seeing functional
                          subdivisions within each network.
                        </p>
                        <p className="text-[12px] text-white/45">
                          Schaefer et al. Cereb Cortex. 2018. doi:10.1093/cercor/bhx179
                        </p>
                      </CollapsibleSection>
                    )}

                    {difumo && (
                      <CollapsibleSection
                        title="DiFuMo 64 functional dictionary"
                        subtitle={`${difumo.n_components}`}
                        rightSlot={
                          <span
                            onClick={(e) => {
                              e.stopPropagation();
                              setDifumoVisible((v) => !v);
                            }}
                            className={`chip ${difumoVisible ? 'chip-on' : ''}`}
                          >
                            {difumoVisible ? 'hide on brain' : 'show on brain'}
                          </span>
                        }
                      >
                        <p className="text-[13px] leading-snug text-white/55">
                          64 fine-grained &quot;functional modes&quot; learned from 2,192 fMRI scans
                          (HCP, OASIS, Connectome). Each component is a coactivating brain region
                          with a plain-language anatomical name; spheres are colored by which Yeo
                          network they belong to.
                        </p>
                        <div className="max-h-[200px] space-y-1 overflow-y-auto pr-1 text-[12.5px]">
                          {difumo.components.map((c) => (
                            <div key={c.component_id} className="flex items-baseline gap-2">
                              <span
                                className="inline-block h-2 w-3 rounded"
                                style={{ background: c.color }}
                              />
                              <span className="text-white/80">{c.name}</span>
                              <span className="text-white/40">{c.yeo_network_name}</span>
                            </div>
                          ))}
                        </div>
                        <p className="hairline-t pt-3 text-[11.5px] leading-snug text-white/40">
                          Dadi et al. NeuroImage. 2020. doi:10.1016/j.neuroimage.2020.117126
                        </p>
                      </CollapsibleSection>
                    )}

                    {yeo17 && (
                      <CollapsibleSection
                        title="Yeo 17-network (finer)"
                        subtitle={`${yeo17.networks.length}`}
                        rightSlot={
                          <span
                            onClick={(e) => {
                              e.stopPropagation();
                              setYeo17Visible((v) => !v);
                            }}
                            className={`chip ${yeo17Visible ? 'chip-on' : ''}`}
                          >
                            {yeo17Visible ? 'hide on brain' : 'show on brain'}
                          </span>
                        }
                      >
                        <p className="text-[13px] leading-snug text-white/55">
                          The 17-network split from the same Yeo 2011 paper. Each of the 7 large
                          networks is subdivided into 2-3 sub-networks (e.g. Default Mode A/B/C,
                          Visual Central/Peripheral). Colors come straight from the published LUT.
                        </p>
                        <div className="space-y-1 text-[12.5px]">
                          {yeo17.networks.map((n) => (
                            <div key={n.network_id} className="flex items-baseline gap-2">
                              <span
                                className="inline-block h-2 w-3 rounded"
                                style={{ background: n.color }}
                              />
                              <span className="text-white/80">{n.short_name}</span>
                              <span className="text-white/50">{n.full_name}</span>
                            </div>
                          ))}
                        </div>
                        <p className="hairline-t pt-3 text-[11.5px] leading-snug text-white/40">
                          Yeo et al. J Neurophysiol. 2011. doi:10.1152/jn.00338.2011
                        </p>
                      </CollapsibleSection>
                    )}

                    {hcp1065 && (
                      <CollapsibleSection
                        title="HCP-1065 white-matter tracts"
                        subtitle={`${hcp1065.tracts.length}`}
                        rightSlot={
                          <span
                            onClick={(e) => {
                              e.stopPropagation();
                              setHcp1065Visible((v) => !v);
                            }}
                            className={`chip ${hcp1065Visible ? 'chip-on' : ''}`}
                          >
                            {hcp1065Visible ? 'hide on brain' : 'show on brain'}
                          </span>
                        }
                      >
                        <p className="text-[13px] leading-snug text-white/55">
                          80 named fiber bundles averaged over 1,065 HCP young-adult subjects. Each
                          tract is rendered as the centerline of its empirical voxel-occupancy
                          distribution (PCA-binned mean per length-bin). Click a group to filter.
                        </p>
                        <div className="flex flex-wrap gap-1">
                          <button
                            onClick={() => setHcp1065Group(null)}
                            className={`chip ${hcp1065Group === null ? 'chip-on' : ''}`}
                          >
                            all
                          </button>
                          {Array.from(new Set(hcp1065.tracts.map((t) => t.group))).map((g) => {
                            const color =
                              hcp1065.tracts.find((t) => t.group === g)?.color ?? '#888';
                            const isActive = hcp1065Group === g;
                            return (
                              <button
                                key={g}
                                onClick={() => setHcp1065Group(isActive ? null : g)}
                                className={`chip ${isActive ? 'chip-on' : ''}`}
                              >
                                <span
                                  className="inline-block h-2 w-2 rounded"
                                  style={{ background: color }}
                                />
                                {g}
                              </button>
                            );
                          })}
                        </div>
                        <p className="hairline-t pt-3 text-[11.5px] leading-snug text-white/40">
                          Yeh et al. NeuroImage. 2018. doi:10.1016/j.neuroimage.2018.05.027
                          {' · '}
                          Atlas: doi:10.5281/zenodo.3627772
                        </p>
                      </CollapsibleSection>
                    )}

                    {allenGenes && (
                      <CollapsibleSection
                        title="Allen brain gene expression"
                        subtitle={`${allenGenes.genes.length} curated`}
                      >
                        <p className="text-[13px] leading-snug text-white/55">{allenGenes.note}</p>
                        {!allenGenes.available && (
                          <p className="tile bg-amber-500/10 p-3 text-[12px] text-amber-200">
                            Cache not built yet. Run the abagen pipeline to enable this layer.
                          </p>
                        )}
                        {allenGenes.available && (
                          <div className="space-y-2">
                            {Array.from(new Set(allenGenes.genes.map((g) => g.system))).map(
                              (system) => (
                                <div key={system}>
                                  <div className="meta-xs mb-1.5">{system}</div>
                                  <div className="flex flex-wrap gap-1">
                                    {allenGenes.genes
                                      .filter((g) => g.system === system)
                                      .map((g) => {
                                        const isActive = activeGene?.gene.symbol === g.symbol;
                                        const isLoading = activeGeneLoading === g.symbol;
                                        return (
                                          <button
                                            key={g.symbol}
                                            disabled={isLoading}
                                            onClick={() => {
                                              if (isActive) {
                                                setActiveGene(null);
                                                return;
                                              }
                                              setActiveGeneLoading(g.symbol);
                                              fetchAllenGeneExpression(g.symbol)
                                                .then((d) => setActiveGene(d))
                                                .catch(() => setActiveGene(null))
                                                .finally(() => setActiveGeneLoading(null));
                                            }}
                                            title={g.description}
                                            className={`rounded border px-2 py-0.5 text-[12.5px] ${
                                              isActive
                                                ? 'border-[#ff66cc] bg-[#ff66cc]/15 text-white'
                                                : 'border-white/20 text-white/70 hover:bg-white/5'
                                            } ${isLoading ? 'opacity-40' : ''}`}
                                          >
                                            {g.symbol}
                                          </button>
                                        );
                                      })}
                                  </div>
                                </div>
                              ),
                            )}
                            {activeGene && (
                              <div className="glass tile rise p-3.5 text-[12.5px] leading-snug">
                                <div className="mb-1 text-white">
                                  {activeGene.gene.symbol} · {activeGene.gene.role}
                                </div>
                                <p className="mb-2 text-white/70">{activeGene.gene.description}</p>
                                <div className="text-white/40">
                                  raw range: {activeGene.raw_min.toFixed(2)} →{' '}
                                  {activeGene.raw_max.toFixed(2)} (z-scored microarray) ·{' '}
                                  {activeGene.regions.length} regions
                                </div>
                              </div>
                            )}
                          </div>
                        )}
                        <p className="hairline-t pt-3 text-[11.5px] leading-snug text-white/40">
                          {allenGenes.citation}
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
                            className={`chip ${networksVisible ? 'chip-on' : ''}`}
                          >
                            {networksVisible ? 'hide on brain' : 'show on brain'}
                          </span>
                        }
                      >
                        <p className="text-[13px] leading-snug text-white/55">
                          7 large-scale brain systems discovered by clustering resting-state
                          activity across 1,000 subjects. Each network has a clear function:
                        </p>
                        <div className="space-y-1.5 text-[12.5px]">
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
                        <p className="hairline-t pt-3 text-[11.5px] leading-snug text-white/40">
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
                            className={`chip ${tractsVisible ? 'chip-on' : ''}`}
                          >
                            {tractsVisible ? 'hide on brain' : 'show on brain'}
                          </span>
                        }
                      >
                        <p className="text-[13px] leading-snug text-white/55">
                          The major fiber bundles connecting brain regions. Each carries a specific
                          kind of information; damage produces predictable deficits.
                        </p>
                        <div className="space-y-1.5 text-[12.5px]">
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
                        <p className="hairline-t pt-3 text-[11.5px] leading-snug text-white/40">
                          schematic Bezier centerlines (not fiber-resolved). Catani &amp; Thiebaut
                          de Schotten. Cortex. 2008. doi:10.1016/j.cortex.2008.05.004
                        </p>
                      </CollapsibleSection>
                    )}

                    <CollapsibleSection title="neuron color key" subtitle="120 cells">
                      <p className="text-[13px] leading-snug text-white/55">
                        Each color = one anatomical population. Every cell is a real reconstruction
                        from neuromorpho.org rendered at its region&apos;s MNI centroid.
                      </p>
                      <div className="space-y-1.5 text-[12.5px]">
                        {[
                          ['#9bd2ff', 'V1 cortical pyramidal', 'Hubel-Wiesel'],
                          ['#7fff9b', 'Hippocampus pyramidal', 'Hebbian / LTP'],
                          ['#ff2d2d', 'CA3 pyramidal', 'Hopfield'],
                          ['#ffd86b', 'Motor cortex pyramidal', 'Precentral'],
                          ['#d99bff', 'Prefrontal pyramidal', 'Frontal Pole'],
                          ['#ff9b6b', 'Thalamic relay neuron', ''],
                          ['#ff6bd4', 'Amygdala', ''],
                          ['#6bffd4', 'Striatum', 'Caudate'],
                          ['#ff8c5e', 'Cerebellum Purkinje cell', 'Diedrichsen 2009 mesh'],
                          ['#b5e85b', 'Dentate gyrus granule cell', ''],
                          ['#ff6bb5', 'Olfactory bulb mitral cell', 'schematic'],
                          ['#c45eff', 'Substantia nigra dopaminergic', 'Pauli 2017 SNc mesh'],
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
                      <div className="hairline-t space-y-1 pt-3 text-[11.5px] leading-snug text-white/40">
                        <p>
                          neuron scale: cortical ×12, subcortical ×6 (small regions like hippocampus
                          would otherwise contain cells exceeding their real bounds)
                        </p>
                        <p>
                          &quot;schematic&quot; = MNI centroid from Mai et al. 2015 stereotaxic
                          atlas (olfactory bulb only — no atlas in-tree). Cerebellum and SNc cells
                          sit at per-hemisphere centroids computed from the real Diedrichsen / Pauli
                          meshes.
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
                        <p className="text-[13px] leading-snug text-white/55">
                          Where each neurotransmitter system acts in the brain, measured with
                          radioactive tracers (PET / SPECT) in living healthy subjects. Click any
                          receptor to highlight regions where it&apos;s densely expressed and read
                          what it does + which drugs target it.
                        </p>
                        {(() => {
                          const systemOrder = [
                            'dopamine',
                            'norepinephrine',
                            'serotonin',
                            'glutamate',
                            'GABA',
                            'acetylcholine',
                            'cannabinoid',
                            'opioid',
                            'histamine',
                          ];
                          const systemLabels: Record<string, string> = {
                            dopamine: 'Dopamine (reward, movement)',
                            norepinephrine: 'Norepinephrine (arousal, attention)',
                            serotonin: 'Serotonin (mood)',
                            glutamate: 'Glutamate (excitation, memory)',
                            GABA: 'GABA (inhibition)',
                            acetylcholine: 'Acetylcholine (attention, memory)',
                            cannabinoid: 'Cannabinoid (THC target)',
                            opioid: 'Opioid (analgesia, reward)',
                            histamine: 'Histamine (wakefulness)',
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
                                    <div className="meta-xs">{systemLabels[sys] ?? sys}</div>
                                    <div className="flex flex-wrap gap-1">
                                      {grouped[sys].map((r) => {
                                        const isActive = activeReceptor?.receptor.key === r.key;
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
                                                setActiveReceptor(await fetchReceptorMap(r.key));
                                              } catch {
                                                /* ignore */
                                              } finally {
                                                setReceptorLoading(false);
                                              }
                                            }}
                                            className={`rounded border px-2 py-1 text-[12.5px] disabled:cursor-not-allowed disabled:opacity-50 ${
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
                          <div className="glass tile rise space-y-3 p-3.5 text-[12.5px] leading-snug">
                            <div>
                              <div className="text-white">{activeReceptor.receptor.name}</div>
                              <div className="text-white/40">
                                {activeReceptor.receptor.system} system · tracer{' '}
                                {activeReceptor.receptor.tracer} · n=
                                {activeReceptor.receptor.n_subjects}
                              </div>
                            </div>
                            <div>
                              <div className="meta-xs">what it does</div>
                              <p className="text-white/75">{activeReceptor.receptor.role}</p>
                            </div>
                            <div>
                              <div className="meta-xs">pharmacology</div>
                              <p className="text-white/75">
                                {activeReceptor.receptor.pharmacology}
                              </p>
                            </div>
                            <div>
                              <div className="meta-xs">top regions (mean PET signal)</div>
                              <ul className="mt-0.5 space-y-0.5">
                                {[...activeReceptor.cortical, ...activeReceptor.subcortical]
                                  .sort((a, b) => b.mean - a.mean)
                                  .slice(0, 6)
                                  .map((r) => (
                                    <li key={r.label} className="text-white/70">
                                      {r.label}{' '}
                                      <span className="text-white/40">({r.mean.toFixed(2)})</span>
                                    </li>
                                  ))}
                              </ul>
                            </div>
                            <div className="hairline-t pt-3 text-[12px] text-white/40">
                              {activeReceptor.receptor.citation}
                            </div>
                          </div>
                        )}
                      </CollapsibleSection>
                    )}
                  </div>
                )}
                {clickedRegion && (
                  <div className="float-panel rise absolute right-4 top-4 max-w-[300px] p-4 text-[12.5px] leading-snug">
                    <div className="text-white/40">destrieux region</div>
                    <div className="mb-2 break-words text-white">{clickedRegion.label}</div>
                    <div className="text-white/40">click @ MNI mm</div>
                    <div className="mb-2 text-white/80">
                      ({clickedRegion.point[0].toFixed(1)}, {clickedRegion.point[1].toFixed(1)},{' '}
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
                      className="mt-2 text-white/45 underline-offset-4 hover:text-white hover:underline"
                    >
                      dismiss
                    </button>
                  </div>
                )}
              </>
            )}
            {view === 'scales' && (
              <>
                {graphError && (
                  <div className="absolute inset-0 flex items-center justify-center px-6 text-center text-[13px] text-accent">
                    error fetching scale graph: {graphError}
                  </div>
                )}
                {!graph && !graphError && (
                  <div className="absolute inset-0 flex items-center justify-center text-[13px] text-white/40">
                    loading multi-scale graph…
                  </div>
                )}
                {graph && (
                  <ScaleExplorer
                    graph={graph}
                    level={scalesLevel}
                    selectedId={scalesSelected}
                    onLevel={setScalesLevel}
                    onSelect={setScalesSelected}
                  />
                )}
              </>
            )}
            {view === 'ai' && (
              <>
                {graphError && (
                  <div className="absolute inset-0 flex items-center justify-center px-6 text-center text-[13px] text-accent">
                    error fetching scale graph: {graphError}
                  </div>
                )}
                {!graph && !graphError && (
                  <div className="absolute inset-0 flex items-center justify-center text-[13px] text-white/40">
                    loading AI schematic…
                  </div>
                )}
                {graph && (
                  <AISchematic
                    graph={graph}
                    selectedId={scalesSelected}
                    onSelect={(id) => setScalesSelected(id === scalesSelected ? null : id)}
                  />
                )}
              </>
            )}
            {view === 'timeline' && (
              <>
                {timelineError && (
                  <div className="absolute inset-0 flex items-center justify-center px-6 text-center text-[13px] text-accent">
                    error fetching timeline: {timelineError}
                  </div>
                )}
                {!timeline && !timelineError && (
                  <div className="absolute inset-0 flex items-center justify-center text-[13px] text-white/40">
                    loading research timeline…
                  </div>
                )}
                {timeline && <TimelineView timeline={timeline} graph={graph} onJump={jumpToNode} />}
              </>
            )}
            {view === 'neuron' && (
              <>
                {neuronError && (
                  <div className="absolute inset-0 flex items-center justify-center px-6 text-center text-[13px] text-accent">
                    error fetching neuron {neuronId}: {neuronError}
                  </div>
                )}
                {!neuron && !neuronError && (
                  <div className="absolute inset-0 flex items-center justify-center text-[13px] text-white/40">
                    loading neuron {neuronId} from neuromorpho.org…
                  </div>
                )}
                {neuron && <NeuronCanvas neuron={neuron} onSegmentClick={setSelected} />}
              </>
            )}
          </div>

          {(view === 'brain' || view === 'neuron') && neuron && (
            <NeuronInspector neuron={neuron} selected={selected} />
          )}
          {(view === 'scales' || view === 'ai') &&
            graph &&
            scalesSelected &&
            (() => {
              const n = graph.nodes.find((x) => x.id === scalesSelected);
              return n ? (
                <NodeDetail
                  graph={graph}
                  node={n}
                  onSelect={(id) => {
                    const t = graph.nodes.find((x) => x.id === id);
                    if (t) setScalesLevel(t.level);
                    setScalesSelected(id);
                  }}
                  onShowOnBrain={showNodeOnBrain}
                  onClose={() => setScalesSelected(null)}
                />
              ) : null;
            })()}
        </div>
      </main>
    </NeuronSelectionCtx.Provider>
  );
}
