'use client';

import { useEffect, useMemo, useRef, useState } from 'react';

import { fetchV1NeuronSample, simulateV1 } from '@/lib/api';
import { useNeuronSelection } from '@/lib/neuron-context';
import type { NeuronSearchResponse, V1Response } from '@/lib/types';

// Anti-theater: the Gabor visualization is drawn from response.gabor_even.
// The tuning curve is drawn from response.tuning_*. Nothing synthetic.

const FILTER_PX = 96;
const PLOT_W = 320;
const PLOT_H = 130;
const PAD_L = 28;
const PAD_R = 8;
const PAD_T = 12;
const PAD_B = 22;

function drawFilter(canvas: HTMLCanvasElement, filter: number[][]) {
  const size = filter.length;
  const ctx = canvas.getContext('2d');
  if (!ctx) return;
  // Find symmetric range so 0 is mid-gray, +max white, -max black.
  let absMax = 1e-9;
  for (const row of filter) {
    for (const v of row) {
      const a = Math.abs(v);
      if (a > absMax) absMax = a;
    }
  }
  const img = ctx.createImageData(size, size);
  for (let y = 0; y < size; y++) {
    for (let x = 0; x < size; x++) {
      const v = filter[y][x] / absMax;
      const g = Math.round((v + 1) * 127.5);
      const i = (y * size + x) * 4;
      img.data[i] = g;
      img.data[i + 1] = g;
      img.data[i + 2] = g;
      img.data[i + 3] = 255;
    }
  }
  // Render at native resolution then upscale via canvas size
  const off = document.createElement('canvas');
  off.width = size;
  off.height = size;
  const offCtx = off.getContext('2d');
  if (!offCtx) return;
  offCtx.putImageData(img, 0, 0);
  ctx.imageSmoothingEnabled = false;
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.drawImage(off, 0, 0, canvas.width, canvas.height);
}

interface FilterCanvasProps {
  label: string;
  filter: number[][] | null;
}

function FilterCanvas({ label, filter }: FilterCanvasProps) {
  const ref = useRef<HTMLCanvasElement | null>(null);
  useEffect(() => {
    if (filter && ref.current) drawFilter(ref.current, filter);
  }, [filter]);
  return (
    <div className="flex flex-col items-center gap-1">
      <canvas ref={ref} width={FILTER_PX} height={FILTER_PX} className="plot" />
      <span className="text-[12px] text-white/45">{label}</span>
    </div>
  );
}

function buildTuningPath(orientations: number[], values: number[]): string {
  const innerW = PLOT_W - PAD_L - PAD_R;
  const innerH = PLOT_H - PAD_T - PAD_B;
  const max = Math.max(...values, 1e-9);
  let d = '';
  for (let i = 0; i < orientations.length; i++) {
    const x = PAD_L + (orientations[i] / 180) * innerW;
    const y = PAD_T + (1 - values[i] / max) * innerH;
    d += (i === 0 ? 'M' : 'L') + x.toFixed(2) + ' ' + y.toFixed(2) + ' ';
  }
  // Close back to first point so the curve loops smoothly across 180°
  if (orientations.length > 0) {
    const x0 = PAD_L + innerW;
    const y0 = PAD_T + (1 - values[0] / max) * innerH;
    d += 'L' + x0.toFixed(2) + ' ' + y0.toFixed(2);
  }
  return d.trim();
}

export function HubelWieselPanel() {
  const [orientation, setOrientation] = useState(45);
  const [response, setResponse] = useState<V1Response | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [running, setRunning] = useState(false);
  const [v1Sample, setV1Sample] = useState<NeuronSearchResponse | null>(null);
  const [v1Error, setV1Error] = useState<string | null>(null);
  const selection = useNeuronSelection();

  useEffect(() => {
    let cancelled = false;
    fetchV1NeuronSample(5)
      .then((sample) => {
        if (!cancelled) setV1Sample(sample);
      })
      .catch((err: unknown) => {
        if (!cancelled) setV1Error(err instanceof Error ? err.message : String(err));
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const onRun = async () => {
    setRunning(true);
    setError(null);
    try {
      setResponse(
        await simulateV1({
          preferred_orientation_deg: orientation,
          spatial_frequency_cyc_per_px: 0.1,
          image_size: 65,
          n_orientations: 36,
        }),
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setRunning(false);
    }
  };

  const innerW = PLOT_W - PAD_L - PAD_R;
  const innerH = PLOT_H - PAD_T - PAD_B;

  const computed = useMemo(() => {
    if (!response) return null;
    return {
      simplePath: buildTuningPath(response.tuning_orientations_deg, response.tuning_simple),
      complexPath: buildTuningPath(response.tuning_orientations_deg, response.tuning_complex),
      preferredX: PAD_L + (response.preferred_orientation_deg / 180) * innerW,
    };
  }, [response, innerW]);

  return (
    <section className="space-y-3">
      <div className="flex items-baseline justify-between">
        <h2 className="kicker">V1 — Hubel & Wiesel 1962</h2>
        <span className="mono text-[11px] text-white/35">Gabor + energy model</span>
      </div>

      <div className="flex justify-around">
        <FilterCanvas label="even (cos)" filter={response?.gabor_even ?? null} />
        <FilterCanvas label="odd (sin)" filter={response?.gabor_odd ?? null} />
      </div>

      <svg width={PLOT_W} height={PLOT_H} viewBox={`0 0 ${PLOT_W} ${PLOT_H}`} className="plot">
        <line x1={PAD_L} x2={PAD_L} y1={PAD_T} y2={PAD_T + innerH} stroke="rgba(255,255,255,0.3)" />
        <line
          x1={PAD_L}
          x2={PAD_L + innerW}
          y1={PAD_T + innerH}
          y2={PAD_T + innerH}
          stroke="rgba(255,255,255,0.3)"
        />
        {[0, 45, 90, 135].map((deg) => {
          const x = PAD_L + (deg / 180) * innerW;
          return (
            <g key={deg}>
              <line
                x1={x}
                x2={x}
                y1={PAD_T + innerH}
                y2={PAD_T + innerH + 3}
                stroke="rgba(255,255,255,0.4)"
              />
              <text
                x={x}
                y={PAD_T + innerH + 14}
                fontSize={9}
                textAnchor="middle"
                fill="rgba(255,255,255,0.5)"
                fontFamily="var(--font-text)"
              >
                {deg}°
              </text>
            </g>
          );
        })}
        <text
          x={4}
          y={PAD_T + 8}
          fontSize={9}
          fill="rgba(255,255,255,0.5)"
          fontFamily="var(--font-text)"
        >
          resp
        </text>

        {!computed && (
          <text
            x={PAD_L + innerW / 2}
            y={PAD_T + innerH / 2 + 3}
            fontSize={10}
            textAnchor="middle"
            fill="rgba(255,255,255,0.35)"
            fontFamily="var(--font-text)"
          >
            no run yet — click compute
          </text>
        )}

        {computed && (
          <>
            <line
              x1={computed.preferredX}
              x2={computed.preferredX}
              y1={PAD_T}
              y2={PAD_T + innerH}
              stroke="rgba(225,5,0,0.4)"
              strokeDasharray="2 3"
            />
            <path
              d={computed.complexPath}
              fill="none"
              stroke="rgba(155,210,255,0.85)"
              strokeWidth={1.4}
            />
            <path d={computed.simplePath} fill="none" stroke="#ffffff" strokeWidth={1.4} />
          </>
        )}
      </svg>

      <div className="flex items-baseline gap-3 text-[10px] font-mono text-white/40">
        <span>
          <span className="inline-block w-3 border-t border-white align-middle" /> simple
        </span>
        <span>
          <span className="inline-block w-3 border-t border-[#9bd2ff] align-middle" /> complex
        </span>
        <span>
          <span className="inline-block w-3 border-t border-dashed border-accent align-middle" />{' '}
          preferred
        </span>
      </div>

      <div className="space-y-3 text-[13px]">
        <label className="flex items-baseline gap-2">
          <span className="meta-xs w-20 self-center">θ_pref °</span>
          <input
            type="number"
            min={0}
            max={179}
            step={5}
            value={orientation}
            onChange={(e) => setOrientation(parseFloat(e.target.value) || 0)}
            className="w-20 field"
          />
          <button onClick={onRun} disabled={running} className="btn btn-sm btn-red ml-auto">
            {running ? 'running…' : 'compute'}
          </button>
        </label>

        {error && <p className="text-accent">{error}</p>}

        {response && (
          <p className="text-[12px] leading-snug text-white/45">
            CNN lineage: LeCun 1989 cited Hubel &amp; Wiesel directly. The first conv-layer filter
            of any modern CNN (VGG, ResNet) converges to a Gabor like the one above.
          </p>
        )}

        {response && (
          <p className="hairline-t pt-3 text-[11.5px] leading-snug text-white/40">
            {response.citation}
          </p>
        )}
      </div>

      <div className="space-y-2 border-t border-white/10 pt-3">
        <div className="flex items-baseline justify-between">
          <h3 className="kicker">Real V1 reconstructions</h3>
          {v1Sample && (
            <span className="mono text-[11px] text-white/35">
              {v1Sample.total_matching.toLocaleString()} on neuromorpho.org
            </span>
          )}
        </div>

        {v1Error && <p className="text-xs text-accent">{v1Error}</p>}
        {!v1Sample && !v1Error && (
          <p className="text-[12px] text-white/45">loading from neuromorpho.org…</p>
        )}

        {v1Sample && (
          <p className="text-[12.5px] leading-snug text-white/45">
            query: brain_region = &quot;primary visual&quot;
          </p>
        )}

        {v1Sample && (
          <ul className="space-y-2.5 text-[12.5px]">
            {v1Sample.results.map((n) => {
              const isActive = selection?.selectedId === n.neuron_id;
              return (
                <li
                  key={n.neuron_id}
                  className={`border-l pl-2 ${isActive ? 'border-accent' : 'border-white/10'}`}
                >
                  <button
                    onClick={() => selection?.selectNeuron(n.neuron_id)}
                    className="text-left text-white hover:text-accent"
                    title="render this neuron in the 3D viewer"
                  >
                    {n.neuron_name}
                  </button>{' '}
                  <span className="text-white/40">#{n.neuron_id}</span>
                  {isActive && <span className="ml-2 text-accent">▸ rendered</span>}
                  <div className="text-white/60">
                    {n.species}
                    {' · '}
                    {n.brain_region.join(' / ')}
                  </div>
                  <div className="text-white/40">
                    {n.cell_type.join(', ') || '—'}
                    {' · '}
                    {n.archive}
                  </div>
                  <div className="space-x-2">
                    {n.reference_doi.length > 0 && (
                      <a
                        href={`https://doi.org/${n.reference_doi[0]}`}
                        target="_blank"
                        rel="noreferrer"
                        className="text-white/70 underline-offset-4 hover:underline"
                      >
                        doi:{n.reference_doi[0]}
                      </a>
                    )}
                    <a
                      href={n.source_url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-white/45 underline-offset-4 hover:underline"
                    >
                      neuromorpho ↗
                    </a>
                  </div>
                </li>
              );
            })}
          </ul>
        )}
      </div>
    </section>
  );
}
