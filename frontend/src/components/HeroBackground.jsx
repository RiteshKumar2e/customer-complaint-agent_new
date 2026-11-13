// 3D starfield behind the landing hero (dark theme only). Loaded lazily by
// Landing so three.js does not delay the first paint.
import { useState, useEffect, useRef } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { Points, PointMaterial, Stars } from "@react-three/drei";
import * as random from "maath/random/dist/maath-random.esm";

// --- Internal 3D Components (Conditional Dark Mode) ---
function ParticleGlobe() {
  const ref = useRef();
  const [isMobile] = useState(() => window.innerWidth < 768);
  const particleCount = isMobile ? 300 : 800;
  const [sphere] = useState(() => random.inSphere(new Float32Array(particleCount * 3), { radius: 1.5 }));

  useFrame((state, delta) => {
    if (ref.current) {
      ref.current.rotation.x -= delta / 20;
      ref.current.rotation.y -= delta / 25;
    }
  });

  return (
    <group rotation={[0, 0, Math.PI / 4]}>
      <Points ref={ref} positions={sphere} stride={3} frustumCulled={false}>
        <PointMaterial
          transparent
          color="#818cf8"
          size={0.005}
          sizeAttenuation={true}
          depthWrite={false}
          blending={1}
        />
      </Points>
    </group>
  );
}

function FloatingGeometry() {
  const group = useRef();
  useFrame((state) => {
    const time = state.clock.getElapsedTime();
    group.current.rotation.y = Math.sin(time / 4) / 4;
    group.current.rotation.x = Math.cos(time / 4) / 4;
  });

  return (
    <group ref={group}>
      <mesh position={[-1.2, 0.5, -0.5]}>
        <icosahedronGeometry args={[0.2, 1]} />
        <meshStandardMaterial color="#6366f1" wireframe transparent opacity={0.15} />
      </mesh>
      <mesh position={[1.2, -0.5, -0.5]}>
        <icosahedronGeometry args={[0.25, 1]} />
        <meshStandardMaterial color="#818cf8" wireframe transparent opacity={0.15} />
      </mesh>
    </group>
  );
}

export default function HeroBackground() {
  const [isLight, setIsLight] = useState(() => document.body.classList.contains('light-theme'));

  useEffect(() => {
    const observer = new MutationObserver(() => {
      setIsLight(document.body.classList.contains('light-theme'));
    });
    observer.observe(document.body, { attributes: true, attributeFilter: ['class'] });
    return () => observer.disconnect();
  }, []);

  if (isLight) return null;

  return (
    <div className="three-bg-overlay-landing">
      <Canvas dpr={[1, 1.5]} camera={{ position: [0, 0, 1.2] }}>
        <ambientLight intensity={0.5} />
        <pointLight position={[10, 10, 10]} intensity={1} />
        <Stars radius={80} depth={40} count={isLight ? 300 : 1000} factor={4} saturation={0} fade speed={1} />
        <ParticleGlobe />
        <FloatingGeometry />
      </Canvas>
    </div>
  );
}

