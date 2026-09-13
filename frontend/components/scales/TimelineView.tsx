'use client';

import { useMemo, useState } from 'react';

import type { Milestone, ScalesGraphResponse, TimelineResponse } from '@/lib/types';

// Research timeline 1921 → 2025. Every entry is a registry milestone with a
// verified DOI (or an explicit note saying why there is none).

const CAT_COLOR: Record<Milestone['category'], string> = {
  neuro: '#9bd2ff',
  ai: '#ffffff',
  bridge: '#ff2d2d',
};

interface TimelineViewProps {
  timeline: TimelineResponse;
  graph: ScalesGraphResponse | null;
  onJump: (nodeId: string) => void;
}

export function TimelineView({ timeline, graph, onJump }: TimelineViewProps) {
  const [filter, setFilter] = useState<'all' | Milestone['category']>('all');
  const byId = useMemo(() => new Map((graph?.nodes ?? []).map((n) => [n.id, n])), [graph]);
  const items = timeline.milestones.filter((m) => filter === 'all' || m.category === filter);
  const decades = useMemo(() => {
    const map = new Map<number, Milestone[]>();
    for (const m of items) {
      const d = Math.floor(m.year / 10) * 10;
      (map.get(d) ?? map.set(d, []).get(d)!).push(m);
    }
    return Array.from(map.entries()).sort((a, b) => a[0] - b[0]);
  }, [items]);

  return (
    <div className="h-full overflow-y-auto">
      <div className="sticky top-0 z-10 flex items-center gap-2 border-b border-white/10 bg-black/95 px-6 py-2 font-mono text-[10px]">
        <span className="text-white/40">{timeline.n} milestones</span>
        {(['all', 'neuro', 'ai', 'bridge'] as const).map((c) => (
          <button
            key={c}
            onClick={() => setFilter(c)}
            className={`rounded border px-2 py-0.5 ${filter === c ? 'border-white text-white' : 'border-white/20 text-white/50 hover:bg-white/5'}`}
            style={c !== 'all' && filter === c ? { borderColor: CAT_COLOR[c] } : undefined}
          >
            {c}
          </button>
        ))}
        <span className="ml-auto text-white/30">{timeline.note}</span>
      </div>
      <div className="mx-auto max-w-4xl px-6 py-6">
        {decades.map(([decade, ms]) => (
          <div key={decade} className="mb-8">
            <div className="mb-3 font-mono text-xs uppercase tracking-widest text-white/40">
              {decade}s
            </div>
            <ol className="space-y-3 border-l border-white/10 pl-5">
              {ms.map((m) => (
                <li key={`${m.year}-${m.title}`} className="relative">
                  <span
                    className="absolute -left-[26px] top-1.5 inline-block h-2 w-2 rounded-full"
                    style={{ background: CAT_COLOR[m.category] }}
                  />
                  <div className="flex items-baseline gap-3">
                    <span className="font-mono text-xs text-white/50">{m.year}</span>
                    <span className="text-sm font-semibold text-white">{m.title}</span>
                    <span
                      className="font-mono text-[10px]"
                      style={{ color: CAT_COLOR[m.category] }}
                    >
                      {m.category}
                    </span>
                  </div>
                  <div className="font-mono text-[10px] text-white/45">{m.who}</div>
                  <p className="mt-1 max-w-3xl text-xs leading-snug text-white/75">
                    {m.significance}
                  </p>
                  <div className="mt-1 flex flex-wrap items-center gap-2 font-mono text-[10px]">
                    {m.doi ? (
                      <a
                        href={`https://doi.org/${m.doi}`}
                        target="_blank"
                        rel="noreferrer"
                        className="text-white/50 underline-offset-2 hover:text-white hover:underline"
                      >
                        doi:{m.doi}
                      </a>
                    ) : (
                      <span className="text-white/30">{m.note}</span>
                    )}
                    {m.links.map((id) => {
                      const n = byId.get(id);
                      return (
                        <button
                          key={id}
                          onClick={() => onJump(id)}
                          className="rounded border border-white/20 px-1.5 py-0.5 text-white/60 hover:bg-white/5"
                          title="open in the scale explorer"
                        >
                          {n ? `${n.side} L${n.level} · ${n.name}` : id}
                        </button>
                      );
                    })}
                  </div>
                </li>
              ))}
            </ol>
          </div>
        ))}
      </div>
    </div>
  );
}
