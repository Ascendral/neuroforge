'use client';

import { useEffect, useMemo, useState } from 'react';

import { fetchHippocampalSample, simulateHebbian } from '@/lib/api';
import { useNeuronSelection } from '@/lib/neuron-context';
import type { HebbianResponse, NeuronSearchResponse } from '@/lib/types';

// Anti-theater: weight curves are drawn directly from response.hebb_norm /
// response.oja_norm. The runaway behavior of pure Hebb and the stabilization
// of Oja are real numerical outputs of the rule, not artistic exaggeration.

const PLOT_W = 320;
const PLOT_H = 150;
const PAD_L = 36;
const PAD_R = 8;
const PAD_T = 12;
const PAD_B = 22;

function buildLogPath(
  xs: number[],
  ys: number[],
  xMax: number,
  yMin: number,
  yMax: number,
): string {
  const innerW = PLOT_W - PAD_L - PAD_R;
  const innerH = PLOT_H - PAD_T - PAD_B;
  let d = '';
  for (let i = 0; i < xs.length; i++) {
    const x = PAD_L + (xs[i] / xMax) * innerW;
    // log scale
    const yv = Math.max(ys[i], 1e-3);
    const ynorm = (Math.log10(yv) - yMin) / (yMax - yMin);
    const y = PAD_T + (1 - ynorm) * innerH;
    d += (i === 0 ? 'M' : 'L') + x.toFixed(2) + ' ' + y.toFixed(2) + ' ';
  }
  return d.trim();
}

export function HebbianPanel() {
  const [response, setResponse] = useState<HebbianResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [running, setRunning] = useState(false);
  const [iters, setIters] = useState(2000);
  const [eta, setEta] = useState(0.005);
  const [sample, setSample] = useState<NeuronSearchResponse | null>(null);
  const [sampleError, setSampleError] = useState<string | null>(null);
  const selection = useNeuronSelection();

  useEffect(() => {
    let cancelled = false;
    fetchHippocampalSample(5)
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
        await simulateHebbian({
          n_iterations: iters,
          learning_rate: eta,
          correlation: 0.8,
          input_dim: 2,
          seed: 42,
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
    const xMax = response.iterations[response.iterations.length - 1] || 1;
    const peakNorm = Math.max(...response.hebb_norm, ...response.oja_norm, 1.5);
    const yMin = Math.log10(0.05);
    const yMax = Math.log10(peakNorm * 1.2);
    return {
      hebbPath: buildLogPath(response.iterations, response.hebb_norm, xMax, yMin, yMax),
      ojaPath: buildLogPath(response.iterations, response.oja_norm, xMax, yMin, yMax),
      xMax,
      yMin,
      yMax,
      // Reference y-positions
      oneY: PAD_T + (1 - (Math.log10(1) - yMin) / (yMax - yMin)) * innerH,
    };
  }, [response, innerH]);

  return (
    <section className="space-y-3">
      <div className="flex items-baseline justify-between">
        <h2 className="kicker">Hebbian / LTP — Hebb 1949 · Bliss-Lømo 1973 · Oja 1982</h2>
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
        <text
          x={4}
          y={PAD_T + 8}
          fontSize={9}
          fill="rgba(255,255,255,0.5)"
          fontFamily="var(--font-text)"
        >
          ||w||
        </text>
        <text
          x={PLOT_W - 24}
          y={PAD_T + innerH + 14}
          fontSize={9}
          fill="rgba(255,255,255,0.5)"
          fontFamily="var(--font-text)"
        >
          iter
        </text>

        {!computed && (
          <text
            x={PAD_L + innerW / 2}
            y={PAD_T + innerH / 2 + 4}
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
              x1={PAD_L}
              x2={PAD_L + innerW}
              y1={computed.oneY}
              y2={computed.oneY}
              stroke="rgba(155,210,255,0.25)"
              strokeDasharray="2 3"
            />
            <text
              x={PAD_L - 4}
              y={computed.oneY + 3}
              fontSize={9}
              textAnchor="end"
              fill="rgba(155,210,255,0.6)"
              fontFamily="var(--font-text)"
            >
              1
            </text>
            <path d={computed.ojaPath} fill="none" stroke="#9bd2ff" strokeWidth={1.4} />
            <path d={computed.hebbPath} fill="none" stroke="#ff2d2d" strokeWidth={1.4} />
          </>
        )}
      </svg>

      <div className="flex items-baseline gap-3 text-[10px] font-mono text-white/40">
        <span>
          <span className="inline-block w-3 border-t border-accent align-middle" /> pure Hebb
          (runaway)
        </span>
        <span>
          <span className="inline-block w-3 border-t border-[#9bd2ff] align-middle" /> Oja (stable
          at ‖w‖=1)
        </span>
      </div>

      <div className="space-y-3 text-[13px]">
        <label className="flex items-baseline gap-2">
          <span className="meta-xs w-16 self-center">iters</span>
          <input
            type="number"
            step={500}
            min={100}
            max={20000}
            value={iters}
            onChange={(e) => setIters(parseInt(e.target.value) || 100)}
            className="w-24 field"
          />
        </label>
        <label className="flex items-baseline gap-2">
          <span className="meta-xs w-16 self-center">η</span>
          <input
            type="number"
            step={0.001}
            min={0.001}
            max={0.1}
            value={eta}
            onChange={(e) => setEta(parseFloat(e.target.value) || 0.001)}
            className="w-24 field"
          />
          <button onClick={onRun} disabled={running} className="btn btn-sm btn-red ml-auto">
            {running ? 'running…' : 'run learning'}
          </button>
        </label>

        {error && <p className="text-accent">{error}</p>}

        {response && (
          <dl className="space-y-1 text-white/70">
            <div className="flex gap-2">
              <dt className="w-32 text-white/40">final ‖w‖ (Hebb)</dt>
              <dd className="text-accent">
                {response.hebb_norm[response.hebb_norm.length - 1].toExponential(2)}
              </dd>
            </div>
            <div className="flex gap-2">
              <dt className="w-32 text-white/40">final ‖w‖ (Oja)</dt>
              <dd className="text-[#9bd2ff]">
                {response.oja_norm[response.oja_norm.length - 1].toFixed(4)}
              </dd>
            </div>
            <div className="flex gap-2">
              <dt className="w-32 text-white/40">final angle Hebb°</dt>
              <dd className="text-white">
                {response.hebb_angle_deg[response.hebb_angle_deg.length - 1].toFixed(2)}
              </dd>
            </div>
            <div className="flex gap-2">
              <dt className="w-32 text-white/40">final angle Oja°</dt>
              <dd className="text-white">
                {response.oja_angle_deg[response.oja_angle_deg.length - 1].toFixed(2)}
              </dd>
            </div>
            <div className="flex gap-2">
              <dt className="w-32 text-white/40">PC direction</dt>
              <dd className="text-white/70">
                [{response.principal_direction.map((v) => v.toFixed(3)).join(', ')}]
              </dd>
            </div>
          </dl>
        )}

        {response && (
          <p className="hairline-t pt-3 text-[11.5px] leading-snug text-white/40">
            {response.citation}
          </p>
        )}
      </div>

      <div className="space-y-2 border-t border-white/10 pt-3">
        <div className="flex items-baseline justify-between">
          <h3 className="kicker">Real hippocampal pyramidals</h3>
          {sample && (
            <span className="mono text-[11px] text-white/35">
              {sample.total_matching.toLocaleString()} on neuromorpho.org
            </span>
          )}
        </div>

        {sampleError && <p className="text-xs text-accent">{sampleError}</p>}
        {!sample && !sampleError && (
          <p className="text-[12px] text-white/45">loading from neuromorpho.org…</p>
        )}

        {sample && (
          <p className="text-[12.5px] leading-snug text-white/45">
            query: brain_region = &quot;hippocampus&quot; AND cell_type = &quot;pyramidal&quot;
          </p>
        )}

        {sample && (
          <ul className="space-y-2.5 text-[12.5px]">
            {sample.results.map((n) => {
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
