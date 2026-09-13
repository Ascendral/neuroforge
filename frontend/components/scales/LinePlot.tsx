'use client';

// Generic small SVG line plot used by the new simulator panels. Draws ONLY the
// series it is given — there is no default or placeholder curve.

export interface Series {
  xs: number[];
  ys: number[];
  color: string;
  dash?: string;
  label?: string;
  width?: number;
}

export interface VMarker {
  x: number;
  label: string;
  color?: string;
}

interface LinePlotProps {
  series: Series[];
  width?: number;
  height?: number;
  xLabel?: string;
  yLabel?: string;
  yMin?: number;
  yMax?: number;
  xMin?: number;
  xMax?: number;
  markers?: VMarker[];
  zeroLine?: boolean;
  empty?: string;
}

const PAD_L = 36;
const PAD_R = 8;
const PAD_T = 10;
const PAD_B = 22;

export function LinePlot({
  series,
  width = 320,
  height = 120,
  xLabel,
  yLabel,
  yMin,
  yMax,
  xMin,
  xMax,
  markers = [],
  zeroLine = false,
  empty = 'no run yet',
}: LinePlotProps) {
  const innerW = width - PAD_L - PAD_R;
  const innerH = height - PAD_T - PAD_B;
  const all = series.filter((s) => s.xs.length > 0);
  const hasData = all.length > 0;
  const xs = all.flatMap((s) => s.xs);
  const ys = all.flatMap((s) => s.ys);
  const x0 = xMin ?? (hasData ? Math.min(...xs) : 0);
  const x1 = xMax ?? (hasData ? Math.max(...xs) : 1);
  let y0 = yMin ?? (hasData ? Math.min(...ys) : 0);
  let y1 = yMax ?? (hasData ? Math.max(...ys) : 1);
  if (y1 - y0 < 1e-9) {
    y0 -= 0.5;
    y1 += 0.5;
  }
  const sx = (x: number) => PAD_L + ((x - x0) / Math.max(x1 - x0, 1e-9)) * innerW;
  const sy = (y: number) => PAD_T + ((y1 - y) / (y1 - y0)) * innerH;
  const path = (s: Series) =>
    s.xs
      .map((x, i) => `${i === 0 ? 'M' : 'L'}${sx(x).toFixed(2)} ${sy(s.ys[i]).toFixed(2)}`)
      .join(' ');

  return (
    <svg
      width={width}
      height={height}
      viewBox={`0 0 ${width} ${height}`}
      className="rounded border border-white/10 bg-black"
    >
      <line x1={PAD_L} x2={PAD_L} y1={PAD_T} y2={PAD_T + innerH} stroke="rgba(255,255,255,0.3)" />
      <line
        x1={PAD_L}
        x2={PAD_L + innerW}
        y1={PAD_T + innerH}
        y2={PAD_T + innerH}
        stroke="rgba(255,255,255,0.3)"
      />
      {zeroLine && y0 < 0 && y1 > 0 && (
        <line
          x1={PAD_L}
          x2={PAD_L + innerW}
          y1={sy(0)}
          y2={sy(0)}
          stroke="rgba(255,255,255,0.15)"
          strokeDasharray="2 3"
        />
      )}
      {yLabel && (
        <text x={4} y={PAD_T + 8} fontSize={9} fill="rgba(255,255,255,0.5)" fontFamily="monospace">
          {yLabel}
        </text>
      )}
      {xLabel && (
        <text
          x={width - PAD_R}
          y={PAD_T + innerH + 14}
          fontSize={9}
          textAnchor="end"
          fill="rgba(255,255,255,0.5)"
          fontFamily="monospace"
        >
          {xLabel}
        </text>
      )}
      <text
        x={PAD_L - 4}
        y={PAD_T + 4}
        fontSize={8}
        textAnchor="end"
        fill="rgba(255,255,255,0.4)"
        fontFamily="monospace"
      >
        {hasData ? y1.toPrecision(2) : ''}
      </text>
      <text
        x={PAD_L - 4}
        y={PAD_T + innerH}
        fontSize={8}
        textAnchor="end"
        fill="rgba(255,255,255,0.4)"
        fontFamily="monospace"
      >
        {hasData ? y0.toPrecision(2) : ''}
      </text>
      {markers.map((m) => (
        <g key={m.label}>
          <line
            x1={sx(m.x)}
            x2={sx(m.x)}
            y1={PAD_T}
            y2={PAD_T + innerH}
            stroke={m.color ?? 'rgba(255,255,255,0.25)'}
            strokeDasharray="3 3"
          />
          <text
            x={sx(m.x) + 2}
            y={PAD_T + 8}
            fontSize={8}
            fill={m.color ?? 'rgba(255,255,255,0.5)'}
            fontFamily="monospace"
          >
            {m.label}
          </text>
        </g>
      ))}
      {!hasData && (
        <text
          x={PAD_L + innerW / 2}
          y={PAD_T + innerH / 2 + 4}
          fontSize={10}
          textAnchor="middle"
          fill="rgba(255,255,255,0.35)"
          fontFamily="monospace"
        >
          {empty}
        </text>
      )}
      {all.map((s, i) => (
        <path
          key={s.label ?? i}
          d={path(s)}
          fill="none"
          stroke={s.color}
          strokeWidth={s.width ?? 1.3}
          strokeDasharray={s.dash}
        />
      ))}
      {all.some((s) => s.label) && (
        <g>
          {all.map((s, i) => (
            <g
              key={`lg-${s.label ?? i}`}
              transform={`translate(${PAD_L + 6 + i * 92}, ${PAD_T + innerH - 6})`}
            >
              <line
                x1={0}
                x2={12}
                y1={0}
                y2={0}
                stroke={s.color}
                strokeWidth={2}
                strokeDasharray={s.dash}
              />
              <text x={16} y={3} fontSize={8} fill="rgba(255,255,255,0.6)" fontFamily="monospace">
                {s.label}
              </text>
            </g>
          ))}
        </g>
      )}
    </svg>
  );
}
