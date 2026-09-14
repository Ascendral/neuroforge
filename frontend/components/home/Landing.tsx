'use client';

import { Kicker, DisplayLine, StatTile } from '@/components/ui/Kicker';
import { heroStill } from '@/components/ui/Hero';
import type { ScalesGraphResponse } from '@/lib/types';

// Landing view: the first screen. Answers "what is this" in one read, with the
// project's own black-studio stills of real reconstructions — no generated art.

type NavTarget = 'brain' | 'scales' | 'ai' | 'timeline' | 'neuron';

const VIEW_CARDS: {
  view: NavTarget;
  still: string;
  title: string;
  blurb: string;
}[] = [
  {
    view: 'scales',
    still: 'purkinje',
    title: 'The ladder',
    blurb:
      'Five rungs, two sides. Brain on the left, a transformer on the right, every bridge tagged by evidence.',
  },
  {
    view: 'brain',
    still: 'brain',
    title: 'The brain',
    blurb: 'A 3D cortex with real atlases, tracts, receptor maps and 120 reconstructed neurons.',
  },
  {
    view: 'ai',
    still: 'granule',
    title: 'The machine',
    blurb: 'A complete schematic of a modern LLM — every box on it is a cited node.',
  },
  {
    view: 'timeline',
    still: 'dopaminergic',
    title: 'The century',
    blurb: '72 landmark results, 1921 to 2025, each one DOI-verified.',
  },
  {
    view: 'neuron',
    still: 'pyramidal',
    title: 'One cell, live',
    blurb: 'Any NeuroMorpho reconstruction in 3D with Hodgkin–Huxley running on it.',
  },
];

export function Landing({
  graph,
  onNavigate,
}: {
  graph: ScalesGraphResponse | null;
  onNavigate: (view: NavTarget) => void;
}) {
  const hero = heroStill('purkinje');
  const brainNodes = graph ? graph.nodes.filter((n) => n.side === 'brain').length : null;
  const aiNodes = graph ? graph.nodes.filter((n) => n.side === 'ai').length : null;
  const bridges = graph ? graph.nodes.reduce((s, n) => s + n.analogs.length, 0) : null;

  return (
    <div className="h-full overflow-y-auto">
      {/* Hero */}
      <div className="relative min-h-[62vh] overflow-hidden">
        {hero && (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={hero.file}
            alt=""
            className="absolute inset-0 h-full w-full object-cover"
            style={{
              maskImage: 'linear-gradient(180deg, black 55%, transparent 98%)',
              WebkitMaskImage: 'linear-gradient(180deg, black 55%, transparent 98%)',
            }}
          />
        )}
        <div
          className="absolute inset-0"
          style={{
            background:
              'radial-gradient(65% 70% at 32% 62%, rgba(10,10,11,0.88), rgba(10,10,11,0.35) 60%, transparent 85%)',
          }}
        />
        <div className="relative flex min-h-[62vh] flex-col justify-end gap-5 px-6 pb-10 pt-16 md:px-12">
          <Kicker>Ascendral · free open research</Kicker>
          <DisplayLine size={52} className="max-w-[16ch] leading-[1.04]">
            The brain and the machine, on one ladder.
          </DisplayLine>
          <p className="max-w-[52ch] text-[15px] leading-relaxed text-white/70">
            The human brain on one side. A modern AI on the other. Five rungs from whole organ down
            to a single synapse — and at every rung, the bridge between them, tagged by how much
            evidence backs it. Everything on screen is real data, and every claim carries a
            citation a script has verified.
          </p>
          <div className="flex flex-wrap items-center gap-3 pt-1">
            <button type="button" className="btn btn-red" onClick={() => onNavigate('scales')}>
              Climb the ladder
            </button>
            <button type="button" className="btn" onClick={() => onNavigate('brain')}>
              Fly the brain
            </button>
          </div>
          {hero && <p className="meta-xs pt-1 text-white/35">{hero.caption}</p>}
        </div>
      </div>

      {/* Numbers */}
      <div className="grid grid-cols-2 gap-3 px-6 py-8 md:grid-cols-5 md:px-12">
        <StatTile label="brain nodes" value={brainNodes ?? '—'} glyph="◧" />
        <StatTile label="AI nodes" value={aiNodes ?? '—'} glyph="◨" />
        <StatTile label="evidence-tagged bridges" value={bridges ?? '—'} glyph="⇄" />
        <StatTile label="live models" value="9" glyph="∿" sub="Hodgkin–Huxley → attention" />
        <StatTile label="verified sources" value="128" glyph="✓" sub="every DOI resolves" />
      </div>

      {/* Views */}
      <div className="px-6 pb-12 md:px-12">
        <Kicker className="mb-4">Five ways in</Kicker>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-5">
          {VIEW_CARDS.map((c) => {
            const still = heroStill(c.still);
            return (
              <button
                key={c.view}
                type="button"
                onClick={() => onNavigate(c.view)}
                className="glass press group overflow-hidden rounded-[18px] text-left"
              >
                <div className="relative h-28 overflow-hidden">
                  {still && (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img
                      src={still.file}
                      alt=""
                      className="h-full w-full object-cover opacity-80 transition-opacity duration-200 group-hover:opacity-100"
                    />
                  )}
                </div>
                <div className="flex flex-col gap-1.5 p-4">
                  <span className="serif text-[17px] text-white">{c.title}</span>
                  <span className="text-[12.5px] leading-snug text-white/55">{c.blurb}</span>
                </div>
              </button>
            );
          })}
        </div>
        <p className="meta-xs pt-8 text-white/35">
          MIT-licensed ·{' '}
          <a
            href="https://github.com/Ascendral/neuroforge"
            rel="noopener noreferrer"
            target="_blank"
            className="underline underline-offset-4 hover:text-white"
          >
            github.com/Ascendral/neuroforge
          </a>{' '}
          · datasets keep their original licenses · no generated imagery anywhere
        </p>
      </div>
    </div>
  );
}
