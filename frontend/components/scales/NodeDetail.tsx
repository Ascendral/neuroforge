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
import { Kicker } from '@/components/ui/Kicker';
import { fetchRegionSample } from '@/lib/api';
import { useNeuronSelection } from '@/lib/neuron-context';
import type { CiteModel, NeuronSearchResponse, ScaleNode, ScalesGraphResponse } from '@/lib/types';

import { STRENGTH_COLOR, STRENGTH_LABEL, Tag } from './strength';

interface NodeDetailProps {
  graph: ScalesGraphResponse;
  node: ScaleNode;
  onSelect: (id: string) => void;
  onShowOnBrain: (node: ScaleNode) => void;
  onClose: () => void;
}

function Cites({ cites }: { cites: CiteModel[] }) {
  return (
    <ul className="space-y-1.5">
      {cites.map((c, i) => (
        <li key={i} className="text-[12px] leading-snug text-white/50">
          {c.text}{' '}
          {c.doi && (
            <a
              href={`https://doi.org/${c.doi}`}
              target="_blank"
              rel="noreferrer"
              className="mono text-white/70 underline-offset-4 hover:text-white hover:underline"
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
    <section className="space-y-2">
      <div className="flex items-baseline justify-between">
        <Kicker>real reconstructions</Kicker>
        {sample && (
          <span className="mono text-[11px] text-white/35">
            {sample.total_matching.toLocaleString()} on neuromorpho.org
          </span>
        )}
      </div>
      {error && <p className="text-[12.5px] text-accent">{error}</p>}
      {!sample && !error && <p className="text-[12px] text-white/45">querying neuromorpho.org…</p>}
      {sample && (
        <ul className="glass tile divide-y divide-white/[0.06] px-4 py-1 text-[13px]">
          {sample.results.map((n) => (
            <li key={n.neuron_id} className="flex items-baseline justify-between gap-3 py-2">
              <button
                onClick={() => selection?.selectNeuron(n.neuron_id)}
                className="press mono text-left text-[12.5px] text-white hover:text-accent"
                title="render this neuron in 3D"
              >
                {n.neuron_name}
              </button>
              <span className="shrink-0 text-[11.5px] text-white/40">
                {n.species} · {n.archive}
              </span>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

export function NodeDetail({ graph, node, onSelect, onShowOnBrain, onClose }: NodeDetailProps) {
  const byId = new Map(graph.nodes.map((n) => [n.id, n]));
  const level = graph.levels.find((l) => l.level === node.level);
  const parent = node.parent ? byId.get(node.parent) : null;
  const backlinks = node.analog_of.map((id) => byId.get(id)).filter((n): n is ScaleNode => !!n);

  return (
    <aside className="hairline-l rise flex h-full w-[460px] shrink-0 flex-col gap-6 overflow-y-auto bg-canvas p-6 text-[14px]">
      <div className="flex items-start justify-between gap-3">
        <div className="space-y-2">
          <Kicker>
            {node.side} · level {node.level} ·{' '}
            {node.side === 'brain' ? level?.brain_name : level?.ai_name}
          </Kicker>
          <h2 className="serif text-[26px] leading-[1.05] text-white">{node.name}</h2>
        </div>
        <button onClick={onClose} className="chip shrink-0" aria-label="close">
          ✕
        </button>
      </div>

      <div className="flex flex-wrap gap-2">
        {node.anchors.length > 0 && (
          <button onClick={() => onShowOnBrain(node)} className="btn btn-sm btn-red">
            show on brain · {node.anchors.length}
          </button>
        )}
        {parent && (
          <button onClick={() => onSelect(parent.id)} className="chip">
            ↖ {parent.name}
          </button>
        )}
        {node.children.map((cid) => {
          const c = byId.get(cid);
          if (!c) return null;
          return (
            <button key={cid} onClick={() => onSelect(cid)} className="chip">
              ↘ {c.name}
            </button>
          );
        })}
      </div>

      <section className="space-y-4">
        <div className="space-y-1">
          <Kicker>what it is</Kicker>
          <p className="text-[14px] leading-relaxed text-white/85">{node.description}</p>
        </div>
        <div className="space-y-1">
          <Kicker>what it does</Kicker>
          <p className="text-[14px] leading-relaxed text-white/85">{node.function}</p>
        </div>
        <div className="space-y-1">
          <Kicker>how</Kicker>
          <p className="text-[14px] leading-relaxed text-white/85">{node.mechanism}</p>
        </div>
      </section>

      {node.facts.length > 0 && (
        <section className="space-y-2">
          <Kicker>numbers</Kicker>
          <div className="grid grid-cols-2 gap-2">
            {node.facts.map((f) => (
              <div key={f.label} className="glass tile flex flex-col gap-1.5 p-3.5">
                <span className="text-[13px] text-accent">◆</span>
                <span className="serif text-[15px] leading-snug text-white">{f.value}</span>
                <span className="meta-xs">{f.label}</span>
                {f.cite.doi && (
                  <a
                    href={`https://doi.org/${f.cite.doi}`}
                    target="_blank"
                    rel="noreferrer"
                    className="mono text-[10.5px] text-white/35 underline-offset-4 hover:text-white hover:underline"
                  >
                    doi:{f.cite.doi}
                  </a>
                )}
              </div>
            ))}
          </div>
        </section>
      )}

      {node.anchors.length > 0 && (
        <section className="space-y-2">
          <Kicker>atlas anchors · MNI mm</Kicker>
          <div className="glass tile divide-y divide-white/[0.06] px-4 py-1 text-[12.5px]">
            {node.anchors.map((a) => (
              <div
                key={`${a.source}:${a.label}`}
                className="flex items-baseline justify-between gap-3 py-2"
              >
                <span className="text-white/85">{a.label}</span>
                <span className="mono shrink-0 text-[11.5px] text-white/40">
                  {a.source.replace('_', '-')} ·{' '}
                  {a.centroid_mni_mm.map((v) => v.toFixed(0)).join(', ')}
                </span>
              </div>
            ))}
          </div>
        </section>
      )}

      {node.neuromorpho && node.neuromorpho.region && <RealCells query={node.neuromorpho} />}

      <section className="space-y-3">
        <Kicker>bridge to the {node.side === 'brain' ? 'AI' : 'brain'} side</Kicker>
        {node.analogs.length === 0 && node.no_analog_note && (
          <div className="tile p-4 text-[13px] leading-relaxed text-white/65 shadow-[inset_0_0_0_1px_rgba(255,255,255,0.14)]">
            <div className="mb-1.5">
              <Tag s="none" />
            </div>
            {node.no_analog_note}
          </div>
        )}
        {node.analogs.map((a) => {
          const t = byId.get(a.target);
          return (
            <div
              key={a.target}
              className="glass tile space-y-2.5 p-4 text-[13px]"
              style={{
                boxShadow: `inset 0 0 0 1px ${STRENGTH_COLOR[a.strength]}, inset 0 1px 0 rgba(255,255,255,0.14), 0 10px 30px rgba(0,0,0,0.35)`,
              }}
            >
              <div className="flex items-start justify-between gap-3">
                <button
                  onClick={() => onSelect(a.target)}
                  className="press serif text-left text-[16px] leading-tight text-white hover:text-accent"
                >
                  {a.target_name}
                  {t && <span className="meta-xs ml-2">L{t.level}</span>}
                </button>
                <Tag s={a.strength} />
              </div>
              <p className="leading-relaxed text-white/75">{a.note}</p>
              <Cites cites={a.cites} />
              <div className="meta-xs">{STRENGTH_LABEL[a.strength]}</div>
            </div>
          );
        })}
        {backlinks.length > 0 && (
          <div className="flex flex-wrap items-center gap-1.5 text-[12px] text-white/50">
            <span className="meta-xs mr-1">cited as analog by</span>
            {backlinks.map((b) => (
              <button key={b.id} onClick={() => onSelect(b.id)} className="chip">
                {b.name}
              </button>
            ))}
          </div>
        )}
      </section>

      {node.widget && (
        <section className="hairline-t pt-5">
          <Widget id={node.widget} />
        </section>
      )}

      <section className="hairline-t space-y-2 pt-4">
        <Kicker>sources</Kicker>
        <Cites cites={node.cites} />
      </section>
    </aside>
  );
}
