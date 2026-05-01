'use client';

// Empty firing-plot placeholder. Phase 4 wires the Hodgkin-Huxley simulator
// (Brian2) and streams membrane potential through this component. Until then
// we render axes only and an honest "no simulation data" label — per CLAUDE.md
// we do NOT fake a fictitious membrane trace.

interface FiringPlotProps {
  selectedPointId: number | null;
}

const PLOT_W = 320;
const PLOT_H = 110;
const PAD_L = 32;
const PAD_R = 8;
const PAD_T = 8;
const PAD_B = 22;

export function FiringPlot({ selectedPointId }: FiringPlotProps) {
  const innerW = PLOT_W - PAD_L - PAD_R;
  const innerH = PLOT_H - PAD_T - PAD_B;

  return (
    <section aria-label="Firing plot" className="space-y-2">
      <div className="flex items-baseline justify-between">
        <h3 className="text-xs uppercase tracking-widest text-white/40">Membrane potential</h3>
        <span className="font-mono text-[10px] text-white/30">
          {selectedPointId === null ? 'no point selected' : `point ${selectedPointId}`}
        </span>
      </div>
      <svg
        width={PLOT_W}
        height={PLOT_H}
        viewBox={`0 0 ${PLOT_W} ${PLOT_H}`}
        className="rounded border border-white/10 bg-black"
      >
        {/* Y axis */}
        <line
          x1={PAD_L}
          x2={PAD_L}
          y1={PAD_T}
          y2={PAD_T + innerH}
          stroke="rgba(255,255,255,0.3)"
          strokeWidth={1}
        />
        {/* X axis */}
        <line
          x1={PAD_L}
          x2={PAD_L + innerW}
          y1={PAD_T + innerH}
          y2={PAD_T + innerH}
          stroke="rgba(255,255,255,0.3)"
          strokeWidth={1}
        />
        {/* Y label: mV */}
        <text x={4} y={PAD_T + 8} fontSize={9} fill="rgba(255,255,255,0.5)" fontFamily="monospace">
          mV
        </text>
        {/* X label: ms */}
        <text
          x={PLOT_W - 14}
          y={PAD_T + innerH + 14}
          fontSize={9}
          fill="rgba(255,255,255,0.5)"
          fontFamily="monospace"
        >
          ms
        </text>
        {/* Empty-state caption */}
        <text
          x={PAD_L + innerW / 2}
          y={PAD_T + innerH / 2 + 4}
          fontSize={10}
          textAnchor="middle"
          fill="rgba(255,255,255,0.35)"
          fontFamily="monospace"
        >
          phase 4 wires hodgkin-huxley
        </text>
      </svg>
    </section>
  );
}
