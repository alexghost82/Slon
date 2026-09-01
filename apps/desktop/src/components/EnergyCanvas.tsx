import { useEffect, useRef } from "react";

interface Particle {
  angle: number;
  radius: number;
  speed: number;
  opacity: number;
  depth: number;
  hue: number;
}

interface EnergyCanvasProps {
  intensity: number;
}

export function EnergyCanvas({ intensity }: EnergyCanvasProps) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    const context = canvas?.getContext("2d");
    if (!canvas || !context) return;

    const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    let width = 0;
    let height = 0;
    let frame = 0;
    let animationId = 0;
    let particles: Particle[] = [];

    const seed = () => {
      particles = [];
      const count = reducedMotion ? 260 : Math.min(1250, Math.floor((width * height) / 1100));
      for (let index = 0; index < count; index += 1) {
        particles.push({
          angle: Math.random() * Math.PI * 2,
          radius: Math.random() ** 0.55 * Math.min(width, height) * 0.29,
          speed: 0.0008 + Math.random() * 0.0026,
          opacity: 0.12 + Math.random() * 0.72,
          depth: Math.random(),
          hue: Math.random() < 0.12 ? 42 : 176,
        });
      }
    };

    const resize = () => {
      const ratio = Math.min(window.devicePixelRatio || 1, 2);
      width = window.innerWidth;
      height = window.innerHeight;
      canvas.width = Math.floor(width * ratio);
      canvas.height = Math.floor(height * ratio);
      canvas.style.width = `${width}px`;
      canvas.style.height = `${height}px`;
      context.setTransform(ratio, 0, 0, ratio, 0, 0);
      seed();
    };

    const draw = () => {
      frame += 0.012;
      context.clearRect(0, 0, width, height);
      const centerX = width < 1150 ? width * 0.62 : width * 0.5;
      const centerY = height * 0.49;
      const radius = Math.min(width, height) * 0.29;

      const gradient = context.createRadialGradient(centerX, centerY, radius * 0.12, centerX, centerY, radius * 1.35);
      gradient.addColorStop(0, "rgba(0,255,237,.025)");
      gradient.addColorStop(0.5, "rgba(0,137,140,.045)");
      gradient.addColorStop(1, "rgba(0,0,0,0)");
      context.fillStyle = gradient;
      context.fillRect(0, 0, width, height);

      context.save();
      context.globalCompositeOperation = "lighter";
      for (const particle of particles) {
        particle.angle += particle.speed * (1 + intensity * 0.55);
        const wobble = Math.sin(frame * 1.8 + particle.angle * 3 + particle.depth * 8) * radius * (0.035 + 0.02 * intensity);
        const particleRadius = particle.radius + wobble;
        const x = centerX + Math.cos(particle.angle + frame * 0.09) * particleRadius * 1.03;
        const y = centerY + Math.sin(particle.angle * 1.03 - frame * 0.08) * particleRadius * 0.93;
        const alpha = particle.opacity * (0.28 + 0.5 * (1 - particle.radius / (radius * 1.25)));
        context.fillStyle = particle.hue === 42 ? `rgba(245,190,98,${alpha * 0.7})` : `rgba(49,242,230,${alpha})`;
        const size = 0.6 + particle.depth * 1.5;
        context.fillRect(x, y, size, size);
      }

      for (let band = 0; band < 16; band += 1) {
        const angleOffset = frame * 0.13 + band * 0.39;
        context.beginPath();
        for (let point = 0; point <= 160; point += 1) {
          const angle = (point / 160) * Math.PI * 2 + angleOffset;
          const bandRadius = radius * (0.66 + 0.13 * Math.sin(angle * 3 + frame * 1.7 + band) + 0.05 * Math.sin(angle * 9 - frame * 2.1 + band * 2));
          const x = centerX + Math.cos(angle) * bandRadius * 1.05;
          const y = centerY + Math.sin(angle) * bandRadius * 0.93;
          if (point === 0) context.moveTo(x, y);
          else context.lineTo(x, y);
        }
        context.closePath();
        context.strokeStyle = band % 5 === 0 ? "rgba(244,190,100,.16)" : "rgba(45,236,226,.11)";
        context.lineWidth = 0.6 + (band % 3) * 0.25;
        context.stroke();
      }

      for (let ellipse = 0; ellipse < 5; ellipse += 1) {
        context.beginPath();
        context.ellipse(centerX, centerY, radius * (0.82 + ellipse * 0.13), radius * (0.82 + ellipse * 0.08), frame * 0.04 + ellipse * 0.3, 0, Math.PI * 2);
        context.strokeStyle = `rgba(51,231,224,${0.05 - ellipse * 0.006})`;
        context.lineWidth = 0.7;
        context.stroke();
      }
      context.restore();

      if (!reducedMotion) animationId = window.requestAnimationFrame(draw);
    };

    resize();
    draw();
    window.addEventListener("resize", resize);
    return () => {
      window.removeEventListener("resize", resize);
      window.cancelAnimationFrame(animationId);
    };
  }, [intensity]);

  return <canvas id="energyCanvas" ref={canvasRef} aria-hidden="true" />;
}