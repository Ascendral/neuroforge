'use client';

import { useMemo } from 'react';

import type { ScaleEdge, ScaleNode, ScalesGraphResponse } from '@/lib/types';

import { STRENGTH_COLOR, STRENGTH_DASH, bestStrength } from './strength';

// The complete schematic of the AI side: inference stack, block internals,
// augmentation, training loop, units and parameters. Every box is a registry
// node (clicking selects it); every arrow is a registry edge. Layout and
// routing are the only things decided here.

interface Box {
  x: number;
  y: number;
  w: number;
  h: number;
}

const W = 1460;
const H = 820;
const LANE_Y = 512; // free horizontal lane between the block container and the units row

// Static layout keyed by node id. Nodes the registry adds later that have no
// slot here are listed in a strip at the bottom so nothing is silently hidden.
const LAYOUT: Record<string, Box> = {
  // inference stack (bottom → top), x 40..260
  'ai.arch': { x: 40, y: 44, w: 220, h: 34 },
  'ai.arch.sampler': { x: 40, y: 98, w: 220, h: 46 },
  'ai.arch.unembed': { x: 40, y: 168, w: 220, h: 46 },
  'ai.arch.blocks': { x: 40, y: 250, w: 220, h: 230 },
  'ai.arch.position': { x: 40, y: 560, w: 220, h: 46 },
  'ai.arch.embedding': { x: 40, y: 632, w: 220, h: 46 },
  'ai.arch.tokenizer': { x: 40, y: 704, w: 220, h: 46 },
  // augmentation, x 320..760
  'ai.aug.moe': { x: 320, y: 60, w: 210, h: 46 },
  'ai.aug.rag': { x: 550, y: 60, w: 210, h: 46 },
  'ai.aug.kvcache': { x: 320, y: 132, w: 210, h: 46 },
  'ai.aug.icl': { x: 550, y: 132, w: 210, h: 46 },
  // one block, exploded, x 320..760
  'ai.block': { x: 320, y: 250, w: 440, h: 230 },
  'ai.block.multihead': { x: 336, y: 284, w: 170, h: 40 },
  'ai.block.attention': { x: 336, y: 338, w: 170, h: 56 },
  'ai.block.induction': { x: 522, y: 338, w: 150, h: 56 },
  'ai.block.norm': { x: 336, y: 420, w: 170, h: 40 },
  'ai.block.mlp': { x: 522, y: 420, w: 150, h: 40 },
  'ai.block.residual': { x: 690, y: 266, w: 54, h: 198 },
  // training loop, x 820..1420
  'ai.train': { x: 820, y: 44, w: 600, h: 34 },
  'ai.train.data': { x: 820, y: 98, w: 280, h: 46 },
  'ai.train.replay': { x: 1140, y: 98, w: 280, h: 46 },
  'ai.train.loss': { x: 820, y: 178, w: 280, h: 46 },
  'ai.train.rlhf': { x: 1140, y: 178, w: 280, h: 46 },
  'ai.train.backprop': { x: 820, y: 258, w: 280, h: 46 },
  'ai.train.regularization': { x: 1140, y: 258, w: 280, h: 46 },
  'ai.train.optimizer': { x: 820, y: 338, w: 280, h: 46 },
  'ai.system': { x: 820, y: 418, w: 600, h: 60 },
  // units row, y 548
  'ai.unit.neuron': { x: 320, y: 548, w: 250, h: 46 },
  'ai.unit.feature': { x: 590, y: 548, w: 250, h: 46 },
  'ai.unit.attention_token': { x: 860, y: 548, w: 250, h: 46 },
  // parameters row, y 640
  'ai.param.weight': { x: 320, y: 640, w: 200, h: 46 },
  'ai.param.gradient': { x: 540, y: 640, w: 200, h: 46 },
  'ai.param.activation': { x: 760, y: 640, w: 200, h: 46 },
  'ai.param.embedding': { x: 980, y: 640, w: 200, h: 46 },
  'ai.param.temperature': { x: 1200, y: 640, w: 200, h: 46 },
};

const CONTAINERS = new Set(['ai.arch', 'ai.arch.blocks', 'ai.block', 'ai.train', 'ai.system']);

const GROUP_LABELS: { label: string; x: number; y: number }[] = [
  { label: 'INFERENCE — ONE FORWARD PASS PER TOKEN', x: 40, y: 34 },
  { label: 'AUGMENTATION', x: 320, y: 50 },
  { label: 'INSIDE ONE BLOCK', x: 320, y: 240 },
  { label: 'TRAINING LOOP', x: 820, y: 34 },
  { label: 'UNITS · LEVEL 4', x: 320, y: 538 },
  { label: 'PARAMETERS · LEVEL 5', x: 320, y: 630 },
];

const EDGE_STYLE: Record<string, { stroke: string; dash?: string }> = {
  data_flow: { stroke: 'rgba(255,255,255,0.5)' },
  gradient: { stroke: 'rgba(225,5,0,0.75)', dash: '5 3' },
  teaches: { stroke: 'rgba(225,5,0,0.55)', dash: '2 3' },
  modulates: { stroke: 'rgba(155,210,255,0.6)', dash: '2 3' },
  projects_to: { stroke: 'rgba(255,255,255,0.5)' },
};

const center = (b: Box) => ({ cx: b.x + b.w / 2, cy: b.y + b.h / 2 });

type Pt = [number, number];

// Does the axis-aligned segment p→q cut through a leaf box (with margin)?
function segmentHitsBox(p: Pt, q: Pt, b: Box, m = 6): boolean {
  const x0 = Math.min(p[0], q[0]) - m;
  const x1 = Math.max(p[0], q[0]) + m;
  const y0 = Math.min(p[1], q[1]) - m;
  const y1 = Math.max(p[1], q[1]) + m;
  return x0 < b.x + b.w && x1 > b.x && y0 < b.y + b.h && y1 > b.y;
}

function pathHitsAny(pts: Pt[], boxes: Box[]): boolean {
  for (let i = 0; i + 1 < pts.length; i++)
    for (const b of boxes) if (segmentHitsBox(pts[i], pts[i + 1], b)) return true;
  return false;
}

// Orthogonal routing: try the direct H-V-H (or straight vertical) path; if it
// crosses any other leaf box, detour through the side gutter and the free lane.
function route(a: Box, b: Box, obstacles: Box[]): Pt[] {
  const ac = center(a);
  const bc = center(b);
  const overlapX = a.x < b.x + b.w && b.x < a.x + a.w;
  const candidates: Pt[][] = [];
  if (overlapX) {
    const down = bc.cy > ac.cy;
    const x = (Math.max(a.x, b.x) + Math.min(a.x + a.w, b.x + b.w)) / 2;
    candidates.push([
      [x, down ? a.y + a.h : a.y],
      [x, down ? b.y : b.y + b.h],
    ]);
    // side detour down the left margin (the sampler → tokenizer feedback)
    const gx = Math.min(a.x, b.x) - 18;
    candidates.push([
      [a.x, ac.cy],
      [gx, ac.cy],
      [gx, bc.cy],
      [b.x, bc.cy],
    ]);
  } else {
    const dir = bc.cx > ac.cx ? 1 : -1;
    const x1 = dir > 0 ? a.x + a.w : a.x;
    const x2 = dir > 0 ? b.x : b.x + b.w;
    const gxA = x1 + dir * 26;
    const gxB = x2 - dir * 26;
    candidates.push([
      [x1, ac.cy],
      [(x1 + x2) / 2, ac.cy],
      [(x1 + x2) / 2, bc.cy],
      [x2, bc.cy],
    ]);
    candidates.push([
      [x1, ac.cy],
      [gxA, ac.cy],
      [gxA, bc.cy],
      [x2, bc.cy],
    ]);
    candidates.push([
      [x1, ac.cy],
      [gxB, ac.cy],
      [gxB, bc.cy],
      [x2, bc.cy],
    ]);
    candidates.push([
      [x1, ac.cy],
      [gxA, ac.cy],
      [gxA, LANE_Y],
      [gxB, LANE_Y],
      [gxB, bc.cy],
      [x2, bc.cy],
    ]);
  }
  for (const c of candidates) if (!pathHitsAny(c, obstacles)) return c;
  return candidates[candidates.length - 1];
}

const toPath = (pts: Pt[]) =>
  pts.map((p, i) => `${i === 0 ? 'M' : 'L'}${p[0].toFixed(1)} ${p[1].toFixed(1)}`).join(' ');

const fit = (s: string, px: number, perChar: number) => {
  const max = Math.max(6, Math.floor(px / perChar));
  return s.length > max ? s.slice(0, max - 1) + '…' : s;
};

interface AISchematicProps {
  graph: ScalesGraphResponse;
  selectedId: string | null;
  onSelect: (id: string) => void;
}

export function AISchematic({ graph, selectedId, onSelect }: AISchematicProps) {
  const ai = useMemo(() => graph.nodes.filter((n) => n.side === 'ai'), [graph]);
  const byId = useMemo(() => new Map(ai.map((n) => [n.id, n])), [ai]);
  const unplaced = ai.filter((n) => !LAYOUT[n.id]);
  const placed = ai.filter((n) => LAYOUT[n.id]);
  const containers = placed.filter((n) => CONTAINERS.has(n.id));
  const leaves = placed.filter((n) => !CONTAINERS.has(n.id));
  const leafBoxes = useMemo(() => new Map(leaves.map((n) => [n.id, LAYOUT[n.id]])), [leaves]);

  const edges = useMemo(() => {
    const es = graph.edges.filter((e) => LAYOUT[e.source] && LAYOUT[e.target]);
    return es.map((e) => {
      const a = LAYOUT[e.source];
      const b = LAYOUT[e.target];
      const obstacles = [...leafBoxes.entries()]
        .filter(([id]) => id !== e.source && id !== e.target)
        .map(([, box]) => box);
      const pts = route(a, b, obstacles);
      return { e, pts };
    });
  }, [graph.edges, leafBoxes]);

  const selected = selectedId ? (byId.get(selectedId) ?? null) : null;
  const related = useMemo(() => {
    if (!selected) return null;
    const s = new Set<string>([selected.id]);
    graph.edges.forEach((e) => {
      if (e.source === selected.id) s.add(e.target);
      if (e.target === selected.id) s.add(e.source);
    });
    if (selected.parent) s.add(selected.parent);
    selected.children.forEach((c) => s.add(c));
    return s;
  }, [selected, graph.edges]);

  const boxFor = (n: ScaleNode, b: Box) => {
    const best =
      bestStrength(n.analogs.map((a) => a.strength)) ?? (n.no_analog_note ? 'none' : null);
    const isSel = n.id === selectedId;
    const dim = !!related && !related.has(n.id);
    const container = CONTAINERS.has(n.id);
    const title = container ? n.name.toUpperCase() : fit(n.name, b.w - 22, 6.9);
    const sub = n.analogs.length > 0 ? `↔ ${n.analogs[0].target_name}` : '∅ no brain counterpart';
    return (
      <g
        key={n.id}
        onClick={() => onSelect(n.id)}
        className="cursor-pointer"
        opacity={dim ? 0.3 : 1}
        style={{ transition: 'opacity 0.3s ease' }}
      >
        <rect
          x={b.x}
          y={b.y}
          width={b.w}
          height={b.h}
          rx={container ? 18 : 12}
          fill={container ? 'rgba(255,255,255,0.025)' : '#141416'}
          stroke={isSel ? '#E10500' : best ? STRENGTH_COLOR[best] : 'rgba(255,255,255,0.22)'}
          strokeWidth={isSel ? 2 : best === 'strong' || best === 'equivalence' ? 1.2 : 1}
          strokeDasharray={best ? STRENGTH_DASH[best] : undefined}
        />
        {!container && (
          <rect x={b.x + 1} y={b.y + 1} width={b.w - 2} height={1} fill="rgba(255,255,255,0.18)" />
        )}
        <text
          x={b.x + 11}
          y={b.y + (container ? 20 : b.h / 2 - 2)}
          fontSize={container ? 9.5 : 11.5}
          fill={container ? 'rgba(255,255,255,0.45)' : '#fff'}
          fontFamily={container ? 'var(--font-text)' : 'var(--font-display)'}
          fontWeight={600}
          letterSpacing={container ? 1.6 : 0}
        >
          {title}
        </text>
        {!container && (
          <text
            x={b.x + 11}
            y={b.y + b.h / 2 + 12}
            fontSize={9}
            fill="rgba(255,255,255,0.5)"
            fontFamily="var(--font-text)"
          >
            {fit(sub, b.w - 22, 5.2)}
          </text>
        )}
        {n.widget && (
          <text
            x={b.x + b.w - 10}
            y={b.y + 13}
            fontSize={9}
            textAnchor="end"
            fill="#E10500"
            fontFamily="var(--font-text)"
          >
            ▶
          </text>
        )}
      </g>
    );
  };

  const edgeEl = ({ e, pts }: { e: ScaleEdge; pts: Pt[] }, i: number) => {
    const st = EDGE_STYLE[e.kind] ?? EDGE_STYLE.data_flow;
    const active = !related || (related.has(e.source) && related.has(e.target));
    const mid = pts[Math.floor((pts.length - 1) / 2)];
    const nxt = pts[Math.floor((pts.length - 1) / 2) + 1] ?? mid;
    const lx = (mid[0] + nxt[0]) / 2;
    const ly = (mid[1] + nxt[1]) / 2;
    return (
      <g
        key={`${e.source}->${e.target}-${i}`}
        opacity={active ? 1 : 0.1}
        style={{ transition: 'opacity 0.3s ease' }}
      >
        <path
          d={toPath(pts)}
          fill="none"
          stroke={st.stroke}
          strokeWidth={1.2}
          strokeDasharray={st.dash}
          strokeLinejoin="round"
          markerEnd={`url(#arrow-${e.kind})`}
        />
        {active && related && (
          <text
            x={lx}
            y={ly - 4}
            fontSize={8.5}
            textAnchor="middle"
            fill="rgba(255,255,255,0.7)"
            fontFamily="var(--font-text)"
            style={{ paintOrder: 'stroke', stroke: '#0A0A0B', strokeWidth: 3 }}
          >
            {e.note}
          </text>
        )}
      </g>
    );
  };

  return (
    <div className="h-full w-full overflow-auto">
      <svg
        viewBox={`0 0 ${W} ${H}`}
        className="h-full w-full min-w-[1000px]"
        preserveAspectRatio="xMidYMid meet"
      >
        <defs>
          {Object.entries(EDGE_STYLE).map(([k, s]) => (
            <marker
              key={k}
              id={`arrow-${k}`}
              viewBox="0 0 10 10"
              refX="9"
              refY="5"
              markerWidth="7"
              markerHeight="7"
              orient="auto-start-reverse"
            >
              <path d="M 0 0 L 10 5 L 0 10 z" fill={s.stroke} />
            </marker>
          ))}
        </defs>

        {GROUP_LABELS.map((g) => (
          <text
            key={g.label}
            x={g.x}
            y={g.y - 8}
            fontSize={9.5}
            fill="rgba(255,255,255,0.4)"
            fontFamily="var(--font-text)"
            fontWeight={600}
            letterSpacing={2}
          >
            {g.label}
          </text>
        ))}

        {containers.map((n) => boxFor(n, LAYOUT[n.id]))}
        {edges.map(edgeEl)}
        {leaves.map((n) => boxFor(n, LAYOUT[n.id]))}

        {/* legend */}
        <g transform="translate(1150, 548)">
          <text
            x={0}
            y={0}
            fontSize={9.5}
            fill="rgba(255,255,255,0.4)"
            fontFamily="var(--font-text)"
            fontWeight={600}
            letterSpacing={2}
          >
            BORDER = EVIDENCE FOR BRAIN ANALOG
          </text>
          {(['equivalence', 'strong', 'analogy', 'none'] as const).map((s, i) => (
            <g key={s} transform={`translate(${(i % 2) * 140}, ${16 + Math.floor(i / 2) * 16})`}>
              <line
                x1={0}
                x2={24}
                y1={4}
                y2={4}
                stroke={STRENGTH_COLOR[s]}
                strokeWidth={2}
                strokeDasharray={STRENGTH_DASH[s]}
              />
              <text
                x={30}
                y={7}
                fontSize={9}
                fill="rgba(255,255,255,0.6)"
                fontFamily="var(--font-text)"
              >
                {s}
              </text>
            </g>
          ))}
          <g transform="translate(0, 60)">
            <text
              x={0}
              y={0}
              fontSize={9.5}
              fill="rgba(255,255,255,0.4)"
              fontFamily="var(--font-text)"
              fontWeight={600}
              letterSpacing={2}
            >
              ARROWS
            </text>
            {(['data_flow', 'gradient', 'teaches', 'modulates'] as const).map((k, i) => (
              <g key={k} transform={`translate(${(i % 2) * 140}, ${16 + Math.floor(i / 2) * 16})`}>
                <line
                  x1={0}
                  x2={24}
                  y1={4}
                  y2={4}
                  stroke={EDGE_STYLE[k].stroke}
                  strokeWidth={2}
                  strokeDasharray={EDGE_STYLE[k].dash}
                />
                <text
                  x={30}
                  y={7}
                  fontSize={9}
                  fill="rgba(255,255,255,0.6)"
                  fontFamily="var(--font-text)"
                >
                  {k.replace('_', ' ')}
                </text>
              </g>
            ))}
          </g>
        </g>

        {unplaced.length > 0 && (
          <text
            x={40}
            y={H - 24}
            fontSize={9.5}
            fill="rgba(255,255,255,0.4)"
            fontFamily="var(--font-text)"
          >
            not placed on this diagram (registry has them):{' '}
            {unplaced.map((n) => n.name).join(' · ')}
          </text>
        )}
      </svg>
    </div>
  );
}
