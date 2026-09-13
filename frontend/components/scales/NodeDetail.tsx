'use client';

import { useEffect, useState } from 'react';

import { DopaminePanel } from '@/components/inspector/DopaminePanel';
import { HebbianPanel } from '@/components/inspector/HebbianPanel';
import { HHPanel } from '@/components/inspector/HHPanel';
import { HopfieldPanel } from '@/components/inspector/HopfieldPanel';
import { HubelWieselPanel } from '@/components/inspector/HubelWieselPanel';
import { McCullochPittsPanel } from '@/components/inspector/McCullochPittsPanel';
import { ModernHopfieldPanel } from '@/components/inspector/ModernHopfieldPanel';
import { STDPPanel } from '@/components/inspector/STDPPanel';
import { SynapsePanel } from '@/components/inspector/SynapsePanel';
import { fetchRegionSample } from '@/lib/api';
import { useNeuronSelection } from '@/lib/neuron-context';
import type { CiteModel, NeuronSearchResponse, ScaleNode, ScalesGraphResponse } from '@/lib/types';

import { STRENGTH_COLOR, STRENGTH_LABEL } from './strength';

interface NodeDetailProps {
  graph: ScalesGraphResponse;
  node: ScaleNode;
  onSelect: (id: string) => void;
  onShowOnBrain: (node: ScaleNode) => void;
  onClose: () => void;
}

function Cites({ cites }: { cites: CiteModel[] }) {
  return (
    <ul className="space-y-1">
      {cites.map((c, i) => (
        <li key={i} className="text-[10px] leading-snug text-white/50">
          {c.text}{' '}
          {c.doi && (
            <a
              href={`https://doi.org/${c.doi}`}
              target="_blank"
              rel="noreferrer"
              className="text-white/70 underline-offset-2 hover:underline"
            >
              doi:{c.doi}
            </a>
          )}
        </li>
      ))}
    </ul>
  );
}

function Widget({ id }: { id: string }) {
  switch (id) {
    case 'hh':
      return <HHPanel />;
    case 'stdp':
      return <STDPPanel />;
    case 'hebbian':
      return <HebbianPanel />;
    case 'hopfield':
      return <HopfieldPanel />;
    case 'modern_hopfield':
      return <ModernHopfieldPanel />;
    case 'dopamine_rpe':
      return <DopaminePanel />;
    case 'synapse':
      return <SynapsePanel />;
    case 'v1':
      return <HubelWieselPanel />;
    case 'mcp':
      return <McCullochPittsPanel />;
    default:
      return null;
  }
}

function RealCells({ query }: { query: Record<string, string> }) {
  const [sample, setSample] = useState<NeuronSearchResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const selection = useNeuronSelection();
  useEffect(() => {
    let cancelled = false;
    setSample(null);
    setError(null);
    fetchRegionSample(query.region, { cell_type: query.cell_type || undefined, size: 5 })
      .then((s) => {
        if (!cancelled) setSample(s);
      })
      .catch((e: unknown) => {
        if (!cancelled) setError(e instanceof Error ? e.message : String(e));
      });
    return () => {
      cancelled = true;
    };
  }, [query.region, query.cell_type]);
  return (
    <div className="space-y-1">
      <div className="flex items-baseline justify-between">
        <span className="font-mono text-[9px] uppercase tracking-widest text-white/40">
          real reconstructions
        </span>
        {sample && (
          <span className="font-mono text-[9px] text-white/30">
            {sample.total_matching.toLocaleString()} on neuromorpho.org
          </span>
        )}
      </div>
      {error && <p className="font-mono text-[10px] text-accent">{error}</p>}
      {!sample && !error && (
        <p className="font-mono text-[10px] text-white/40">querying neuromorpho.org…</p>
      )}
      {sample && (
        <ul className="space-y-1 font-mono text-[10px]">
          {sample.results.map((n) => (
            <li key={n.neuron_id} className="flex items-baseline gap-2">
              <button
                onClick={() => selection?.selectNeuron(n.neuron_id)}
                className="text-left text-white hover:text-accent"
                title="render this neuron in 3D"
              >
                {n.neuron_name}
              </button>
              <span className="text-white/40">
                {n.species} · {n.archive}
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export function NodeDetail({ graph, node, onSelect, onShowOnBrain, onClose }: NodeDetailProps) {
  const byId = new Map(graph.nodes.map((n) => [n.id, n]));
  const level = graph.levels.find((l) => l.level === node.level);
  const parent = node.parent ? byId.get(node.parent) : null;
  const backlinks = node.analog_of.map((id) => byId.get(id)).filter((n): n is ScaleNode => !!n);

  return (
    <aside className="flex h-full w-[400px] shrink-0 flex-col gap-4 overflow-y-auto border-l border-white/10 bg-black p-5 text-sm">
      <div className="flex items-start justify-between gap-2">
        <div>
          <div className="font-mono text-[10px] uppercase tracking-widest text-white/40">
            {node.side} · level {node.level} ·{' '}
            {node.side === 'brain' ? level?.brain_name : level?.ai_name}
          </div>
          <h2 className="text-base font-semibold leading-tight text-white">{node.name}</h2>
        </div>
        <button onClick={onClose} className="font-mono text-[10px] text-white/40 hover:text-white">
          close
        </button>
      </div>

      <div className="flex flex-wrap gap-1 font-mono text-[10px]">
        {parent && (
          <button
            onClick={() => onSelect(parent.id)}
            className="rounded border border-white/20 px-2 py-0.5 text-white/60 hover:bg-white/5"
          >
            ↖ zoom out · {parent.name}
          </button>
        )}
        {node.children.map((cid) => {
          const c = byId.get(cid);
          if (!c) return null;
          return (
            <button
              key={cid}
              onClick={() => onSelect(cid)}
              className="rounded border border-white/20 px-2 py-0.5 text-white/60 hover:bg-white/5"
            >
              ↘ zoom in · {c.name}
            </button>
          );
        })}
        {node.anchors.length > 0 && (
          <button
            onClick={() => onShowOnBrain(node)}
            className="rounded border border-[#ffe45e]/60 px-2 py-0.5 text-[#ffe45e] hover:bg-[#ffe45e]/10"
          >
            show on brain ({node.anchors.length})
          </button>
        )}
      </div>

      <section className="space-y-2 font-mono text-xs">
        <div>
          <div className="text-[9px] uppercase tracking-widest text-white/40">what it is</div>
          <p className="leading-snug text-white/80">{node.description}</p>
        </div>
        <div>
          <div className="text-[9px] uppercase tracking-widest text-white/40">what it does</div>
          <p className="leading-snug text-white/80">{node.function}</p>
        </div>
        <div>
          <div className="text-[9px] uppercase tracking-widest text-white/40">how</div>
          <p className="leading-snug text-white/80">{node.mechanism}</p>
        </div>
      </section>

      {node.facts.length > 0 && (
        <section className="space-y-1 font-mono text-[10px]">
          <div className="text-[9px] uppercase tracking-widest text-white/40">numbers</div>
          {node.facts.map((f) => (
            <div key={f.label} className="border-l border-white/10 pl-2">
              <span className="text-white/50">{f.label}: </span>
              <span className="text-white">{f.value}</span>
              {f.cite.doi && (
                <>
                  {' '}
                  <a
                    href={`https://doi.org/${f.cite.doi}`}
                    target="_blank"
                    rel="noreferrer"
                    className="text-white/40 underline-offset-2 hover:underline"
                  >
                    doi:{f.cite.doi}
                  </a>
                </>
              )}
            </div>
          ))}
        </section>
      )}

      {node.anchors.length > 0 && (
        <section className="space-y-1 font-mono text-[10px]">
          <div className="text-[9px] uppercase tracking-widest text-white/40">
            atlas anchors (MNI mm)
          </div>
          {node.anchors.map((a) => (
            <div key={`${a.source}:${a.label}`} className="text-white/60">
              <span className="text-white/80">{a.label}</span> · {a.source} · (
              {a.centroid_mni_mm.map((v) => v.toFixed(0)).join(', ')})
            </div>
          ))}
        </section>
      )}

      {node.neuromorpho && node.neuromorpho.region && <RealCells query={node.neuromorpho} />}

      <section className="space-y-2">
        <div className="font-mono text-[9px] uppercase tracking-widest text-white/40">
          bridge to the {node.side === 'brain' ? 'AI' : 'brain'} side
        </div>
        {node.analogs.length === 0 && node.no_analog_note && (
          <div className="rounded border border-dashed border-white/20 p-2 font-mono text-[10px] leading-snug text-white/60">
            <span className="text-white/40">none · </span>
            {node.no_analog_note}
          </div>
        )}
        {node.analogs.map((a) => {
          const t = byId.get(a.target);
          return (
            <div
              key={a.target}
              className="space-y-1 rounded border p-2 font-mono text-[10px]"
              style={{ borderColor: STRENGTH_COLOR[a.strength] }}
            >
              <div className="flex items-baseline justify-between gap-2">
                <button
                  onClick={() => onSelect(a.target)}
                  className="text-left text-white hover:text-accent"
                >
                  → {a.target_name}
                  {t && <span className="text-white/40"> · L{t.level}</span>}
                </button>
                <span className="shrink-0" style={{ color: STRENGTH_COLOR[a.strength] }}>
                  {a.strength}
                </span>
              </div>
              <p className="leading-snug text-white/70">{a.note}</p>
              <Cites cites={a.cites} />
              <div className="text-[9px] text-white/30">{STRENGTH_LABEL[a.strength]}</div>
            </div>
          );
        })}
        {backlinks.length > 0 && (
          <div className="font-mono text-[10px] text-white/50">
            cited as analog by:{' '}
            {backlinks.map((b, i) => (
              <span key={b.id}>
                {i > 0 && ', '}
                <button onClick={() => onSelect(b.id)} className="text-white/70 hover:text-accent">
                  {b.name}
                </button>
              </span>
            ))}
          </div>
        )}
      </section>

      {node.widget && (
        <section className="border-t border-white/10 pt-4">
          <Widget id={node.widget} />
        </section>
      )}

      <section className="space-y-1 border-t border-white/10 pt-3">
        <div className="font-mono text-[9px] uppercase tracking-widest text-white/40">sources</div>
        <Cites cites={node.cites} />
      </section>
    </aside>
  );
}
