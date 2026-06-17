'use client';

import { Instance, Instances } from '@react-three/drei';
import { useMemo } from 'react';
import * as THREE from 'three';

import type { NeuronPoint, NeuronResponse } from '@/lib/types';
import { swcTypeLabel } from '@/lib/types';

// Anti-theater note: every segment rendered here corresponds to a real
// reconstructed parent->child point pair from a NeuroMorpho SWC file. There
// are no synthetic branches.

interface Segment {
  childId: number;
  childType: number;
  childParentId: number;
  position: THREE.Vector3;
  quaternion: THREE.Quaternion;
  length: number;
  radius: number;
}

const Y_AXIS = new THREE.Vector3(0, 1, 0);

function buildSegments(points: NeuronPoint[]): Segment[] {
  const byId = new Map<number, NeuronPoint>();
  for (const p of points) byId.set(p.id, p);

  const segments: Segment[] = [];
  for (const child of points) {
    if (child.parent_id === -1) continue;
    const parent = byId.get(child.parent_id);
    if (!parent) continue;

    const start = new THREE.Vector3(parent.x, parent.y, parent.z);
    const end = new THREE.Vector3(child.x, child.y, child.z);
    const dir = new THREE.Vector3().subVectors(end, start);
    const length = dir.length();
    if (length === 0) continue;

    const position = new THREE.Vector3().addVectors(start, end).multiplyScalar(0.5);
    const quaternion = new THREE.Quaternion().setFromUnitVectors(Y_AXIS, dir.clone().normalize());
    const radius = Math.max((parent.radius + child.radius) * 0.5, 0.05);

    segments.push({
      childId: child.id,
      childType: child.type,
      childParentId: child.parent_id,
      position,
      quaternion,
      length,
      radius,
    });
  }
  return segments;
}

function somaCenter(points: NeuronPoint[]): { center: THREE.Vector3; radius: number } | null {
  const soma = points.filter((p) => p.type === 1);
  if (soma.length === 0) return null;
  const center = new THREE.Vector3();
  let radius = 0;
  for (const p of soma) {
    center.add(new THREE.Vector3(p.x, p.y, p.z));
    radius = Math.max(radius, p.radius);
  }
  center.divideScalar(soma.length);
  return { center, radius };
}

function colorForType(type: number): string {
  // Black/white default with red accent for soma (CLAUDE.md UI rule).
  switch (type) {
    case 1:
      return '#ff2d2d'; // soma — red accent
    case 2:
      return '#9bd2ff'; // axon — pale blue
    case 3:
      return '#ffffff'; // basal dendrite — white
    case 4:
      return '#cfcfcf'; // apical dendrite — light gray
    default:
      return '#7f7f7f';
  }
}

export interface SWCNeuronProps {
  neuron: NeuronResponse;
  onSegmentClick?: (info: { id: number; type: number; parentId: number }) => void;
}

export function SWCNeuron({ neuron, onSegmentClick }: SWCNeuronProps) {
  const segments = useMemo(() => buildSegments(neuron.points), [neuron.points]);
  const soma = useMemo(() => somaCenter(neuron.points), [neuron.points]);

  // Group segments by type so each Instances batch can carry a single material color.
  const byType = useMemo(() => {
    const groups = new Map<number, Segment[]>();
    for (const s of segments) {
      const list = groups.get(s.childType) ?? [];
      list.push(s);
      groups.set(s.childType, list);
    }
    return Array.from(groups.entries()).sort((a, b) => a[0] - b[0]);
  }, [segments]);

  return (
    <group>
      {soma && (
        <mesh
          position={soma.center}
          onClick={(event) => {
            event.stopPropagation();
            const somaPoint = neuron.points.find((p) => p.type === 1);
            if (!somaPoint) return;
            const info = { id: somaPoint.id, type: 1, parentId: somaPoint.parent_id };
            console.log('[soma click]', info, swcTypeLabel(1));
            onSegmentClick?.(info);
          }}
        >
          <sphereGeometry args={[soma.radius, 32, 32]} />
          <meshStandardMaterial color={colorForType(1)} />
        </mesh>
      )}

      {byType.map(([type, group]) => (
        <Instances
          key={type}
          limit={group.length}
          range={group.length}
          onClick={(event) => {
            event.stopPropagation();
            const idx = event.instanceId;
            if (idx === undefined) return;
            const seg = group[idx];
            const info = { id: seg.childId, type: seg.childType, parentId: seg.childParentId };
            console.log('[segment click]', info, swcTypeLabel(seg.childType));
            onSegmentClick?.(info);
          }}
        >
          <cylinderGeometry args={[1, 1, 1, 8]} />
          <meshStandardMaterial color={colorForType(type)} />
          {group.map((seg, i) => (
            <Instance
              key={i}
              position={seg.position}
              quaternion={seg.quaternion}
              scale={[seg.radius, seg.length, seg.radius]}
            />
          ))}
        </Instances>
      ))}
    </group>
  );
}
