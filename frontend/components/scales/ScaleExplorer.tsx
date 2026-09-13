'use client';

import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react';

import type { EvidenceStrength, ScaleNode, ScalesGraphResponse } from '@/lib/types';

import { STRENGTH_COLOR, STRENGTH_DASH, STRENGTH_LABEL, bestStrength } from './strength';

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
      className={`w-full rounded border bg-black/85 p-2 text-left transition-colors ${
        selected ? 'border-accent' : 'border-white/15 hover:border-white/40'
      } ${dim ? 'opacity-40' : ''}`}
    >
      <div className="flex items-baseline justify-between gap-2">
        <span className="text-xs font-semibold leading-tight text-white">{node.name}</span>
        {best && (
          <span
            className="shrink-0 font-mono text-[9px]"
            style={{ color: STRENGTH_COLOR[best] }}
            title={STRENGTH_LABEL[best]}
          >
            {best === 'none' ? '∅' : best}
          </span>
        )}
      </div>
      <p className="mt-1 font-mono text-[10px] leading-snug text-white/55">{node.function}</p>
      <div className="mt-1 flex flex-wrap gap-1 font-mono text-[9px] text-white/35">
        {node.widget && (
          <span className="rounded border border-white/15 px-1">
            ▶ {node.widget.replace('_', ' ')}
          </span>
        )}
        {node.anchors.length > 0 && (
          <span className="rounded border border-white/15 px-1">◉ atlas</span>
        )}
        {node.neuromorpho && (
          <span className="rounded border border-white/15 px-1">⌇ real cells</span>
        )}
        {node.children.length > 0 && (
          <span className="rounded border border-white/15 px-1">↘ {node.children.length}</span>
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
    for (const n of brainNodes) {
      for (const a of n.analogs) {
        if (!visible.has(a.target)) continue;
        const e1 = cardRefs.current.get(n.id);
        const e2 = cardRefs.current.get(a.target);
        if (!e1 || !e2) continue;
        const b1 = e1.getBoundingClientRect();
        const b2 = e2.getBoundingClientRect();
        out.push({
          from: n.id,
          to: a.target,
          strength: a.strength,
          x1: b1.right - rootBox.left,
          y1: b1.top + b1.height / 2 - rootBox.top + root.scrollTop,
          x2: b2.left - rootBox.left,
          y2: b2.top + b2.height / 2 - rootBox.top + root.scrollTop,
        });
      }
    }
    // AI → brain links not already covered
    for (const n of aiNodes) {
      for (const a of n.analogs) {
        if (!visible.has(a.target)) continue;
        if (out.some((l) => l.from === a.target && l.to === n.id)) continue;
        const e1 = cardRefs.current.get(a.target);
        const e2 = cardRefs.current.get(n.id);
        if (!e1 || !e2) continue;
        const b1 = e1.getBoundingClientRect();
        const b2 = e2.getBoundingClientRect();
        out.push({
          from: a.target,
          to: n.id,
          strength: a.strength,
          x1: b1.right - rootBox.left,
          y1: b1.top + b1.height / 2 - rootBox.top + root.scrollTop,
          x2: b2.left - rootBox.left,
          y2: b2.top + b2.height / 2 - rootBox.top + root.scrollTop,
        });
      }
    }
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
      <div className="flex items-stretch gap-1 border-b border-white/10 px-4 py-2">
        {graph.levels.map((l) => (
          <button
            key={l.level}
            onClick={() => {
              onLevel(l.level);
              onSelect(null);
            }}
            className={`flex-1 rounded border px-2 py-1 text-left font-mono text-[10px] ${
              l.level === level
                ? 'border-accent text-white'
                : 'border-white/15 text-white/50 hover:bg-white/5'
            }`}
          >
            <div className="uppercase tracking-widest text-white/40">level {l.level}</div>
            <div>
              {l.brain_name} <span className="text-white/30">↔</span> {l.ai_name}
            </div>
          </button>
        ))}
      </div>

      {lv && (
        <div className="flex gap-6 border-b border-white/10 px-4 py-2 font-mono text-[10px] text-white/50">
          <div className="flex-1">
            <span className="text-white/80">brain · {lv.brain_name}</span> — {lv.brain_blurb}
          </div>
          <div className="w-24 shrink-0 text-center text-white/30">
            {(['equivalence', 'strong', 'analogy', 'none'] as EvidenceStrength[]).map((s) => (
              <div key={s} className="flex items-center gap-1" title={STRENGTH_LABEL[s]}>
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
                <span className="text-[9px]">{s}</span>
              </div>
            ))}
          </div>
          <div className="flex-1 text-right">
            <span className="text-white/80">AI · {lv.ai_name}</span> — {lv.ai_blurb}
          </div>
        </div>
      )}

      {crossLevelLinks.length > 0 && (
        <div className="flex flex-wrap items-center gap-2 border-b border-white/10 px-4 py-1.5 font-mono text-[10px] text-white/50">
          <span>links on other rungs:</span>
          {crossLevelLinks.map(({ a, t }) => (
            <button
              key={t.id}
              onClick={() => {
                onLevel(t.level);
                onSelect(t.id);
              }}
              className="rounded border px-2 py-0.5 hover:bg-white/5"
              style={{ borderColor: STRENGTH_COLOR[a.strength], color: STRENGTH_COLOR[a.strength] }}
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
                strokeWidth={active && related ? 2 : 1.2}
                strokeDasharray={STRENGTH_DASH[l.strength]}
                opacity={active ? 1 : 0.15}
              />
            );
          })}
        </svg>
        <div className="grid grid-cols-[1fr_120px_1fr] gap-0 p-4">
          <div className="space-y-2">
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
              <p className="font-mono text-[10px] text-white/40">nothing at this rung</p>
            )}
          </div>
          <div />
          <div className="space-y-2">
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
              <p className="font-mono text-[10px] text-white/40">nothing at this rung</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
