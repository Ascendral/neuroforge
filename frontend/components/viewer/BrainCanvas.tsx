'use client';

import { Instance, Instances, OrbitControls } from '@react-three/drei';
import { Canvas } from '@react-three/fiber';
import { useEffect, useMemo, useRef } from 'react';
import * as THREE from 'three';

import { useNeuronSelection } from '@/lib/neuron-context';
import type { BrainMeshResponse, NeuronSummary } from '@/lib/types';

// Anti-theater: every vertex below comes from fsaverage5's pial.gii.gz file
// inside the nilearn package. The brain you're seeing is the actual averaged
// cortical surface from 40 healthy human subjects in MNI152 space, not a
// stylized illustration. Neuron markers are placed at the *real MNI centroid*
// of their region (Harvard-Oxford), with small jitter so multiple cells in
// the same region don't overlap visually. The UI labels this "schematic
// placement within {region}".

interface HemisphereProps {
  vertices_flat: number[];
  faces_flat: number[];
  color: string;
  opacity: number;
}

function HemisphereMesh({ vertices_flat, faces_flat, color, opacity }: HemisphereProps) {
  const geomRef = useRef<THREE.BufferGeometry>(null);

  const { positions, indices } = useMemo(() => {
    const positions = new Float32Array(vertices_flat);
    const indices = new Uint32Array(faces_flat);
    return { positions, indices };
  }, [vertices_flat, faces_flat]);

  useEffect(() => {
    const g = geomRef.current;
    if (!g) return;
    g.computeVertexNormals();
  }, [positions, indices]);

  return (
    <mesh>
      <bufferGeometry ref={geomRef}>
        <bufferAttribute
          attach="attributes-position"
          args={[positions, 3]}
        />
        <bufferAttribute attach="index" args={[indices, 1]} />
      </bufferGeometry>
      <meshStandardMaterial
        color={color}
        roughness={0.85}
        metalness={0.05}
        side={THREE.DoubleSide}
        transparent
        opacity={opacity}
        depthWrite={false}
      />
    </mesh>
  );
}

export interface NeuronMarker {
  neuron: NeuronSummary;
  centroid_mni_mm: [number, number, number];
  module: string;
  color: string;
}

interface MarkerClusterProps {
  markers: NeuronMarker[];
  jitter_mm?: number;
}

function MarkerCluster({ markers, jitter_mm = 6 }: MarkerClusterProps) {
  const selection = useNeuronSelection();
  const positions = useMemo(() => {
    // Deterministic jitter from neuron_id so positions are stable across re-renders
    return markers.map((m, _i) => {
      const seed = m.neuron.neuron_id;
      const dx = (Math.sin(seed * 12.9898) * 43758.5453) % 1;
      const dy = (Math.sin(seed * 78.233) * 43758.5453) % 1;
      const dz = (Math.sin(seed * 39.346) * 43758.5453) % 1;
      return [
        m.centroid_mni_mm[0] + (dx - 0.5) * jitter_mm,
        m.centroid_mni_mm[1] + (dy - 0.5) * jitter_mm,
        m.centroid_mni_mm[2] + (dz - 0.5) * jitter_mm,
      ] as [number, number, number];
    });
  }, [markers, jitter_mm]);

  // Group by color so each Instances batch can carry a single material color
  const byColor = useMemo(() => {
    const groups = new Map<string, { marker: NeuronMarker; pos: [number, number, number] }[]>();
    markers.forEach((m, i) => {
      const list = groups.get(m.color) ?? [];
      list.push({ marker: m, pos: positions[i] });
      groups.set(m.color, list);
    });
    return Array.from(groups.entries());
  }, [markers, positions]);

  return (
    <>
      {byColor.map(([color, group]) => (
        <Instances
          key={color}
          limit={group.length}
          range={group.length}
          onClick={(event) => {
            event.stopPropagation();
            const idx = event.instanceId;
            if (idx === undefined) return;
            selection?.selectNeuron(group[idx].marker.neuron.neuron_id);
          }}
        >
          <sphereGeometry args={[2.2, 12, 12]} />
          <meshStandardMaterial color={color} emissive={color} emissiveIntensity={0.4} />
          {group.map((g, i) => (
            <Instance
              key={g.marker.neuron.neuron_id}
              position={g.pos}
              userData={{ neuronId: g.marker.neuron.neuron_id }}
            />
          ))}
        </Instances>
      ))}
    </>
  );
}

interface BrainCanvasProps {
  mesh: BrainMeshResponse;
  markers?: NeuronMarker[];
}

export function BrainCanvas({ mesh, markers = [] }: BrainCanvasProps) {
  const center = useMemo(() => {
    // Compute combined bbox center across both hemispheres
    const v = [...mesh.left.vertices_flat, ...mesh.right.vertices_flat];
    let minX = Infinity, minY = Infinity, minZ = Infinity;
    let maxX = -Infinity, maxY = -Infinity, maxZ = -Infinity;
    for (let i = 0; i < v.length; i += 3) {
      minX = Math.min(minX, v[i]);
      maxX = Math.max(maxX, v[i]);
      minY = Math.min(minY, v[i + 1]);
      maxY = Math.max(maxY, v[i + 1]);
      minZ = Math.min(minZ, v[i + 2]);
      maxZ = Math.max(maxZ, v[i + 2]);
    }
    return {
      center: new THREE.Vector3((minX + maxX) / 2, (minY + maxY) / 2, (minZ + maxZ) / 2),
      radius: Math.max(maxX - minX, maxY - minY, maxZ - minZ) * 0.5,
    };
  }, [mesh]);

  const cameraDistance = center.radius * 3;

  return (
    <Canvas
      camera={{
        position: [
          center.center.x + cameraDistance * 0.6,
          center.center.y + cameraDistance * 0.4,
          center.center.z + cameraDistance,
        ],
        fov: 35,
        near: 0.1,
        far: cameraDistance * 100,
      }}
      style={{ background: '#000' }}
    >
      <ambientLight intensity={0.45} />
      <directionalLight position={[1, 1, 1]} intensity={0.6} />
      <directionalLight position={[-1, -0.5, -1]} intensity={0.3} />
      <HemisphereMesh
        vertices_flat={mesh.left.vertices_flat}
        faces_flat={mesh.left.faces_flat}
        color="#d8d8d8"
        opacity={0.12}
      />
      <HemisphereMesh
        vertices_flat={mesh.right.vertices_flat}
        faces_flat={mesh.right.faces_flat}
        color="#bfbfbf"
        opacity={0.12}
      />
      {markers.length > 0 && <MarkerCluster markers={markers} />}
      <OrbitControls
        target={center.center}
        enableDamping
        dampingFactor={0.1}
        minDistance={center.radius * 0.4}
        maxDistance={cameraDistance * 8}
      />
    </Canvas>
  );
}
