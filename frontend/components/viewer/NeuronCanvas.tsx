'use client';

import { OrbitControls } from '@react-three/drei';
import { Canvas } from '@react-three/fiber';
import { useMemo } from 'react';
import * as THREE from 'three';

import type { NeuronResponse } from '@/lib/types';

import { SWCNeuron } from './SWCNeuron';

function neuronExtent(neuron: NeuronResponse): { center: THREE.Vector3; radius: number } {
  const box = new THREE.Box3();
  for (const p of neuron.points) {
    box.expandByPoint(new THREE.Vector3(p.x, p.y, p.z));
  }
  const center = new THREE.Vector3();
  box.getCenter(center);
  const size = new THREE.Vector3();
  box.getSize(size);
  const radius = Math.max(size.x, size.y, size.z) * 0.5 || 1;
  return { center, radius };
}

interface NeuronCanvasProps {
  neuron: NeuronResponse;
  onSegmentClick?: (info: { id: number; type: number; parentId: number }) => void;
}

export function NeuronCanvas({ neuron, onSegmentClick }: NeuronCanvasProps) {
  const { center, radius } = useMemo(() => neuronExtent(neuron), [neuron]);
  const cameraDistance = radius * 3;

  return (
    <Canvas
      camera={{
        position: [
          center.x + cameraDistance,
          center.y + cameraDistance * 0.3,
          center.z + cameraDistance,
        ],
        fov: 40,
        near: 0.1,
        far: cameraDistance * 100,
      }}
      style={{ background: '#000' }}
    >
      <ambientLight intensity={0.4} />
      <directionalLight position={[1, 1, 1]} intensity={0.8} />
      <directionalLight position={[-1, -0.5, -1]} intensity={0.3} />
      <SWCNeuron neuron={neuron} onSegmentClick={onSegmentClick} />
      <OrbitControls
        target={center}
        enableDamping
        dampingFactor={0.1}
        minDistance={radius * 0.5}
        maxDistance={cameraDistance * 10}
      />
    </Canvas>
  );
}
