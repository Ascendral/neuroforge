'use client';

import { useFrame } from '@react-three/fiber';
import { useMemo, useRef } from 'react';
import * as THREE from 'three';

import type { NeuronResponse } from '@/lib/types';

// Anti-theater: every line segment is a real parent→child SWC connection
// from `neuron.points`. The firing animation runs a pulse outward from the
// soma along the *actual* path-length distance in the dendrite tree (BFS
// from type=1 points), so the wave shape mirrors the real morphology.
//
// Speed/period are SCALED for visibility — the UI labels them. Real values
// for reference: AP propagation along unmyelinated dendrite is ~500-2000
// µm/ms; HH at 10 µA fires at ~67 Hz (15 ms period). Both are too fast to
// see at the scale we render (a typical reconstructed cell is ~300-500 µm
// across). We use 250 µm/ms and 600 ms period to keep traversals visible
// to the human eye, and offset each neuron's phase so they don't fire in
// lockstep.

interface NeuronGlyphProps {
  neuron: NeuronResponse;
  position: [number, number, number];
  scale: number;
  color: string;
  /** Animation speed in microns/ms (visualization, not real biophysics). */
  speed_um_per_ms?: number;
  /** Inter-spike interval in ms (visualization). */
  period_ms?: number;
}

const VERT = `
attribute float distFromSoma;
varying float vDist;
void main() {
  vDist = distFromSoma;
  gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
}
`;

const FRAG = `
precision mediump float;
varying float vDist;
uniform float time_ms;
uniform float speed_um_per_ms;
uniform float period_ms;
uniform float phase_ms;
uniform vec3 baseColor;
uniform vec3 fireColor;
uniform float maxDist;
void main() {
  float t = mod(time_ms + phase_ms, period_ms);
  float wavefront = t * speed_um_per_ms;
  float distance_from_wave = abs(vDist - wavefront);
  // Wider pulse band (90 µm) for clearer visibility against the brain shell.
  float half_width = 90.0;
  // Smooth bell-shape intensity instead of a triangle: looks more like a
  // depolarization wave and fades naturally on either side.
  float t_norm = clamp(distance_from_wave / half_width, 0.0, 1.0);
  float intensity = pow(1.0 - t_norm, 2.0);
  // Quick fade once the wave has run past the dendrite's farthest extent.
  if (wavefront > maxDist + half_width) intensity = 0.0;
  // Boost output above 1.0 at the peak so the fire color visibly pops
  // (display will clip but the bright burst registers as glow).
  vec3 c = mix(baseColor, fireColor, intensity);
  c += fireColor * intensity * 1.4; // additive boost
  gl_FragColor = vec4(c, 0.97);
}
`;

export function NeuronGlyph({
  neuron,
  position,
  scale,
  color,
  speed_um_per_ms = 250,
  period_ms = 600,
}: NeuronGlyphProps) {
  // Build per-vertex distance from soma along the SWC tree.
  const { positions, distances, somaOffset, maxDist } = useMemo(() => {
    const byId = new Map(neuron.points.map((p) => [p.id, p]));
    // distFromSoma per point id, BFS-equivalent via SWC's parent-before-child
    // ordering (verified by backend test_parse_rejects_forward_parent_reference).
    const distById = new Map<number, number>();
    for (const p of neuron.points) {
      if (p.parent_id === -1 || !byId.has(p.parent_id)) {
        distById.set(p.id, 0);
        continue;
      }
      const parent = byId.get(p.parent_id)!;
      const parentDist = distById.get(parent.id) ?? 0;
      const dx = p.x - parent.x;
      const dy = p.y - parent.y;
      const dz = p.z - parent.z;
      const segLen = Math.sqrt(dx * dx + dy * dy + dz * dz);
      distById.set(p.id, parentDist + segLen);
    }

    const segPositions: number[] = [];
    const segDistances: number[] = [];
    let maxD = 0;
    for (const child of neuron.points) {
      if (child.parent_id === -1) continue;
      const parent = byId.get(child.parent_id);
      if (!parent) continue;
      const dParent = distById.get(parent.id) ?? 0;
      const dChild = distById.get(child.id) ?? 0;
      segPositions.push(parent.x, parent.y, parent.z, child.x, child.y, child.z);
      segDistances.push(dParent, dChild);
      if (dChild > maxD) maxD = dChild;
    }

    const soma = neuron.points.filter((p) => p.type === 1);
    let so: [number, number, number] = [0, 0, 0];
    if (soma.length > 0) {
      const sx = soma.reduce((a, p) => a + p.x, 0) / soma.length;
      const sy = soma.reduce((a, p) => a + p.y, 0) / soma.length;
      const sz = soma.reduce((a, p) => a + p.z, 0) / soma.length;
      so = [sx, sy, sz];
    }

    return {
      positions: new Float32Array(segPositions),
      distances: new Float32Array(segDistances),
      somaOffset: so,
      maxDist: maxD,
    };
  }, [neuron.points]);

  const baseColor = useMemo(() => new THREE.Color(color), [color]);
  // Bright pulse color: full white with a tinge of the cell's hue, so the
  // wave reads as a clear flash propagating along the dendrite tree.
  const fireColor = useMemo(() => new THREE.Color('#ffffff'), []);
  // Stable per-neuron phase offset so neurons don't fire in lockstep.
  const phase_ms = useMemo(() => {
    const seed = neuron.neuron_id;
    return (Math.sin(seed * 7919) * 100000) % (period_ms);
  }, [neuron.neuron_id, period_ms]);

  const uniforms = useRef({
    time_ms: { value: 0 },
    speed_um_per_ms: { value: speed_um_per_ms },
    period_ms: { value: period_ms },
    phase_ms: { value: phase_ms },
    baseColor: { value: baseColor },
    fireColor: { value: fireColor },
    maxDist: { value: maxDist },
  });

  useFrame((state) => {
    uniforms.current.time_ms.value = state.clock.elapsedTime * 1000.0;
  });

  return (
    <group position={position} scale={scale}>
      <group position={[-somaOffset[0], -somaOffset[1], -somaOffset[2]]}>
        <lineSegments>
          <bufferGeometry>
            <bufferAttribute attach="attributes-position" args={[positions, 3]} />
            <bufferAttribute attach="attributes-distFromSoma" args={[distances, 1]} />
          </bufferGeometry>
          <shaderMaterial
            transparent
            uniforms={uniforms.current}
            vertexShader={VERT}
            fragmentShader={FRAG}
          />
        </lineSegments>
        <mesh>
          <sphereGeometry args={[8, 12, 12]} />
          <meshBasicMaterial color={color} />
        </mesh>
      </group>
    </group>
  );
}
