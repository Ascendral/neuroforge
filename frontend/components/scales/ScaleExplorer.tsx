'use client';

import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react';

import type { EvidenceStrength, ScaleNode, ScalesGraphResponse } from '@/lib/types';

import { STRENGTH_COLOR, STRENGTH_DASH, STRENGTH_LABEL, Tag, bestStrength } from './strength';

// The ladder view: brain on the left, AI on the right, one rung at a time.
// Lines between cards are the registry's analog links (colored by evidence
// strength). Cards are registry nodes; nothing is drawn that the backend did
// not return.

interface ScaleExplorerProps {
  graph: ScalesGraphResponse;
  level: number;
  selectedId: string | null;
  onLevel: (level: number) => void;
  onSelect: (id: string | null) => void;
}

interface Line {
  from: string;
  to: string;
  strength: EvidenceStrength;
  x1: number;
  y1: number;
  x2: number;
  y2: number;
}

function Card({
  node,
  selected,
  dim,
  onClick,
  register,
}: {
  node: ScaleNode;
  selected: boolean;
  dim: boolean;
  onClick: () => void;
  register: (el: HTMLButtonElement | null) => void;
}) {
  const best =
    bestStrength(node.analogs.map((a) => a.strength)) ?? (node.no_analog_note ? 'none' : null);
  return (
    <button
      ref={register}
      onClick={onClick}
      className={`press tile w-full p-4 text-left ${selected ? 'glass-strong' : 'glass'}`}
      style={{
        opacity: dim ? 0.35 : 1,
        boxShadow: selected
          ? 'inset 0 0 0 1.5px #E10500, inset 0 1px 0 rgba(255,255,255,0.22), 0 14px 34px rgba(0,0,0,0.5)'
          : undefined,
        transition:
          'opacity 0.3s ease, transform 0.25s var(--spring), background-color 0.2s ease, box-shadow 0.2s ease',
      }}
    >
      <div className="flex items-start justify-between gap-3">
        <span className="serif text-[17px] leading-tight text-white">{node.name}</span>
        {best && <Tag s={best} />}
      </div>
      <p className="mt-1.5 text-[13px] leading-snug text-white/55">{node.function}</p>
      <div className="mt-2.5 flex flex-wrap gap-1.5 text-[10.5px] text-white/40">
        {node.widget && (
          <span className="meta-xs rounded-full bg-white/[0.07] px-2 py-0.5 text-white/60">
            ▶ live model
          </span>
        )}
        {node.anchors.length > 0 && (
          <span className="meta-xs rounded-full bg-white/[0.07] px-2 py-0.5">◉ atlas</span>
        )}
        {node.neuromorpho && (
          <span className="meta-xs rounded-full bg-white/[0.07] px-2 py-0.5">⌇ real cells</span>
        )}
        {node.children.length > 0 && (
          <span className="meta-xs rounded-full bg-white/[0.07] px-2 py-0.5">
            ↘ {node.children.length} inside
          </span>
        )}
      </div>
    </button>
  );
}

export function ScaleExplorer({ graph, level, selectedId, onLevel, onSelect }: ScaleExplorerProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const cardRefs = useRef<Map<string, HTMLButtonElement>>(new Map());
  const [lines, setLines] = useState<Line[]>([]);

  const byId = useMemo(() => new Map(graph.nodes.map((n) => [n.id, n])), [graph]);
  const brainNodes = useMemo(
    () =>
      graph.nodes
        .filter((n) => n.side === 'brain' && n.level === level)
        .sort((a, b) => a.order - b.order),
    [graph, level],
  );
  const aiNodes = useMemo(
    () =>
      graph.nodes
        .filter((n) => n.side === 'ai' && n.level === level)
        .sort((a, b) => a.order - b.order),
    [graph, level],
  );
  const lv = graph.levels.find((l) => l.level === level);
  const selected = selectedId ? (byId.get(selectedId) ?? null) : null;

  // ids linked to the selected node (for dimming everything else)
  const related = useMemo(() => {
    if (!selected) return null;
    const s = new Set<string>([selected.id]);
    selected.analogs.forEach((a) => s.add(a.target));
    selected.analog_of.forEach((id) => s.add(id));
    if (selected.parent) s.add(selected.parent);
    selected.children.forEach((c) => s.add(c));
    return s;
  }, [selected]);

  const register = useCallback(
    (id: string) => (el: HTMLButtonElement | null) => {
      if (el) cardRefs.current.set(id, el);
      else cardRefs.current.delete(id);
    },
    [],
  );

  const measure = useCallback(() => {
    const root = containerRef.current;
    if (!root) return;
    const rootBox = root.getBoundingClientRect();
    const out: Line[] = [];
    const visible = new Set([...brainNodes, ...aiNodes].map((n) => n.id));
    const push = (fromId: string, toId: string, strength: EvidenceStrength) => {
      if (out.some((l) => l.from === fromId && l.to === toId)) return;
      const e1 = cardRefs.current.get(fromId);
      const e2 = cardRefs.current.get(toId);
      if (!e1 || !e2) return;
      const b1 = e1.getBoundingClientRect();
      const b2 = e2.getBoundingClientRect();
      out.push({
        from: fromId,
        to: toId,
        strength,
        x1: b1.right - rootBox.left,
        y1: b1.top + b1.height / 2 - rootBox.top + root.scrollTop,
        x2: b2.left - rootBox.left,
        y2: b2.top + b2.height / 2 - rootBox.top + root.scrollTop,
      });
    };
    for (const n of brainNodes)
      for (const a of n.analogs) if (visible.has(a.target)) push(n.id, a.target, a.strength);
    for (const n of aiNodes)
      for (const a of n.analogs) if (visible.has(a.target)) push(a.target, n.id, a.strength);
    setLines(out);
  }, [brainNodes, aiNodes]);

  useLayoutEffect(() => {
    measure();
  }, [measure, selectedId]);

  useEffect(() => {
    const root = containerRef.current;
    if (!root) return;
    const ro = new ResizeObserver(() => measure());
    ro.observe(root);
    root.addEventListener('scroll', measure);
    window.addEventListener('resize', measure);
    return () => {
      ro.disconnect();
      root.removeEventListener('scroll', measure);
      window.removeEventListener('resize', measure);
    };
  }, [measure]);

  const crossLevelLinks = useMemo(() => {
    if (!selected) return [];
    return selected.analogs
      .map((a) => ({ a, t: byId.get(a.target) }))
      .filter(
        (x): x is { a: (typeof selected.analogs)[number]; t: ScaleNode } =>
          !!x.t && x.t.level !== level,
      );
  }, [selected, byId, level]);

  return (
    <div className="flex h-full flex-col">
      {/* ladder */}
      <div className="hairline-b flex items-stretch gap-2 px-5 py-3">
        {graph.levels.map((l) => {
          const on = l.level === level;
          return (
            <button
              key={l.level}
              onClick={() => {
                onLevel(l.level);
                onSelect(null);
              }}
              className={`press tile flex-1 px-4 py-2.5 text-left ${on ? 'bg-white text-[#0A0A0B]' : 'glass text-white/60 hover:text-white'}`}
              style={{ transition: 'all 0.3s var(--spring)' }}
            >
              <div className={`meta-xs ${on ? '!text-[#0A0A0B]/55' : ''}`}>level {l.level}</div>
              <div className="serif mt-0.5 text-[15px] leading-tight">
                {l.brain_name} <span className="opacity-40">↔</span> {l.ai_name}
              </div>
            </button>
          );
        })}
      </div>

      {lv && (
        <div className="hairline-b flex items-center gap-8 px-5 py-2.5 text-[12.5px] text-white/50">
          <div className="flex-1">
            <span className="meta mr-2 text-white/80">brain</span>
            {lv.brain_blurb}
          </div>
          <div className="flex shrink-0 items-center gap-3">
            {(['equivalence', 'strong', 'analogy', 'none'] as EvidenceStrength[]).map((s) => (
              <div key={s} className="flex items-center gap-1.5" title={STRENGTH_LABEL[s]}>
                <svg width={22} height={6}>
                  <line
                    x1={0}
                    x2={22}
                    y1={3}
                    y2={3}
                    stroke={STRENGTH_COLOR[s]}
                    strokeWidth={2}
                    strokeDasharray={STRENGTH_DASH[s]}
                  />
                </svg>
                <span className="meta-xs">{s}</span>
              </div>
            ))}
          </div>
          <div className="flex-1 text-right">
            {lv.ai_blurb}
            <span className="meta ml-2 text-white/80">ai</span>
          </div>
        </div>
      )}

      {crossLevelLinks.length > 0 && (
        <div className="hairline-b rise flex flex-wrap items-center gap-2 px-5 py-2 text-[12.5px] text-white/50">
          <span className="meta-xs">links on other rungs</span>
          {crossLevelLinks.map(({ a, t }) => (
            <button
              key={t.id}
              onClick={() => {
                onLevel(t.level);
                onSelect(t.id);
              }}
              className="chip"
              style={{ color: STRENGTH_COLOR[a.strength] }}
            >
              L{t.level} · {t.name}
            </button>
          ))}
        </div>
      )}

      <div ref={containerRef} className="relative flex-1 overflow-y-auto">
        <svg
          className="pointer-events-none absolute left-0 top-0 h-full w-full"
          style={{ minHeight: '100%' }}
        >
          {lines.map((l) => {
            const active = !related || (related.has(l.from) && related.has(l.to));
            const mx = (l.x1 + l.x2) / 2;
            return (
              <path
                key={`${l.from}->${l.to}`}
                d={`M${l.x1} ${l.y1} C ${mx} ${l.y1}, ${mx} ${l.y2}, ${l.x2} ${l.y2}`}
                fill="none"
                stroke={STRENGTH_COLOR[l.strength]}
                strokeWidth={active && related ? 2.2 : 1.2}
                strokeDasharray={STRENGTH_DASH[l.strength]}
                opacity={active ? 1 : 0.12}
                style={{ transition: 'opacity 0.3s ease' }}
              />
            );
          })}
        </svg>
        <div className="grid grid-cols-[1fr_140px_1fr] gap-0 p-5">
          <div className="space-y-3">
            {brainNodes.map((n) => (
              <Card
                key={n.id}
                node={n}
                selected={n.id === selectedId}
                dim={!!related && !related.has(n.id)}
                onClick={() => onSelect(n.id === selectedId ? null : n.id)}
                register={register(n.id)}
              />
            ))}
            {brainNodes.length === 0 && (
              <p className="text-[12px] text-white/45">nothing at this rung</p>
            )}
          </div>
          <div />
          <div className="space-y-3">
            {aiNodes.map((n) => (
              <Card
                key={n.id}
                node={n}
                selected={n.id === selectedId}
                dim={!!related && !related.has(n.id)}
                onClick={() => onSelect(n.id === selectedId ? null : n.id)}
                register={register(n.id)}
              />
            ))}
            {aiNodes.length === 0 && (
              <p className="text-[12px] text-white/45">nothing at this rung</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
