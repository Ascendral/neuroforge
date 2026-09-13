'use client';

import { useMemo } from 'react';

import type { ScaleNode, ScalesGraphResponse } from '@/lib/types';

import { STRENGTH_COLOR, STRENGTH_DASH, bestStrength } from './strength';

// The complete schematic of the AI side: inference stack, block internals,
// augmentation, training loop, units and parameters. Every box is a registry
// node (clicking selects it); every arrow is a registry edge. Layout is the
// only thing decided here.

interface Box {
  x: number;
  y: number;
  w: number;
  h: number;
}

const W = 1240;
const H = 760;

// Static layout keyed by node id. Nodes the registry adds later that have no
// slot here are listed in a strip at the bottom so nothing is silently hidden.
const LAYOUT: Record<string, Box> = {
  // inference stack (bottom → top)
  'ai.arch.tokenizer': { x: 40, y: 660, w: 200, h: 44 },
  'ai.arch.embedding': { x: 40, y: 590, w: 200, h: 44 },
  'ai.arch.position': { x: 40, y: 520, w: 200, h: 44 },
  'ai.arch.blocks': { x: 40, y: 250, w: 200, h: 220 },
  'ai.arch.unembed': { x: 40, y: 170, w: 200, h: 44 },
  'ai.arch.sampler': { x: 40, y: 100, w: 200, h: 44 },
  'ai.arch': { x: 40, y: 40, w: 200, h: 36 },
  // one block, exploded
  'ai.block': { x: 300, y: 250, w: 380, h: 220 },
  'ai.block.norm': { x: 316, y: 420, w: 100, h: 34 },
  'ai.block.attention': { x: 316, y: 330, w: 150, h: 60 },
  'ai.block.multihead': { x: 316, y: 282, w: 150, h: 34 },
  'ai.block.induction': { x: 480, y: 330, w: 100, h: 60 },
  'ai.block.mlp': { x: 480, y: 410, w: 100, h: 44 },
  'ai.block.residual': { x: 620, y: 262, w: 44, h: 196 },
  // augmentation
  'ai.aug.kvcache': { x: 300, y: 130, w: 170, h: 44 },
  'ai.aug.icl': { x: 490, y: 130, w: 170, h: 44 },
  'ai.aug.moe': { x: 300, y: 60, w: 170, h: 44 },
  'ai.aug.rag': { x: 490, y: 60, w: 170, h: 44 },
  // training loop (right column)
  'ai.train': { x: 760, y: 40, w: 440, h: 36 },
  'ai.train.data': { x: 760, y: 100, w: 200, h: 44 },
  'ai.train.replay': { x: 1000, y: 100, w: 200, h: 44 },
  'ai.train.loss': { x: 760, y: 180, w: 200, h: 44 },
  'ai.train.rlhf': { x: 1000, y: 180, w: 200, h: 44 },
  'ai.train.backprop': { x: 760, y: 260, w: 200, h: 44 },
  'ai.train.regularization': { x: 1000, y: 260, w: 200, h: 44 },
  'ai.train.optimizer': { x: 760, y: 340, w: 200, h: 44 },
  // units + parameters
  'ai.unit.neuron': { x: 300, y: 530, w: 150, h: 40 },
  'ai.unit.feature': { x: 470, y: 530, w: 150, h: 40 },
  'ai.unit.attention_token': { x: 640, y: 530, w: 150, h: 40 },
  'ai.param.weight': { x: 300, y: 610, w: 120, h: 36 },
  'ai.param.gradient': { x: 440, y: 610, w: 120, h: 36 },
  'ai.param.activation': { x: 580, y: 610, w: 120, h: 36 },
  'ai.param.embedding': { x: 720, y: 610, w: 120, h: 36 },
  'ai.param.temperature': { x: 860, y: 610, w: 120, h: 36 },
  'ai.system': { x: 760, y: 430, w: 440, h: 60 },
};

const GROUP_LABELS: { label: string; x: number; y: number }[] = [
  { label: 'INFERENCE — one forward pass per token', x: 40, y: 30 },
  { label: 'INSIDE ONE BLOCK', x: 300, y: 240 },
  { label: 'AUGMENTATION', x: 300, y: 50 },
  { label: 'TRAINING LOOP', x: 760, y: 30 },
  { label: 'UNITS  (level 4)', x: 300, y: 520 },
  { label: 'PARAMETERS  (level 5)', x: 300, y: 600 },
];

const EDGE_STYLE: Record<string, { stroke: string; dash?: string }> = {
  data_flow: { stroke: 'rgba(255,255,255,0.55)' },
  gradient: { stroke: 'rgba(225,5,0,0.7)', dash: '5 3' },
  teaches: { stroke: 'rgba(225,5,0,0.5)', dash: '2 3' },
  modulates: { stroke: 'rgba(155,210,255,0.6)', dash: '2 3' },
  projects_to: { stroke: 'rgba(255,255,255,0.5)' },
};

function center(b: Box) {
  return { cx: b.x + b.w / 2, cy: b.y + b.h / 2 };
}

// Exit/entry point on the box border toward another box.
function port(from: Box, to: Box) {
  const a = center(from);
  const b = center(to);
  const dx = b.cx - a.cx;
  const dy = b.cy - a.cy;
  if (Math.abs(dx) * from.h > Math.abs(dy) * from.w) {
    return { x: dx > 0 ? from.x + from.w : from.x, y: a.cy };
  }
  return { x: a.cx, y: dy > 0 ? from.y + from.h : from.y };
}

interface AISchematicProps {
  graph: ScalesGraphResponse;
  selectedId: string | null;
  onSelect: (id: string) => void;
}

export function AISchematic({ graph, selectedId, onSelect }: AISchematicProps) {
  const ai = useMemo(() => graph.nodes.filter((n) => n.side === 'ai'), [graph]);
  const byId = useMemo(() => new Map(ai.map((n) => [n.id, n])), [ai]);
  const unplaced = ai.filter((n) => !LAYOUT[n.id]);
  const edges = graph.edges.filter((e) => LAYOUT[e.source] && LAYOUT[e.target]);
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
    const container = b.w > 300 || b.h > 150;
    return (
      <g
        key={n.id}
        onClick={() => onSelect(n.id)}
        className="cursor-pointer"
        opacity={dim ? 0.3 : 1}
      >
        <rect
          x={b.x}
          y={b.y}
          width={b.w}
          height={b.h}
          rx={container ? 18 : 12}
          fill={container ? 'rgba(255,255,255,0.025)' : 'rgba(255,255,255,0.06)'}
          stroke={isSel ? '#E10500' : best ? STRENGTH_COLOR[best] : 'rgba(255,255,255,0.22)'}
          strokeWidth={isSel ? 2 : best === 'strong' || best === 'equivalence' ? 1.2 : 1}
          strokeDasharray={best ? STRENGTH_DASH[best] : undefined}
        />
        {!container && (
          <rect
            x={b.x + 1}
            y={b.y + 1}
            width={b.w - 2}
            height={1}
            fill="rgba(255,255,255,0.18)"
            rx={1}
          />
        )}
        <text
          x={b.x + 10}
          y={b.y + (container ? 16 : b.h / 2 - 3)}
          fontSize={container ? 10 : 11.5}
          fill={container ? 'rgba(255,255,255,0.45)' : '#fff'}
          fontFamily={container ? 'var(--font-text)' : 'var(--font-display)'}
          fontWeight={600}
          letterSpacing={container ? 1.5 : 0}
          style={container ? { textTransform: 'uppercase' } : undefined}
        >
          {n.name.length > 30 && !container ? n.name.slice(0, 29) + '…' : n.name}
        </text>
        {!container && (
          <text
            x={b.x + 10}
            y={b.y + b.h / 2 + 11}
            fontSize={9}
            fill="rgba(255,255,255,0.5)"
            fontFamily="var(--font-text)"
          >
            {n.analogs.length > 0
              ? `↔ ${n.analogs[0].target_name}`.slice(0, Math.max(10, Math.floor(b.w / 5.4)))
              : '∅ no brain counterpart'}
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

  // draw containers first, then leaves on top
  const placed = ai.filter((n) => LAYOUT[n.id]);
  const containers = placed.filter((n) => LAYOUT[n.id].w > 300 || LAYOUT[n.id].h > 150);
  const leaves = placed.filter((n) => !containers.includes(n));

  return (
    <div className="h-full w-full overflow-auto">
      <svg
        viewBox={`0 0 ${W} ${H}`}
        className="h-full w-full min-w-[900px]"
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
            fontSize={9}
            fill="rgba(255,255,255,0.35)"
            fontFamily="var(--font-text)"
            letterSpacing={1.5}
          >
            {g.label}
          </text>
        ))}

        {containers.map((n) => boxFor(n, LAYOUT[n.id]))}

        {edges.map((e, i) => {
          const a = LAYOUT[e.source];
          const b = LAYOUT[e.target];
          const p1 = port(a, b);
          const p2 = port(b, a);
          const st = EDGE_STYLE[e.kind] ?? EDGE_STYLE.data_flow;
          const active = !related || (related.has(e.source) && related.has(e.target));
          const mx = (p1.x + p2.x) / 2;
          const my = (p1.y + p2.y) / 2;
          const vertical = Math.abs(p2.y - p1.y) > Math.abs(p2.x - p1.x);
          const d = vertical
            ? `M${p1.x} ${p1.y} C ${p1.x} ${my}, ${p2.x} ${my}, ${p2.x} ${p2.y}`
            : `M${p1.x} ${p1.y} C ${mx} ${p1.y}, ${mx} ${p2.y}, ${p2.x} ${p2.y}`;
          return (
            <g key={`${e.source}->${e.target}-${i}`} opacity={active ? 1 : 0.12}>
              <path
                d={d}
                fill="none"
                stroke={st.stroke}
                strokeWidth={1.2}
                strokeDasharray={st.dash}
                markerEnd={`url(#arrow-${e.kind})`}
              />
              {active && related && (
                <text
                  x={mx}
                  y={my - 3}
                  fontSize={8}
                  textAnchor="middle"
                  fill="rgba(255,255,255,0.6)"
                  fontFamily="var(--font-text)"
                >
                  {e.note}
                </text>
              )}
            </g>
          );
        })}

        {leaves.map((n) => boxFor(n, LAYOUT[n.id]))}

        {/* legend */}
        <g transform={`translate(760, 520)`}>
          <text
            x={0}
            y={0}
            fontSize={9}
            fill="rgba(255,255,255,0.35)"
            fontFamily="var(--font-text)"
            letterSpacing={1.5}
          >
            BOX BORDER = EVIDENCE FOR ITS BRAIN ANALOG
          </text>
          {(['equivalence', 'strong', 'analogy', 'none'] as const).map((s, i) => (
            <g key={s} transform={`translate(${(i % 2) * 220}, ${14 + Math.floor(i / 2) * 16})`}>
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
                fontSize={8.5}
                fill="rgba(255,255,255,0.6)"
                fontFamily="var(--font-text)"
              >
                {s}
              </text>
            </g>
          ))}
          <text
            x={0}
            y={60}
            fontSize={9}
            fill="rgba(255,255,255,0.35)"
            fontFamily="var(--font-text)"
            letterSpacing={1.5}
          >
            ARROWS
          </text>
          {Object.entries(EDGE_STYLE)
            .filter(([k]) => k !== 'projects_to')
            .map(([k, s], i) => (
              <g key={k} transform={`translate(${(i % 2) * 220}, ${74 + Math.floor(i / 2) * 16})`}>
                <line
                  x1={0}
                  x2={24}
                  y1={4}
                  y2={4}
                  stroke={s.stroke}
                  strokeWidth={2}
                  strokeDasharray={s.dash}
                />
                <text
                  x={30}
                  y={7}
                  fontSize={8.5}
                  fill="rgba(255,255,255,0.6)"
                  fontFamily="var(--font-text)"
                >
                  {k.replace('_', ' ')}
                </text>
              </g>
            ))}
        </g>

        {unplaced.length > 0 && (
          <g transform={`translate(40, ${H - 30})`}>
            <text
              x={0}
              y={0}
              fontSize={9}
              fill="rgba(255,255,255,0.4)"
              fontFamily="var(--font-text)"
            >
              not placed on this diagram (registry has them):{' '}
              {unplaced.map((n) => n.name).join(' · ')}
            </text>
          </g>
        )}
      </svg>
    </div>
  );
}
