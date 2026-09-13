'use client';

import { useEffect, useRef, useState } from 'react';

import { LinePlot } from '@/components/scales/LinePlot';
import { simulateModernHopfield } from '@/lib/api';
import type { ModernHopfieldResponse } from '@/lib/types';

// Anti-theater: every pixel here is response data — target / corrupted /
// recovered states, the softmax attention row of the first update, the
// energy per update, and the classic-vs-modern capacity sweep measured by
// the backend on identical random patterns.

const PATTERN_PX = 72;

function drawBipolar(canvas: HTMLCanvasElement, pattern: number[]) {
  const n = Math.round(Math.sqrt(pattern.length));
  const ctx = canvas.getContext('2d');
  if (!ctx) return;
  const img = ctx.createImageData(n, n);
  for (let i = 0; i < pattern.length; i++) {
    const g = pattern[i] > 0 ? 240 : 24;
    const j = i * 4;
    img.data[j] = g;
    img.data[j + 1] = g;
    img.data[j + 2] = g;
    img.data[j + 3] = 255;
  }
  const off = document.createElement('canvas');
  off.width = n;
  off.height = n;
  off.getContext('2d')?.putImageData(img, 0, 0);
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
      <span className="font-mono text-[9px] text-white/40">{label}</span>
    </div>
  );
}

export function ModernHopfieldPanel() {
  const [d, setD] = useState(64);
  const [n, setN] = useState(64);
  const [corruption, setCorruption] = useState(0.2);
  const [beta, setBeta] = useState(1.0);
  const [response, setResponse] = useState<ModernHopfieldResponse | null>(null);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const onRun = async () => {
    setRunning(true);
    setError(null);
    try {
      setResponse(
        await simulateModernHopfield({
          d,
          n_patterns: n,
          corruption_fraction: corruption,
          beta,
          n_updates: 3,
          sweep: true,
          sweep_trials: 6,
        }),
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setRunning(false);
    }
  };

  const sweep = response?.sweep ?? null;

  return (
    <section className="space-y-3">
      <div className="flex items-baseline justify-between">
        <h2 className="text-xs uppercase tracking-widest text-white/40">
          Modern Hopfield ≡ attention
        </h2>
        <span className="font-mono text-[10px] text-white/30">ξ ← X·softmax(β Xᵀξ)</span>
      </div>

      <div className="flex justify-around">
        <PatternCanvas label="stored" pattern={response?.target ?? null} />
        <PatternCanvas label="corrupted" pattern={response?.corrupted ?? null} />
        <PatternCanvas label="modern" pattern={response?.modern_final_sign ?? null} />
        <PatternCanvas label="classic 1982" pattern={response?.classic_final ?? null} />
      </div>

      {response && (
        <div className="space-y-1">
          <div className="font-mono text-[9px] uppercase tracking-widest text-white/40">
            attention row of the first update (softmax over {response.n_patterns} stored patterns)
          </div>
          <svg
            width={320}
            height={28}
            viewBox="0 0 320 28"
            className="rounded border border-white/10 bg-black"
          >
            {response.modern_attention_weights.map((w, i) => {
              const bw = 320 / response.modern_attention_weights.length;
              return (
                <rect
                  key={i}
                  x={i * bw}
                  y={28 - w * 26}
                  width={Math.max(bw - 0.5, 0.5)}
                  height={w * 26}
                  fill={i === response.target_index ? '#ff2d2d' : 'rgba(255,255,255,0.6)'}
                />
              );
            })}
          </svg>
          <div className="font-mono text-[9px] text-white/40">
            max |update − attention(Q=ξ, K=V=X)| ={' '}
            {response.attention_max_abs_diff.toExponential(1)} — the two formulas are the same
            computation.
          </div>
        </div>
      )}

      <LinePlot
        width={320}
        height={120}
        xLabel="α = N/d"
        yLabel="recall"
        yMin={0}
        yMax={1}
        markers={[
          {
            x: response?.classic_critical_alpha ?? 0.138,
            label: '0.138',
            color: 'rgba(255,45,45,0.7)',
          },
        ]}
        series={
          sweep
            ? [
                {
                  xs: sweep.alphas,
                  ys: sweep.classic_success,
                  color: 'rgba(255,255,255,0.55)',
                  label: 'classic 1982',
                },
                {
                  xs: sweep.alphas,
                  ys: sweep.modern_success,
                  color: '#ff2d2d',
                  label: 'modern 2021',
                },
              ]
            : []
        }
        empty="no run yet — click recall"
      />

      <div className="space-y-2 font-mono text-xs">
        <label className="flex items-baseline gap-2">
          <span className="w-16 text-white/40">d</span>
          <input
            type="number"
            min={16}
            max={256}
            value={d}
            onChange={(e) => {
              const v = parseInt(e.target.value) || 16;
              const sq = Math.max(4, Math.round(Math.sqrt(v)));
              setD(sq * sq);
            }}
            className="w-24 rounded border border-white/10 bg-black px-2 py-1 text-white outline-none focus:border-white/40"
          />
          <span className="text-white/30">
            {Math.round(Math.sqrt(d))}×{Math.round(Math.sqrt(d))}
          </span>
        </label>
        <label className="flex items-baseline gap-2">
          <span className="w-16 text-white/40">N</span>
          <input
            type="number"
            min={1}
            max={1024}
            value={n}
            onChange={(e) => setN(parseInt(e.target.value) || 1)}
            className="w-24 rounded border border-white/10 bg-black px-2 py-1 text-white outline-none focus:border-white/40"
          />
          <span className={n / d > 0.138 ? 'text-accent' : 'text-white/30'}>
            α={(n / d).toFixed(2)}
          </span>
        </label>
        <label className="flex items-baseline gap-2">
          <span className="w-16 text-white/40">corrupt</span>
          <input
            type="number"
            min={0}
            max={1}
            step={0.05}
            value={corruption}
            onChange={(e) =>
              setCorruption(Math.max(0, Math.min(1, parseFloat(e.target.value) || 0)))
            }
            className="w-24 rounded border border-white/10 bg-black px-2 py-1 text-white outline-none focus:border-white/40"
          />
        </label>
        <label className="flex items-baseline gap-2">
          <span className="w-16 text-white/40">β</span>
          <input
            type="number"
            min={0.01}
            max={50}
            step={0.05}
            value={beta}
            onChange={(e) => setBeta(Math.max(0.01, parseFloat(e.target.value) || 0.01))}
            className="w-24 rounded border border-white/10 bg-black px-2 py-1 text-white outline-none focus:border-white/40"
          />
          <span className="text-white/30">1/√d = {(1 / Math.sqrt(d)).toFixed(3)}</span>
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
              <dt className="w-28 text-white/40">modern overlap</dt>
              <dd
                className={
                  response.modern_overlaps[response.modern_overlaps.length - 1] > 0.95
                    ? 'text-white'
                    : 'text-accent'
                }
              >
                {response.modern_overlaps.map((o) => o.toFixed(2)).join(' → ')}
              </dd>
            </div>
            <div className="flex gap-2">
              <dt className="w-28 text-white/40">classic overlap</dt>
              <dd className={response.classic_overlap > 0.95 ? 'text-white' : 'text-accent'}>
                {response.classic_overlap.toFixed(3)}
              </dd>
            </div>
            <div className="flex gap-2">
              <dt className="w-28 text-white/40">energy</dt>
              <dd className="text-white">
                {response.modern_energies.map((e) => e.toFixed(1)).join(' → ')}
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
    </section>
  );
}
