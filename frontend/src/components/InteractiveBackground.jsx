import { Canvas, useFrame } from "@react-three/fiber";
import { MeshDistortMaterial, Environment } from "@react-three/drei";
import { useRef, useState, useEffect } from "react";
import * as THREE from "three";

function SplittingBlob({ position, splitDirection, color, distort, speed }) {
  const meshA = useRef(null);
  const meshB = useRef(null);
  const materialRef = useRef(null);

  useFrame((state) => {
    if (!meshA.current || !meshB.current) return;
    const time = state.clock.getElapsedTime();

    // Smooth track of scroll
    const scrollY = window.scrollY || 0;
    const scrollFactor = Math.min(Math.max(scrollY / 1500, 0), 1);

    // Base organic floating motion
    const floatY = Math.sin(time * speed) * 0.2;

    // The separation distance grows exponentially as you scroll
    const separation = Math.pow(scrollFactor, 2) * 5;

    // Split targets
    const targetAX = position[0] - splitDirection[0] * separation;
    const targetAY = position[1] - splitDirection[1] * separation + floatY;
    const targetAZ = position[2] - splitDirection[2] * separation;

    const targetBX = position[0] + splitDirection[0] * separation;
    const targetBY = position[1] + splitDirection[1] * separation + floatY;
    const targetBZ = position[2] + splitDirection[2] * separation;

    meshA.current.position.lerp(
      new THREE.Vector3(targetAX, targetAY, targetAZ),
      0.08,
    );
    meshB.current.position.lerp(
      new THREE.Vector3(targetBX, targetBY, targetBZ),
      0.08,
    );

    // Spin rapidly when splitting
    const spin = scrollFactor * 3;
    meshA.current.rotation.x = Math.sin(time / 4) + spin;
    meshB.current.rotation.y = Math.cos(time / 4) + spin;

    if (materialRef.current) {
      // High distortion right at the tipping point to look like tearing
      const peakTear = Math.sin(scrollFactor * Math.PI);
      const targetDistort = Math.min(distort + peakTear * 0.6, 0.85);
      materialRef.current.distort = THREE.MathUtils.lerp(
        materialRef.current.distort,
        targetDistort,
        0.08,
      );

      const targetSpeed = speed + peakTear * 4;
      materialRef.current.speed = THREE.MathUtils.lerp(
        materialRef.current.speed,
        targetSpeed,
        0.08,
      );
    }
  });

  return (
    <group>
      <mesh ref={meshA} position={position}>
        <sphereGeometry args={[1, 64, 64]} />
        <MeshDistortMaterial
          ref={materialRef}
          color={color}
          envMapIntensity={0.8}
          clearcoat={0.8}
          clearcoatRoughness={0.2}
          metalness={0.1}
          roughness={0.4}
          distort={distort}
          speed={speed * 1.5}
          depthWrite={false}
          transparent={true}
          opacity={0.9}
        />
      </mesh>
      <mesh
        ref={meshB}
        position={[
          position[0] + 0.001,
          position[1] + 0.001,
          position[2] + 0.001,
        ]}
      >
        <sphereGeometry args={[1, 64, 64]} />
        <MeshDistortMaterial
          color={color}
          envMapIntensity={0.8}
          clearcoat={0.8}
          clearcoatRoughness={0.2}
          metalness={0.1}
          roughness={0.4}
          distort={distort}
          speed={speed * 1.5}
          depthWrite={false}
          transparent={true}
          opacity={0.9}
        />
      </mesh>
    </group>
  );
}

function Scene() {
  const [mousePosition, setMousePosition] = useState(new THREE.Vector2());

  useEffect(() => {
    const handleMouseMove = (e) => {
      setMousePosition(
        new THREE.Vector2(
          (e.clientX / window.innerWidth) * 2 - 1,
          -(e.clientY / window.innerHeight) * 2 + 1,
        ),
      );
    };
    window.addEventListener("mousemove", handleMouseMove);
    return () => window.removeEventListener("mousemove", handleMouseMove);
  }, []);

  const groupRef = useRef(null);

  useFrame(() => {
    if (groupRef.current) {
      // Parallax effect
      groupRef.current.position.x = THREE.MathUtils.lerp(
        groupRef.current.position.x,
        mousePosition.x * 2,
        0.05,
      );
      groupRef.current.position.y = THREE.MathUtils.lerp(
        groupRef.current.position.y,
        mousePosition.y * 2,
        0.05,
      );
    }
  });

  return (
    <group ref={groupRef}>
      <SplittingBlob
        position={[-3, 1, -2]}
        splitDirection={[-1, 0.5, -0.5]}
        color="#bfdbfe"
        distort={0.4}
        speed={2}
      />
      <SplittingBlob
        position={[3, -2, -4]}
        splitDirection={[0.5, 1, 0]}
        color="#93c5fd"
        distort={0.5}
        speed={1.5}
      />
      <SplittingBlob
        position={[0, -2, -1]}
        splitDirection={[-0.8, -0.2, 0.5]}
        color="#60a5fa"
        distort={0.3}
        speed={2.5}
      />
      <SplittingBlob
        position={[-4, -1, -5]}
        splitDirection={[0.5, -0.5, 0.5]}
        color="#d8b4fe"
        distort={0.2}
        speed={1}
      />
      <SplittingBlob
        position={[4, 2, -3]}
        splitDirection={[1, -0.3, -0.5]}
        color="#e9d5ff"
        distort={0.6}
        speed={3}
      />
    </group>
  );
}

export default function InteractiveBackground() {
  return (
    <div className="fixed inset-0 z-0 pointer-events-none">
      <Canvas camera={{ position: [0, 0, 8], fov: 45 }}>
        <ambientLight intensity={0.5} />
        <directionalLight
          position={[10, 10, 5]}
          intensity={1.5}
          color="#ffffff"
        />
        <directionalLight
          position={[-10, -10, -5]}
          intensity={0.5}
          color="#2563eb"
        />
        <Scene />
        <Environment preset="city" />
      </Canvas>
    </div>
  );
}
