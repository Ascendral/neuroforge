'use client';

import { useState } from 'react';

import { LinePlot } from '@/components/scales/LinePlot';
import { simulateDopamineRPE } from '@/lib/api';
import type { DopamineRPEResponse } from '@/lib/types';

// Anti-theater: the three panels below are the backend TD(0) model's δ(t)
// for the three Schultz-Dayan-Montague 1997 conditions. Nothing is drawn
// until the response arrives; the parameter note printed under the plots is
// the backend's own statement of which constants are the demo's, not the
// paper's.

function Condition({ title, r, ys }: { title: string; r: DopamineRPEResponse; ys: number[] }) {
  const cue = r.cue_step * r.bin_ms;
  const rew = r.reward_step * r.bin_ms;
  return (
    <div className="space-y-1">
      <div className="font-mono text-[9px] uppercase tracking-widest text-white/50">{title}</div>
      <LinePlot
        width={320}
        height={90}
        xLabel="ms"
        yLabel="δ"
        yMin={-1.05}
        yMax={1.05}
        zeroLine
        markers={[
          { x: cue, label: 'cue', color: 'rgba(155,210,255,0.7)' },
          { x: rew, label: 'reward', color: 'rgba(255,216,107,0.7)' },
        ]}
        series={[{ xs: r.times_ms, ys, color: '#ff2d2d', width: 1.6 }]}
      />
    </div>
  );
}

export function DopaminePanel() {
  const [trials, setTrials] = useState(200);
  const [gamma, setGamma] = useState(0.98);
  const [response, setResponse] = useState<DopamineRPEResponse | null>(null);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const onRun = async () => {
    setRunning(true);
    setError(null);
    try {
      setResponse(await simulateDopamineRPE({ n_training_trials: trials, gamma }));
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setRunning(false);
    }
  };

  return (
    <section className="space-y-3">
      <div className="flex items-baseline justify-between">
        <h2 className="text-xs uppercase tracking-widest text-white/40">
          Dopamine = reward prediction error
        </h2>
        <span className="font-mono text-[10px] text-white/30">δ = r + γV(t) − V(t−1)</span>
      </div>

      {response ? (
        <div className="space-y-2">
          <Condition
            title="1 · unpredicted reward (naive)"
            r={response}
            ys={response.delta_unpredicted}
          />
          <Condition
            title="2 · predicted reward (after training)"
            r={response}
            ys={response.delta_predicted}
          />
          <Condition
            title="3 · predicted reward omitted"
            r={response}
            ys={response.delta_omitted}
          />
          <div className="font-mono text-[9px] uppercase tracking-widest text-white/50">
            learning: δ moves from reward to cue over trials
          </div>
          <LinePlot
            width={320}
            height={90}
            xLabel="trial"
            yLabel="δ"
            yMin={0}
            yMax={1.05}
            series={[
              {
                xs: response.delta_at_reward_per_trial.map((_, i) => i + 1),
                ys: response.delta_at_reward_per_trial,
                color: 'rgba(255,216,107,0.9)',
                label: 'at reward',
              },
              {
                xs: response.delta_at_cue_per_trial.map((_, i) => i + 1),
                ys: response.delta_at_cue_per_trial,
                color: 'rgba(155,210,255,0.9)',
                label: 'at cue',
              },
            ]}
          />
        </div>
      ) : (
        <LinePlot width={320} height={90} series={[]} empty="no run yet — click train" />
      )}

      <div className="space-y-2 font-mono text-xs">
        <label className="flex items-baseline gap-2">
          <span className="w-16 text-white/40">trials</span>
          <input
            type="number"
            min={1}
            max={2000}
            value={trials}
            onChange={(e) => setTrials(Math.max(1, parseInt(e.target.value) || 1))}
            className="w-24 rounded border border-white/10 bg-black px-2 py-1 text-white outline-none focus:border-white/40"
          />
        </label>
        <label className="flex items-baseline gap-2">
          <span className="w-16 text-white/40">γ</span>
          <input
            type="number"
            min={0.5}
            max={1}
            step={0.01}
            value={gamma}
            onChange={(e) =>
              setGamma(Math.min(1, Math.max(0.5, parseFloat(e.target.value) || 0.5)))
            }
            className="w-24 rounded border border-white/10 bg-black px-2 py-1 text-white outline-none focus:border-white/40"
          />
          <button
            onClick={onRun}
            disabled={running}
            className="ml-auto rounded border border-white/30 px-3 py-1 text-white hover:bg-white/10 disabled:cursor-not-allowed disabled:opacity-40"
          >
            {running ? 'training…' : 'train'}
          </button>
        </label>
        {error && <p className="text-accent">{error}</p>}
        {response && (
          <>
            <p className="text-[10px] leading-snug text-white/50">{response.parameter_note}</p>
            <p className="border-t border-white/10 pt-2 text-[10px] leading-snug text-white/40">
              {response.citation}
            </p>
          </>
        )}
      </div>
    </section>
  );
}
