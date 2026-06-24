import { Canvas, useFrame } from "@react-three/fiber";
import { MeshDistortMaterial } from "@react-three/drei";
import { useRef, useEffect } from "react";
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
    const separation = 0.42 + Math.pow(scrollFactor, 2) * 5;

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
        <sphereGeometry args={[0.82, 48, 48]} />
        <MeshDistortMaterial
          ref={materialRef}
          color={color}
          envMapIntensity={0.8}
          clearcoat={0.8}
          clearcoatRoughness={0.2}
          metalness={0}
          roughness={0.55}
          distort={distort}
          speed={speed * 1.5}
          depthWrite={false}
          transparent={true}
          opacity={0.34}
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
        <sphereGeometry args={[0.82, 48, 48]} />
        <MeshDistortMaterial
          color={color}
          envMapIntensity={0.8}
          clearcoat={0.8}
          clearcoatRoughness={0.2}
          metalness={0}
          roughness={0.55}
          distort={distort}
          speed={speed * 1.5}
          depthWrite={false}
          transparent={true}
          opacity={0.24}
        />
      </mesh>
    </group>
  );
}

function Scene() {
  const mousePosition = useRef(new THREE.Vector2());

  useEffect(() => {
    const handleMouseMove = (e) => {
      mousePosition.current.set(
        (e.clientX / window.innerWidth) * 2 - 1,
        -(e.clientY / window.innerHeight) * 2 + 1,
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
        mousePosition.current.x * 2,
        0.05,
      );
      groupRef.current.position.y = THREE.MathUtils.lerp(
        groupRef.current.position.y,
        mousePosition.current.y * 2,
        0.05,
      );
    }
  });

  return (
    <group ref={groupRef}>
      <SplittingBlob
        position={[-3.6, 1, -3]}
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
        position={[0, -3, -4]}
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
    <div
      className="fixed inset-0 z-0 pointer-events-none overflow-hidden"
      aria-hidden="true"
      data-testid="interactive-background"
    >
      <div className="absolute -left-24 top-24 h-80 w-80 rounded-full bg-blue-200/35 blur-3xl" />
      <div className="absolute -right-20 top-12 h-96 w-96 rounded-full bg-violet-200/30 blur-3xl" />
      <div className="absolute bottom-0 left-1/3 h-80 w-80 rounded-full bg-sky-200/30 blur-3xl" />
      <Canvas
        camera={{ position: [0, 0, 8], fov: 45 }}
        dpr={[1, 1.5]}
        gl={{
          alpha: true,
          antialias: true,
          powerPreference: "high-performance",
        }}
      >
        <ambientLight intensity={1.1} />
        <hemisphereLight args={["#ffffff", "#bfdbfe", 1.4]} />
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
      </Canvas>
    </div>
  );
}
