'use client';

import { useMemo, useState } from 'react';

import { Hero, heroStill } from '@/components/ui/Hero';
import { Pills } from '@/components/ui/Pills';
import type { Milestone, ScalesGraphResponse, TimelineResponse } from '@/lib/types';

// Research timeline 1921 → 2025. Every entry is a registry milestone with a
// verified DOI (or an explicit note saying why there is none).

const CAT_COLOR: Record<Milestone['category'], string> = {
  neuro: '#9bd2ff',
  ai: '#ffffff',
  bridge: '#E10500',
};

const FILTERS = ['all', 'neuro', 'ai', 'bridge'] as const;
type Filter = (typeof FILTERS)[number];

interface TimelineViewProps {
  timeline: TimelineResponse;
  graph: ScalesGraphResponse | null;
  onJump: (nodeId: string) => void;
}

export function TimelineView({ timeline, graph, onJump }: TimelineViewProps) {
  const [filter, setFilter] = useState<Filter>('all');
  const byId = useMemo(() => new Map((graph?.nodes ?? []).map((n) => [n.id, n])), [graph]);
  const items = useMemo(
    () => timeline.milestones.filter((m) => filter === 'all' || m.category === filter),
    [timeline, filter],
  );
  const decades = useMemo(() => {
    const map = new Map<number, Milestone[]>();
    for (const m of items) {
      const d = Math.floor(m.year / 10) * 10;
      (map.get(d) ?? map.set(d, []).get(d)!).push(m);
    }
    return Array.from(map.entries()).sort((a, b) => a[0] - b[0]);
  }, [items]);

  const count = (c: Milestone['category']) =>
    timeline.milestones.filter((m) => m.category === c).length;
  const years = timeline.milestones.map((m) => m.year);

  return (
    <div className="h-full overflow-y-auto">
      <Hero
        still={heroStill('pyramidal')}
        kicker="research timeline"
        title={
          <>
            {Math.min(...years)} <span className="text-white/30">→</span> {Math.max(...years)}
          </>
        }
        subtitle="Landmark results in neuroscience, in AI, and at the bridge between them. Every entry cites a DOI that the build verifies."
        callouts={[
          { label: 'milestones', value: timeline.n },
          { label: 'neuro', value: count('neuro') },
          { label: 'ai', value: count('ai') },
          { label: 'bridge', value: count('bridge') },
          { label: 'dois verified', value: timeline.milestones.filter((m) => m.doi).length },
        ]}
        height={260}
      />
      <div className="hairline-b sticky top-0 z-10 flex items-center gap-4 bg-canvas/90 px-6 py-3 backdrop-blur-xl">
        <Pills options={FILTERS} value={filter} onChange={setFilter} size="sm" />
        <span className="meta-xs">
          {items.length} of {timeline.n} milestones
        </span>
        <span className="ml-auto hidden text-[12px] text-white/35 lg:block">{timeline.note}</span>
      </div>
      <div className="mx-auto max-w-4xl px-6 py-8">
        {decades.map(([decade, ms]) => (
          <div key={decade} className="mb-12">
            <div className="display mb-5 text-white/90" style={{ fontSize: 30 }}>
              {decade}s
            </div>
            <ol className="space-y-3">
              {ms.map((m) => (
                <li key={`${m.year}-${m.title}`} className="glass tile rise relative p-5 pl-6">
                  <span
                    className="absolute left-0 top-6 h-8 w-[3px] rounded-r"
                    style={{ background: CAT_COLOR[m.category] }}
                  />
                  <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
                    <span className="mono text-[13px] text-white/50">{m.year}</span>
                    <span className="serif text-[19px] leading-tight text-white">{m.title}</span>
                    <span className="meta-xs" style={{ color: CAT_COLOR[m.category] }}>
                      {m.category}
                    </span>
                  </div>
                  <div className="mt-1 text-[12.5px] text-white/45">{m.who}</div>
                  <p className="mt-2 max-w-3xl text-[14px] leading-relaxed text-white/80">
                    {m.significance}
                  </p>
                  <div className="mt-3 flex flex-wrap items-center gap-2">
                    {m.doi ? (
                      <a
                        href={`https://doi.org/${m.doi}`}
                        target="_blank"
                        rel="noreferrer"
                        className="mono text-[11.5px] text-white/50 underline-offset-4 hover:text-white hover:underline"
                      >
                        doi:{m.doi}
                      </a>
                    ) : (
                      <span className="text-[11.5px] text-white/35">{m.note}</span>
                    )}
                    {m.links.map((id) => {
                      const n = byId.get(id);
                      return (
                        <button
                          key={id}
                          onClick={() => onJump(id)}
                          className="chip"
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
