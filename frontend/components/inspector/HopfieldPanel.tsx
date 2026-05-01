'use client';

import { useEffect, useMemo, useRef, useState } from 'react';

import { fetchCA3Sample, simulateHopfield } from '@/lib/api';
import type { HopfieldResponse, NeuronSearchResponse } from '@/lib/types';

// Anti-theater: every cell rendered comes from response.target_pattern,
// response.corrupted_input, or response.final_state. Energy curve is
// response.energies. Nothing synthetic.

const PATTERN_PX = 96;
const PLOT_W = 320;
const PLOT_H = 110;
const PAD_L = 36;
const PAD_R = 8;
const PAD_T = 8;
const PAD_B = 22;

function drawBipolar(canvas: HTMLCanvasElement, pattern: number[]) {
  const n = Math.round(Math.sqrt(pattern.length));
  const ctx = canvas.getContext('2d');
  if (!ctx) return;
  const img = ctx.createImageData(n, n);
  for (let i = 0; i < pattern.length; i++) {
    const v = pattern[i];
    const g = v > 0 ? 240 : 24;
    const j = i * 4;
    img.data[j] = g;
    img.data[j + 1] = g;
    img.data[j + 2] = g;
    img.data[j + 3] = 255;
  }
  const off = document.createElement('canvas');
  off.width = n;
  off.height = n;
  const offCtx = off.getContext('2d');
  if (!offCtx) return;
  offCtx.putImageData(img, 0, 0);
  ctx.imageSmoothingEnabled = false;
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.drawImage(off, 0, 0, canvas.width, canvas.height);
}

function PatternCanvas({ label, pattern }: { label: string; pattern: number[] | null }) {
  const ref = useRef<HTMLCanvasElement | null>(null);
  useEffect(() => {
    if (pattern && ref.current) drawBipolar(ref.current, pattern);
  }, [pattern]);
  return (
    <div className="flex flex-col items-center gap-1">
      <canvas
        ref={ref}
        width={PATTERN_PX}
        height={PATTERN_PX}
        className="rounded border border-white/10 bg-black"
      />
      <span className="font-mono text-[10px] text-white/40">{label}</span>
    </div>
  );
}

function buildEnergyPath(values: number[]): string {
  const innerW = PLOT_W - PAD_L - PAD_R;
  const innerH = PLOT_H - PAD_T - PAD_B;
  const min = Math.min(...values);
  const max = Math.max(...values);
  const span = Math.max(max - min, 1e-9);
  let d = '';
  for (let i = 0; i < values.length; i++) {
    const x = PAD_L + (i / Math.max(values.length - 1, 1)) * innerW;
    const y = PAD_T + ((max - values[i]) / span) * innerH;
    d += (i === 0 ? 'M' : 'L') + x.toFixed(2) + ' ' + y.toFixed(2) + ' ';
  }
  return d.trim();
}

export function HopfieldPanel() {
  const [response, setResponse] = useState<HopfieldResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [running, setRunning] = useState(false);
  const [nNeurons, setNNeurons] = useState(64);
  const [nPatterns, setNPatterns] = useState(5);
  const [corruption, setCorruption] = useState(0.2);

  const [sample, setSample] = useState<NeuronSearchResponse | null>(null);
  const [sampleError, setSampleError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetchCA3Sample(5)
      .then((s) => {
        if (!cancelled) setSample(s);
      })
      .catch((err: unknown) => {
        if (!cancelled) setSampleError(err instanceof Error ? err.message : String(err));
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
        await simulateHopfield({
          n_neurons: nNeurons,
          n_patterns: nPatterns,
          corruption_fraction: corruption,
          target_index: 0,
          max_sweeps: 6,
          seed: 42,
        }),
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setRunning(false);
    }
  };

  const energyPath = useMemo(
    () => (response ? buildEnergyPath(response.energies) : null),
    [response],
  );

  const innerW = PLOT_W - PAD_L - PAD_R;
  const innerH = PLOT_H - PAD_T - PAD_B;

  return (
    <section className="space-y-3">
      <div className="flex items-baseline justify-between">
        <h2 className="text-xs uppercase tracking-widest text-white/40">Hopfield 1982 attractor</h2>
        <span className="font-mono text-[10px] text-white/30">α = K/N (critical 0.138)</span>
      </div>

      <div className="flex justify-around">
        <PatternCanvas label="stored" pattern={response?.target_pattern ?? null} />
        <PatternCanvas label="corrupted" pattern={response?.corrupted_input ?? null} />
        <PatternCanvas label="recovered" pattern={response?.final_state ?? null} />
      </div>

      <svg
        width={PLOT_W}
        height={PLOT_H}
        viewBox={`0 0 ${PLOT_W} ${PLOT_H}`}
        className="rounded border border-white/10 bg-black"
      >
        <line x1={PAD_L} x2={PAD_L} y1={PAD_T} y2={PAD_T + innerH} stroke="rgba(255,255,255,0.3)" />
        <line x1={PAD_L} x2={PAD_L + innerW} y1={PAD_T + innerH} y2={PAD_T + innerH} stroke="rgba(255,255,255,0.3)" />
        <text x={4} y={PAD_T + 8} fontSize={9} fill="rgba(255,255,255,0.5)" fontFamily="monospace">E</text>
        <text x={PLOT_W - 24} y={PAD_T + innerH + 14} fontSize={9} fill="rgba(255,255,255,0.5)" fontFamily="monospace">step</text>

        {!energyPath && (
          <text x={PAD_L + innerW / 2} y={PAD_T + innerH / 2 + 4} fontSize={10} textAnchor="middle" fill="rgba(255,255,255,0.35)" fontFamily="monospace">
            no run yet — click recall
          </text>
        )}

        {energyPath && <path d={energyPath} fill="none" stroke="#9bd2ff" strokeWidth={1.4} />}
      </svg>

      <div className="space-y-2 font-mono text-xs">
        <label className="flex items-baseline gap-2">
          <span className="w-16 text-white/40">N</span>
          <input
            type="number"
            min={16}
            max={400}
            step={1}
            value={nNeurons}
            onChange={(e) => {
              const v = parseInt(e.target.value) || 16;
              const sq = Math.round(Math.sqrt(v));
              setNNeurons(sq * sq);
            }}
            className="w-24 rounded border border-white/10 bg-black px-2 py-1 text-white outline-none focus:border-white/40"
          />
          <span className="text-white/30">→ {Math.round(Math.sqrt(nNeurons))}×{Math.round(Math.sqrt(nNeurons))}</span>
        </label>
        <label className="flex items-baseline gap-2">
          <span className="w-16 text-white/40">K</span>
          <input
            type="number"
            min={1}
            max={80}
            step={1}
            value={nPatterns}
            onChange={(e) => setNPatterns(parseInt(e.target.value) || 1)}
            className="w-24 rounded border border-white/10 bg-black px-2 py-1 text-white outline-none focus:border-white/40"
          />
          <span className="text-white/30">α={(nPatterns / nNeurons).toFixed(3)}</span>
        </label>
        <label className="flex items-baseline gap-2">
          <span className="w-16 text-white/40">corrupt</span>
          <input
            type="number"
            min={0}
            max={1}
            step={0.05}
            value={corruption}
            onChange={(e) => setCorruption(Math.max(0, Math.min(1, parseFloat(e.target.value) || 0)))}
            className="w-24 rounded border border-white/10 bg-black px-2 py-1 text-white outline-none focus:border-white/40"
          />
          <button
            onClick={onRun}
            disabled={running}
            className="ml-auto rounded border border-white/30 px-3 py-1 text-white hover:bg-white/10 disabled:cursor-not-allowed disabled:opacity-40"
          >
            {running ? 'running…' : 'recall'}
          </button>
        </label>

        {error && <p className="text-accent">{error}</p>}

        {response && (
          <dl className="space-y-1 text-white/70">
            <div className="flex gap-2">
              <dt className="w-24 text-white/40">α (K/N)</dt>
              <dd className={response.target_capacity_alpha > response.critical_capacity ? 'text-accent' : 'text-white'}>
                {response.target_capacity_alpha.toFixed(3)} {response.target_capacity_alpha > response.critical_capacity ? '(over critical)' : ''}
              </dd>
            </div>
            <div className="flex gap-2">
              <dt className="w-24 text-white/40">overlap</dt>
              <dd className={response.converged ? 'text-[#9bd2ff]' : 'text-accent'}>{response.final_overlap.toFixed(3)}</dd>
            </div>
            <div className="flex gap-2">
              <dt className="w-24 text-white/40">converged</dt>
              <dd className="text-white">{response.converged ? 'yes' : 'no'}</dd>
            </div>
            <div className="flex gap-2">
              <dt className="w-24 text-white/40">ΔE</dt>
              <dd className="text-white">
                {response.energies[0].toFixed(2)} → {response.energies[response.energies.length - 1].toFixed(2)}
              </dd>
            </div>
          </dl>
        )}

        {response && (
          <p className="border-t border-white/10 pt-2 text-[10px] leading-snug text-white/40">
            {response.citation}
          </p>
        )}
      </div>

      <div className="space-y-2 border-t border-white/10 pt-3">
        <div className="flex items-baseline justify-between">
          <h3 className="text-xs uppercase tracking-widest text-white/40">Real CA3 pyramidals</h3>
          {sample && (
            <span className="font-mono text-[10px] text-white/30">
              {sample.total_matching.toLocaleString()} on neuromorpho.org
            </span>
          )}
        </div>

        {sampleError && <p className="text-xs text-accent">{sampleError}</p>}
        {!sample && !sampleError && (
          <p className="font-mono text-[10px] text-white/40">loading from neuromorpho.org…</p>
        )}

        {sample && (
          <p className="font-mono text-[10px] leading-snug text-white/40">
            query: brain_region = &quot;CA3&quot; AND cell_type = &quot;pyramidal&quot;
          </p>
        )}

        {sample && (
          <ul className="space-y-2 font-mono text-[10px]">
            {sample.results.map((n) => (
              <li key={n.neuron_id} className="border-l border-white/10 pl-2">
                <a href={n.source_url} target="_blank" rel="noreferrer" className="text-white underline-offset-2 hover:underline">
                  {n.neuron_name}
                </a>{' '}
                <span className="text-white/40">#{n.neuron_id}</span>
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
                {n.reference_doi.length > 0 && (
                  <div>
                    <a href={`https://doi.org/${n.reference_doi[0]}`} target="_blank" rel="noreferrer" className="text-white/70 underline-offset-2 hover:underline">
                      doi:{n.reference_doi[0]}
                    </a>
                  </div>
                )}
              </li>
            ))}
          </ul>
        )}
      </div>
    </section>
  );
}
