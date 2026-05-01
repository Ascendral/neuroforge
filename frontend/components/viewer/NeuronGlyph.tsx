'use client';

import { useMemo } from 'react';

import type { NeuronResponse } from '@/lib/types';

// Anti-theater: every line segment drawn here is a real parent→child SWC
// connection from `neuron.points`, the same data the full-screen NeuronCanvas
// uses. Inside the brain shell we render at exaggerated scale (typically 20×)
// so the cell is *visible* against the brain mesh; the UI labels this
// explicitly. Real coords in microns are preserved up to a uniform scale +
// translation to the region centroid.

interface NeuronGlyphProps {
  neuron: NeuronResponse;
  position: [number, number, number]; // MNI mm where the neuron's "soma" sits
  scale: number;                       // unitless; SWC microns × scale → mm
  color: string;
}

export function NeuronGlyph({ neuron, position, scale, color }: NeuronGlyphProps) {
  const positions = useMemo(() => {
    const byId = new Map(neuron.points.map((p) => [p.id, p]));
    const seg: number[] = [];
    for (const child of neuron.points) {
      if (child.parent_id === -1) continue;
      const parent = byId.get(child.parent_id);
      if (!parent) continue;
      seg.push(parent.x, parent.y, parent.z, child.x, child.y, child.z);
    }
    return new Float32Array(seg);
  }, [neuron.points]);

  // Soma centroid in the SWC's own coordinate system
  const somaOffset = useMemo<[number, number, number]>(() => {
    const soma = neuron.points.filter((p) => p.type === 1);
    if (soma.length === 0) return [0, 0, 0];
    const sx = soma.reduce((a, p) => a + p.x, 0) / soma.length;
    const sy = soma.reduce((a, p) => a + p.y, 0) / soma.length;
    const sz = soma.reduce((a, p) => a + p.z, 0) / soma.length;
    return [sx, sy, sz];
  }, [neuron.points]);

  // Place neuron at MNI centroid, with its own soma offset cancelled so the
  // soma sits at exactly the position prop.
  return (
    <group position={position} scale={scale}>
      <group position={[-somaOffset[0], -somaOffset[1], -somaOffset[2]]}>
        <lineSegments>
          <bufferGeometry>
            <bufferAttribute attach="attributes-position" args={[positions, 3]} />
          </bufferGeometry>
          <lineBasicMaterial color={color} transparent opacity={0.95} />
        </lineSegments>
        <mesh>
          <sphereGeometry args={[8, 12, 12]} />
          <meshBasicMaterial color={color} />
        </mesh>
      </group>
    </group>
  );
}
