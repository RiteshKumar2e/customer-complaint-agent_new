import { useEffect, useRef } from "react";

// OJASS-style cursor: a soft glowing orb glued to the pointer plus a few
// embers that drift upward and fade. Built to stay cheap:
//  - glow sprites are rendered once per theme and blitted with drawImage
//    (no per-frame createRadialGradient / shadowBlur)
//  - embers live in a fixed ring-buffer pool, spawned by distance travelled
//    inside the rAF tick, never inside the pointer handler
//  - the rAF loop stops itself when nothing is moving
//  - disabled on touch / reduced-motion / weak devices, and steps down
//    automatically if frames get slow

const POOL_SIZE = 64;
const SPAWN_SPACING = 8; // px of pointer travel per ember
const MAX_SPAWN_PER_FRAME = 4;
const ORB_FOLLOW = 0.75; // per-60fps-frame smoothing; high = tight to pointer
const SLOW_FRAME_MS = 28;

const THEMES = {
  dark: {
    composite: "lighter",
    glow: [0, 210, 255],
    core: [255, 255, 255],
    embers: [[0, 210, 255], [255, 255, 255]],
    glowAlpha: 0.55,
    emberAlpha: 0.95,
  },
  light: {
    composite: "source-over",
    glow: [59, 130, 246],
    core: [37, 99, 235],
    embers: [[37, 99, 235], [96, 165, 250]],
    glowAlpha: 0.18,
    emberAlpha: 0.55,
  },
};

// 0 = off, 1 = orb + few embers, 2 = full
function detectQuality() {
  if (typeof window === "undefined" || !window.matchMedia) return 0;
  const mq = (q) => window.matchMedia(q).matches;
  if (mq("(pointer: coarse)") || !mq("(hover: hover)")) return 0;
  if (mq("(prefers-reduced-motion: reduce)")) return 0;
  const nav = window.navigator || {};
  if (nav.connection && nav.connection.saveData) return 0;
  const cores = nav.hardwareConcurrency || 4;
  const memory = nav.deviceMemory || 4;
  if (cores <= 2 || memory <= 2) return 0;
  return cores <= 4 || memory <= 4 ? 1 : 2;
}

function makeSprite(size, stops) {
  const c = document.createElement("canvas");
  c.width = c.height = size;
  const g = c.getContext("2d");
  if (!g) return null;
  const r = size / 2;
  const grad = g.createRadialGradient(r, r, 0, r, r, r);
  stops.forEach(([at, color]) => grad.addColorStop(at, color));
  g.fillStyle = grad;
  g.fillRect(0, 0, size, size);
  return c;
}

function buildSprites(theme) {
  const rgba = ([r, g, b], a) => `rgba(${r}, ${g}, ${b}, ${a})`;
  return {
    glow: makeSprite(128, [
      [0, rgba(theme.glow, 0.9)],
      [0.35, rgba(theme.glow, 0.35)],
      [1, rgba(theme.glow, 0)],
    ]),
    core: makeSprite(32, [
      [0, rgba(theme.core, 1)],
      [0.45, rgba(theme.core, 0.85)],
      [1, rgba(theme.glow, 0)],
    ]),
    embers: theme.embers.map((color) =>
      makeSprite(24, [
        [0, rgba(color, 1)],
        [0.4, rgba(color, 0.6)],
        [1, rgba(color, 0)],
      ])
    ),
  };
}

export default function CursorTrail() {
  const canvasRef = useRef(null);

  useEffect(() => {
    let quality = detectQuality();
    const canvas = canvasRef.current;
    if (!quality || !canvas) return;
    const ctx = canvas.getContext("2d", { alpha: true });
    if (!ctx) return;

    document.body.classList.add("custom-cursor-active");

    const isLight = () => document.body.classList.contains("light-theme");
    let theme = isLight() ? THEMES.light : THEMES.dark;
    let sprites = buildSprites(theme);

    const observer = new MutationObserver(() => {
      const next = isLight() ? THEMES.light : THEMES.dark;
      if (next === theme) return;
      theme = next;
      sprites = buildSprites(theme);
      wake();
    });
    observer.observe(document.body, { attributes: true, attributeFilter: ["class"] });

    // Capped DPR keeps the full-viewport clear cheap on 4K / retina screens.
    let dpr = 1;
    const resize = () => {
      dpr = Math.min(window.devicePixelRatio || 1, 1.5);
      canvas.width = Math.round(window.innerWidth * dpr);
      canvas.height = Math.round(window.innerHeight * dpr);
      wake();
    };

    const pool = Array.from({ length: POOL_SIZE }, () => ({
      x: 0, y: 0, vx: 0, vy: 0, life: 0, decay: 0, size: 0, sprite: 0,
    }));
    let head = 0;
    let alive = 0;

    const target = { x: 0, y: 0 };
    const orb = { x: 0, y: 0, alpha: 0 };
    let visible = false;
    let hasPointer = false;
    let travel = 0;
    let lastSpawn = { x: 0, y: 0 };

    let rafId = 0;
    let lastTime = 0;
    let slowFrames = 0;

    const spawn = (x, y) => {
      const p = pool[head];
      head = (head + 1) % POOL_SIZE;
      if (p.life <= 0) alive++;
      const angle = Math.random() * Math.PI * 2;
      const speed = Math.random() * 1.6 + 0.4;
      p.x = x + (Math.random() - 0.5) * 20;
      p.y = y + (Math.random() - 0.5) * 20;
      p.vx = Math.cos(angle) * speed;
      p.vy = Math.sin(angle) * speed - 1.2; // upward bias, like rising embers
      p.life = 1;
      p.decay = 0.014 + Math.random() * 0.01;
      p.size = Math.random() * 6 + 4;
      p.sprite = Math.random() < 0.8 ? 0 : 1; // mostly theme colour, a few bright sparks
    };

    const frame = (time) => {
      rafId = 0;
      const dt = lastTime ? Math.min(time - lastTime, 64) : 16.67;
      lastTime = time;
      const step = dt / 16.67; // normalise motion to 60fps so 120Hz looks the same

      // Adaptive step-down: sustained slow frames => fewer embers. Never turns
      // the cursor off at runtime; the orb itself is only two drawImage calls.
      if (quality > 1 && dt > SLOW_FRAME_MS) {
        if (++slowFrames > 90) {
          quality = 1;
          slowFrames = 0;
        }
      } else if (slowFrames > 0) {
        slowFrames--;
      }

      // Orb follows the pointer with frame-rate independent smoothing.
      const follow = 1 - Math.pow(1 - ORB_FOLLOW, step);
      orb.x += (target.x - orb.x) * follow;
      orb.y += (target.y - orb.y) * follow;
      orb.alpha += ((visible ? 1 : 0) - orb.alpha) * Math.min(1, 0.2 * step);

      // Spawn embers from distance travelled since the last spawn.
      if (visible) {
        const dx = target.x - lastSpawn.x;
        const dy = target.y - lastSpawn.y;
        travel += Math.sqrt(dx * dx + dy * dy);
        lastSpawn.x = target.x;
        lastSpawn.y = target.y;
        const spacing = quality === 2 ? SPAWN_SPACING : SPAWN_SPACING * 2.5;
        let n = 0;
        while (travel >= spacing && n < MAX_SPAWN_PER_FRAME) {
          spawn(target.x, target.y);
          travel -= spacing;
          n++;
        }
        if (travel > spacing) travel = 0; // don't bank a backlog on fast flicks
      }

      ctx.setTransform(1, 0, 0, 1, 0, 0);
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      ctx.globalCompositeOperation = theme.composite;

      for (let i = 0; i < POOL_SIZE; i++) {
        const p = pool[i];
        if (p.life <= 0) continue;
        p.vx *= Math.pow(0.97, step);
        p.vy = p.vy * Math.pow(0.97, step) - 0.04 * step;
        p.x += p.vx * step;
        p.y += p.vy * step;
        p.life -= p.decay * step;
        if (p.life <= 0) {
          alive--;
          continue;
        }
        const s = p.size * (0.4 + p.life * 0.6);
        const img = sprites.embers[p.sprite];
        if (!img) continue;
        ctx.globalAlpha = p.life * theme.emberAlpha;
        ctx.drawImage(img, p.x - s / 2, p.y - s / 2, s, s);
      }

      if (orb.alpha > 0.01 && sprites.glow && sprites.core) {
        ctx.globalAlpha = orb.alpha * theme.glowAlpha;
        ctx.drawImage(sprites.glow, orb.x - 36, orb.y - 36, 72, 72);
        ctx.globalAlpha = orb.alpha;
        ctx.drawImage(sprites.core, orb.x - 9, orb.y - 9, 18, 18);
      }
      ctx.globalAlpha = 1;
      ctx.globalCompositeOperation = "source-over";

      // Keep ticking only while something is still changing.
      const settling =
        Math.abs(target.x - orb.x) > 0.1 ||
        Math.abs(target.y - orb.y) > 0.1 ||
        Math.abs((visible ? 1 : 0) - orb.alpha) > 0.01;
      if (alive > 0 || settling) {
        rafId = requestAnimationFrame(frame);
      } else {
        lastTime = 0;
      }
    };

    function wake() {
      if (!rafId && !document.hidden) rafId = requestAnimationFrame(frame);
    }

    // The handler only records the latest position; all work happens once per frame.
    const onPointerMove = (e) => {
      if (e.pointerType === "touch") return;
      target.x = e.clientX;
      target.y = e.clientY;
      if (!hasPointer) {
        hasPointer = true;
        orb.x = lastSpawn.x = target.x;
        orb.y = lastSpawn.y = target.y;
      }
      visible = true;
      wake();
    };
    const onPointerLeave = () => {
      visible = false;
      hasPointer = false;
      wake();
    };
    const onVisibility = () => {
      if (document.hidden) {
        cancelAnimationFrame(rafId);
        rafId = 0;
        lastTime = 0;
      } else {
        wake();
      }
    };

    window.addEventListener("resize", resize, { passive: true });
    window.addEventListener("pointermove", onPointerMove, { passive: true });
    document.documentElement.addEventListener("pointerleave", onPointerLeave);
    document.addEventListener("visibilitychange", onVisibility);
    resize();

    let tornDown = false;
    function teardown() {
      if (tornDown) return;
      tornDown = true;
      cancelAnimationFrame(rafId);
      rafId = 0;
      window.removeEventListener("resize", resize);
      window.removeEventListener("pointermove", onPointerMove);
      document.documentElement.removeEventListener("pointerleave", onPointerLeave);
      document.removeEventListener("visibilitychange", onVisibility);
      observer.disconnect();
      document.body.classList.remove("custom-cursor-active");
      ctx.setTransform(1, 0, 0, 1, 0, 0);
      ctx.clearRect(0, 0, canvas.width, canvas.height);
    }

    return teardown;
  }, []);

  return (
    <canvas
      ref={canvasRef}
      aria-hidden="true"
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        width: "100%",
        height: "100%",
        pointerEvents: "none",
        zIndex: 2000000, // above all modals (Sign-In Prompt is 999999)
      }}
    />
  );
}
