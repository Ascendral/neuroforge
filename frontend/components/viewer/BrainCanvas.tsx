'use client';

import { OrbitControls } from '@react-three/drei';
import { Canvas } from '@react-three/fiber';
import { useEffect, useMemo, useRef } from 'react';
import * as THREE from 'three';

import type { BrainMeshResponse } from '@/lib/types';

// Anti-theater: every vertex below comes from fsaverage5's pial.gii.gz file
// inside the nilearn package. The brain you're seeing is the actual averaged
// cortical surface from 40 healthy human subjects in MNI152 space, not a
// stylized illustration.

interface HemisphereProps {
  vertices_flat: number[];
  faces_flat: number[];
  color: string;
}

function HemisphereMesh({ vertices_flat, faces_flat, color }: HemisphereProps) {
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
      />
    </mesh>
  );
}

interface BrainCanvasProps {
  mesh: BrainMeshResponse;
}

export function BrainCanvas({ mesh }: BrainCanvasProps) {
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
      <ambientLight intensity={0.5} />
      <directionalLight position={[1, 1, 1]} intensity={0.7} />
      <directionalLight position={[-1, -0.5, -1]} intensity={0.3} />
      <HemisphereMesh
        vertices_flat={mesh.left.vertices_flat}
        faces_flat={mesh.left.faces_flat}
        color="#d8d8d8"
      />
      <HemisphereMesh
        vertices_flat={mesh.right.vertices_flat}
        faces_flat={mesh.right.faces_flat}
        color="#bfbfbf"
      />
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
