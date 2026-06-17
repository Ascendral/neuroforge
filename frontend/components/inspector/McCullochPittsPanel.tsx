'use client';

import { useEffect, useState } from 'react';

import { fetchMCPGate, fetchXorImpossibility } from '@/lib/api';
import type { MCPGateResponse, MCPXorSearchResponse } from '@/lib/types';

const GATES = ['AND', 'OR', 'NOT', 'NAND', 'NOR'] as const;
type GateName = (typeof GATES)[number];

export function McCullochPittsPanel() {
  const [gate, setGate] = useState<GateName>('AND');
  const [result, setResult] = useState<MCPGateResponse | null>(null);
  const [resultError, setResultError] = useState<string | null>(null);
  const [xor, setXor] = useState<MCPXorSearchResponse | null>(null);
  const [xorError, setXorError] = useState<string | null>(null);
  const [running, setRunning] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setResultError(null);
    fetchMCPGate(gate)
      .then((r) => {
        if (!cancelled) setResult(r);
      })
      .catch((err: unknown) => {
        if (!cancelled) setResultError(err instanceof Error ? err.message : String(err));
      });
    return () => {
      cancelled = true;
    };
  }, [gate]);

  const onRunXorSearch = async () => {
    setRunning(true);
    setXorError(null);
    try {
      setXor(await fetchXorImpossibility());
    } catch (err) {
      setXorError(err instanceof Error ? err.message : String(err));
    } finally {
      setRunning(false);
    }
  };

  return (
    <section className="space-y-3">
      <div className="flex items-baseline justify-between">
        <h2 className="text-xs uppercase tracking-widest text-white/40">
          McCulloch-Pitts 1943 — threshold logic
        </h2>
        <span className="font-mono text-[10px] text-white/30">historical abstraction</span>
      </div>

      <div className="flex flex-wrap gap-1">
        {GATES.map((g) => (
          <button
            key={g}
            onClick={() => setGate(g)}
            className={`rounded border px-2 py-1 font-mono text-[10px] ${
              gate === g
                ? 'border-accent bg-accent/10 text-white'
                : 'border-white/20 text-white/60 hover:bg-white/5'
            }`}
          >
            {g}
          </button>
        ))}
      </div>

      {resultError && <p className="font-mono text-xs text-accent">{resultError}</p>}

      {result && (
        <div className="space-y-2 font-mono text-xs">
          <p className="text-white/70">{result.description}</p>

          <div className="rounded border border-white/10 bg-black p-2">
            <div className="grid grid-cols-[auto_auto_auto] gap-x-4 text-[10px]">
              <div className="text-white/40">{result.n_inputs === 1 ? 'A' : 'A B'}</div>
              <div className="text-white/40">expect</div>
              <div className="text-white/40">produced</div>
              {result.inputs_table.map((row, i) => (
                <div key={i} className="contents">
                  <div className="text-white">{row.join(' ')}</div>
                  <div className="text-white/60">{result.expected[i]}</div>
                  <div
                    className={
                      result.expected[i] === result.produced[i] ? 'text-[#9bd2ff]' : 'text-accent'
                    }
                  >
                    {result.produced[i]} {result.expected[i] === result.produced[i] ? '✓' : '✗'}
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="flex gap-3 text-[10px]">
            <span className="text-white/40">w =</span>
            <span className="text-white">[{result.weights.join(', ')}]</span>
            <span className="text-white/40">θ =</span>
            <span className="text-white">{result.threshold}</span>
            <span className={`ml-auto ${result.passes ? 'text-[#9bd2ff]' : 'text-accent'}`}>
              {result.passes ? 'computed correctly' : 'fails'}
            </span>
          </div>
        </div>
      )}

      <div className="space-y-2 border-t border-white/10 pt-3">
        <div className="flex items-baseline justify-between">
          <h3 className="text-xs uppercase tracking-widest text-white/40">
            XOR — single-layer impossibility
          </h3>
          <button
            onClick={onRunXorSearch}
            disabled={running}
            className="rounded border border-white/30 px-2 py-1 font-mono text-[10px] text-white hover:bg-white/10 disabled:cursor-not-allowed disabled:opacity-40"
          >
            {running ? 'searching…' : 'brute-force search'}
          </button>
        </div>

        {xorError && <p className="font-mono text-xs text-accent">{xorError}</p>}

        {xor && (
          <div className="space-y-1 font-mono text-[10px]">
            <p className="text-white/60">
              target XOR truth table: <span className="text-white">{xor.target.join(' ')}</span>
            </p>
            <p className="text-white/60">
              searched <span className="text-white">{xor.combinations_tried.toLocaleString()}</span>{' '}
              (w₁, w₂, θ) triples in [{xor.weight_range.join(', ')}] step {xor.step}
            </p>
            <p className="text-white/60">
              best match:{' '}
              <span className={xor.best_match_correct === 4 ? 'text-[#9bd2ff]' : 'text-accent'}>
                {xor.best_match_correct} / 4
              </span>{' '}
              at w=[{xor.best_weights?.join(', ')}], θ={xor.best_threshold}
            </p>
            <p className={xor.no_solution ? 'text-accent' : 'text-[#9bd2ff]'}>
              {xor.no_solution
                ? 'no single-layer M-P neuron computes XOR (Minsky-Papert 1969)'
                : 'unexpected: XOR was solved (would falsify Minsky-Papert)'}
            </p>
          </div>
        )}
      </div>

      {result && (
        <p className="border-t border-white/10 pt-2 text-[10px] leading-snug text-white/40">
          {result.citation}
        </p>
      )}
    </section>
  );
}
