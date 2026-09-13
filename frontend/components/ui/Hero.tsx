'use client';

import heroes from '@/lib/heroes.json';

// Hero band: a black-studio still of a REAL reconstruction (or the real
// fsaverage shell) rendered by scripts/render_heroes.py, fading into the
// canvas, with the display headline, a kicker, and spec callouts. The caption
// credits the actual cell — nothing here is generated art.

export interface HeroStill {
  key: string;
  file: string;
  kind: 'neuron' | 'brain';
  caption: string;
  neuron_name?: string;
  archive?: string;
  species?: string;
  doi?: string | null;
  source_url?: string;
}

const STILLS = heroes as HeroStill[];

export function heroStill(key: string): HeroStill | null {
  return STILLS.find((h) => h.key === key) ?? STILLS[0] ?? null;
}

export interface Callout {
  label: string;
  value: React.ReactNode;
}

interface HeroProps {
  still: HeroStill | null;
  kicker: string;
  title: React.ReactNode;
  subtitle?: React.ReactNode;
  callouts?: Callout[];
  height?: number;
  children?: React.ReactNode; // slot overlaid at the bottom (e.g. the ladder)
}

export function Hero({
  still,
  kicker,
  title,
  subtitle,
  callouts = [],
  height = 260,
  children,
}: HeroProps) {
  return (
    <div className="hairline-b relative shrink-0 overflow-hidden bg-canvas" style={{ height }}>
      {still && (
        // eslint-disable-next-line @next/next/no-img-element
        <img
          src={still.file}
          alt=""
          className="absolute inset-0 h-full w-full object-cover object-left"
          style={{
            WebkitMaskImage:
              'linear-gradient(to right, black 0%, black 38%, rgba(0,0,0,0.55) 58%, transparent 82%), linear-gradient(to bottom, black 70%, transparent 100%)',
            maskImage:
              'linear-gradient(to right, black 0%, black 38%, rgba(0,0,0,0.55) 58%, transparent 82%), linear-gradient(to bottom, black 70%, transparent 100%)',
            WebkitMaskComposite: 'source-in',
            maskComposite: 'intersect',
          }}
        />
      )}
      <div className="absolute inset-y-0 right-0 flex w-[58%] flex-col justify-center gap-3 px-8">
        <span className="kicker">{kicker}</span>
        <h2 className="display text-white" style={{ fontSize: 'clamp(18px, 2.4vw, 34px)', lineHeight: 1.05 }}>
          {title}
        </h2>
        {subtitle && (
          <p className="max-w-xl text-[14px] leading-relaxed text-white/60">{subtitle}</p>
        )}
        {callouts.length > 0 && (
          <div className="mt-1 flex flex-wrap gap-6">
            {callouts.map((c) => (
              <div key={c.label} className="flex flex-col">
                <span className="serif text-[22px] leading-none text-white">{c.value}</span>
                <span className="meta-xs mt-1.5">{c.label}</span>
              </div>
            ))}
          </div>
        )}
      </div>
      {still && (
        <div className="absolute bottom-3 left-5 max-w-[46%] text-[10.5px] leading-snug text-white/35">
          {still.caption}
          {still.source_url && (
            <>
              {' · '}
              <a
                href={still.source_url}
                target="_blank"
                rel="noreferrer"
                className="hover:text-white/70"
              >
                source ↗
              </a>
            </>
          )}
        </div>
      )}
      {children}
    </div>
  );
}
