'use client';

import { Instance, Instances, OrbitControls } from '@react-three/drei';
import { Canvas } from '@react-three/fiber';
import { useEffect, useMemo, useRef } from 'react';
import * as THREE from 'three';

import { useNeuronSelection } from '@/lib/neuron-context';
import type { BrainMeshResponse, NeuronResponse, NeuronSummary } from '@/lib/types';

import { NeuronGlyph } from './NeuronGlyph';

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
  destrieux_label_id: number[];
  color: string;
  opacity: number;
  onRegionClick?: (info: { destrieuxId: number; point: [number, number, number] }) => void;
}

function HemisphereMesh({
  vertices_flat,
  faces_flat,
  destrieux_label_id,
  color,
  opacity,
  onRegionClick,
}: HemisphereProps) {
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
    <mesh
      onClick={(event) => {
        if (!onRegionClick) return;
        event.stopPropagation();
        const faceIdx = event.faceIndex;
        if (faceIdx === undefined || faceIdx === null) return;
        const vIdx = indices[faceIdx * 3]; // first vertex of triangle
        const destrieuxId = destrieux_label_id[vIdx] ?? 0;
        const p = event.point;
        onRegionClick({ destrieuxId, point: [p.x, p.y, p.z] });
      }}
    >
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
  /** Optional per-marker glyph scale override (microns × scale → mm in brain space).
   *  Useful when a cell would visibly spill out of a small subcortical region. */
  scale?: number;
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

export interface FunctionHighlight {
  label: string;
  centroid_mni_mm: [number, number, number];
}

export interface RegionIntensity {
  label: string;
  centroid_mni_mm: [number, number, number];
  normalized: number; // 0-1
}

export interface TractCurve {
  name: string;
  color: string;
  start: [number, number, number];
  midpoint: [number, number, number];
  end: [number, number, number];
}

function TractTube({ curve }: { curve: TractCurve }) {
  const tubeGeom = useMemo(() => {
    const path = new THREE.QuadraticBezierCurve3(
      new THREE.Vector3(...curve.start),
      new THREE.Vector3(...curve.midpoint),
      new THREE.Vector3(...curve.end),
    );
    return new THREE.TubeGeometry(path, 48, 1.2, 8, false);
  }, [curve.start, curve.midpoint, curve.end]);

  return (
    <mesh geometry={tubeGeom}>
      <meshStandardMaterial
        color={curve.color}
        emissive={curve.color}
        emissiveIntensity={0.4}
        transparent
        opacity={0.85}
      />
    </mesh>
  );
}

interface BrainCanvasProps {
  mesh: BrainMeshResponse;
  markers?: NeuronMarker[];
  swcMap?: Map<number, NeuronResponse>;
  glyphScale?: number; // microns × glyphScale → mm. 0.02 ≈ 20× exaggeration of real ~0.001.
  onRegionClick?: (info: {
    destrieuxId: number;
    label: string;
    point: [number, number, number];
  }) => void;
  functionHighlights?: FunctionHighlight[];
  highlightColor?: string;
  regionIntensities?: RegionIntensity[];
  intensityColor?: string;
  tracts?: TractCurve[];
}

export function BrainCanvas({
  mesh,
  markers = [],
  swcMap,
  glyphScale = 0.02,
  onRegionClick,
  functionHighlights = [],
  highlightColor = '#ffe45e',
  regionIntensities = [],
  intensityColor = '#5eebff',
  tracts = [],
}: BrainCanvasProps) {
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
        destrieux_label_id={mesh.left.destrieux_label_id}
        color="#d8d8d8"
        opacity={0.12}
        onRegionClick={
          onRegionClick
            ? ({ destrieuxId, point }) =>
                onRegionClick({
                  destrieuxId,
                  label: mesh.destrieux_labels[destrieuxId] ?? `unknown (${destrieuxId})`,
                  point,
                })
            : undefined
        }
      />
      <HemisphereMesh
        vertices_flat={mesh.right.vertices_flat}
        faces_flat={mesh.right.faces_flat}
        destrieux_label_id={mesh.right.destrieux_label_id}
        color="#bfbfbf"
        opacity={0.12}
        onRegionClick={
          onRegionClick
            ? ({ destrieuxId, point }) =>
                onRegionClick({
                  destrieuxId,
                  label: mesh.destrieux_labels[destrieuxId] ?? `unknown (${destrieuxId})`,
                  point,
                })
            : undefined
        }
      />
      {markers.length > 0 &&
        markers.map((m, i) => {
          const seed = m.neuron.neuron_id;
          const dx = (Math.sin(seed * 12.9898) * 43758.5453) % 1;
          const dy = (Math.sin(seed * 78.233) * 43758.5453) % 1;
          const dz = (Math.sin(seed * 39.346) * 43758.5453) % 1;
          const jitterMm = 6;
          const pos: [number, number, number] = [
            m.centroid_mni_mm[0] + (dx - 0.5) * jitterMm,
            m.centroid_mni_mm[1] + (dy - 0.5) * jitterMm,
            m.centroid_mni_mm[2] + (dz - 0.5) * jitterMm,
          ];
          const swc = swcMap?.get(m.neuron.neuron_id);
          if (swc) {
            return (
              <NeuronGlyph
                key={`g-${seed}-${i}`}
                neuron={swc}
                position={pos}
                scale={m.scale ?? glyphScale}
                color={m.color}
              />
            );
          }
          return null;
        })}
      {markers.length > 0 && (!swcMap || swcMap.size === 0) && (
        <MarkerCluster markers={markers} />
      )}
      {functionHighlights.map((h, i) => (
        <mesh key={`${h.label}-${i}`} position={h.centroid_mni_mm}>
          <sphereGeometry args={[10, 24, 24]} />
          <meshStandardMaterial
            color={highlightColor}
            emissive={highlightColor}
            emissiveIntensity={1.0}
            transparent
            opacity={0.55}
          />
        </mesh>
      ))}
      {regionIntensities.map((r, i) => {
        const radius = 4 + r.normalized * 14;
        return (
          <mesh key={`int-${r.label}-${i}`} position={r.centroid_mni_mm}>
            <sphereGeometry args={[radius, 24, 24]} />
            <meshStandardMaterial
              color={intensityColor}
              emissive={intensityColor}
              emissiveIntensity={Math.max(0.15, r.normalized)}
              transparent
              opacity={0.15 + 0.5 * r.normalized}
            />
          </mesh>
        );
      })}
      {tracts.map((t, i) => (
        <TractTube key={`tract-${t.name}-${i}`} curve={t} />
      ))}
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
