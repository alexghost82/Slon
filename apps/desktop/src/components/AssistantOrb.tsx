import { useEffect, useRef } from "react";
import type { AssistantState } from "../lib/types";

interface AssistantOrbProps {
  state: AssistantState;
}

function stateEnergy(state: AssistantState): number {
  switch (state) {
    case "listening":
      return 1.1;
    case "thinking":
      return 1.35;
    case "speaking":
      return 1.55;
    case "muted":
      return 0.45;
    case "error":
    case "missingApiKey":
      return 0.75;
    case "offline":
      return 0.35;
    default:
      return 0.9;
  }
}

function displayState(state: AssistantState): string {
  if (state === "missingApiKey") return "LISTENING";
  return state.toUpperCase();
}

export function AssistantOrb({ state }: AssistantOrbProps) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const context = canvas.getContext("2d");
    if (!context) return;

    const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    let frame = 0;
    let animationId = 0;

    const resize = () => {
      const rect = canvas.getBoundingClientRect();
      const ratio = window.devicePixelRatio || 1;
      canvas.width = Math.max(1, Math.floor(rect.width * ratio));
      canvas.height = Math.max(1, Math.floor(rect.height * ratio));
      context.setTransform(ratio, 0, 0, ratio, 0, 0);
    };

    const draw = () => {
      const width = canvas.clientWidth;
      const height = canvas.clientHeight;
      const centerX = width / 2;
      const centerY = height / 2;
      const radius = Math.min(width, height) * 0.29;
      const energy = stateEnergy(state);
      const time = frame / 60;

      context.clearRect(0, 0, width, height);
      context.fillStyle = "rgba(2, 7, 18, 0.58)";
      context.fillRect(0, 0, width, height);

      const starCount = reducedMotion ? 38 : 90;
      for (let index = 0; index < starCount; index += 1) {
        const x = (Math.sin(index * 74.13) * 0.5 + 0.5) * width;
        const y = (Math.cos(index * 31.71) * 0.5 + 0.5) * height;
        const alpha = 0.12 + ((index % 5) * 0.035);
        context.fillStyle = `rgba(137, 219, 255, ${alpha})`;
        context.fillRect(x, y, 1, 1);
      }

      const aura = context.createRadialGradient(centerX, centerY, radius * 0.15, centerX, centerY, radius * 1.9);
      aura.addColorStop(0, `rgba(124, 246, 255, ${0.22 * energy})`);
      aura.addColorStop(0.45, `rgba(118, 80, 255, ${0.16 * energy})`);
      aura.addColorStop(0.8, "rgba(20, 12, 48, 0.22)");
      aura.addColorStop(1, "rgba(0, 0, 0, 0)");
      context.fillStyle = aura;
      context.beginPath();
      context.arc(centerX, centerY, radius * 2.1, 0, Math.PI * 2);
      context.fill();

      context.globalCompositeOperation = "lighter";

      for (let cloud = 0; cloud < 7; cloud += 1) {
        context.save();
        context.translate(centerX, centerY);
        context.rotate((reducedMotion ? 0 : time * (0.08 + cloud * 0.018)) + cloud * 0.62);
        context.lineWidth = 8 + cloud * 1.3;
        context.lineCap = "round";
        context.lineJoin = "round";
        context.shadowBlur = 26 + cloud * 4;
        context.shadowColor = cloud % 3 === 0 ? "rgba(43, 234, 255, 0.8)" : cloud % 3 === 1 ? "rgba(162, 76, 255, 0.7)" : "rgba(255, 245, 226, 0.5)";
        context.strokeStyle = cloud % 3 === 0 ? `rgba(43, 234, 255, ${0.18 + energy * 0.09})` : cloud % 3 === 1 ? `rgba(163, 78, 255, ${0.16 + energy * 0.08})` : `rgba(255, 247, 230, ${0.12 + energy * 0.06})`;
        context.beginPath();
        for (let step = 0; step <= 150; step += 1) {
          const angle = (step / 150) * Math.PI * 2;
          const pulse = Math.sin(angle * (3 + cloud) + time * (0.9 + cloud * 0.13)) * 16;
          const thread = Math.cos(angle * (7 + cloud * 2) - time * 1.4) * 9;
          const ringRadius = radius * (0.86 + cloud * 0.025) + (pulse + thread) * energy;
          const x = Math.cos(angle) * ringRadius;
          const y = Math.sin(angle) * ringRadius;
          if (step === 0) context.moveTo(x, y);
          else context.lineTo(x, y);
        }
        context.closePath();
        context.stroke();
        context.restore();
      }

      const plasmaCount = reducedMotion ? 20 : 72;
      for (let index = 0; index < plasmaCount; index += 1) {
        const angle = (index / plasmaCount) * Math.PI * 2;
        const wobble = Math.sin(time * 1.7 + index * 0.73) * 15 * energy;
        const inner = radius * (0.55 + (index % 5) * 0.035) + wobble;
        const outer = radius * (1.0 + (index % 7) * 0.025) + Math.cos(time * 1.2 + index) * 18 * energy;
        const curve = angle + Math.sin(time + index) * 0.45;
        const x1 = centerX + Math.cos(angle) * inner;
        const y1 = centerY + Math.sin(angle) * inner;
        const x2 = centerX + Math.cos(angle + 0.18) * outer;
        const y2 = centerY + Math.sin(angle + 0.18) * outer;
        const cx = centerX + Math.cos(curve) * radius * 0.92;
        const cy = centerY + Math.sin(curve) * radius * 0.92;

        context.strokeStyle = index % 4 === 0 ? "rgba(247, 251, 255, 0.66)" : index % 4 === 1 ? "rgba(37, 229, 255, 0.52)" : index % 4 === 2 ? "rgba(181, 78, 255, 0.46)" : "rgba(255, 151, 86, 0.26)";
        context.lineWidth = index % 9 === 0 ? 2.4 : 0.9;
        context.shadowBlur = 20;
        context.shadowColor = index % 3 === 0 ? "rgba(70, 224, 255, 0.56)" : "rgba(164, 76, 255, 0.46)";
        context.beginPath();
        context.moveTo(x1, y1);
        context.quadraticCurveTo(cx, cy, x2, y2);
        context.stroke();
      }

      for (let flare = 0; flare < 18; flare += 1) {
        const angle = flare * 0.91 + time * 0.35;
        const distance = radius * (0.78 + (flare % 6) * 0.07);
        const x = centerX + Math.cos(angle) * distance;
        const y = centerY + Math.sin(angle) * distance;
        const glow = context.createRadialGradient(x, y, 0, x, y, 26 + (flare % 4) * 10);
        glow.addColorStop(0, flare % 3 === 0 ? "rgba(255, 248, 230, 0.48)" : "rgba(70, 232, 255, 0.38)");
        glow.addColorStop(1, "rgba(0, 0, 0, 0)");
        context.fillStyle = glow;
        context.beginPath();
        context.arc(x, y, 28, 0, Math.PI * 2);
        context.fill();
      }

      context.globalCompositeOperation = "source-over";

      const core = context.createRadialGradient(centerX, centerY, 0, centerX, centerY, radius * 0.36);
      core.addColorStop(0, "rgba(230, 252, 255, 0.92)");
      core.addColorStop(0.45, "rgba(46, 226, 255, 0.42)");
      core.addColorStop(1, "rgba(11, 29, 61, 0)");
      context.fillStyle = core;
      context.beginPath();
      context.arc(centerX, centerY, radius * 0.36, 0, Math.PI * 2);
      context.fill();

      const bars = 9;
      context.shadowBlur = 18;
      context.shadowColor = "rgba(37, 224, 255, 0.75)";
      context.strokeStyle = "rgba(197, 249, 255, 0.9)";
      context.lineCap = "round";
      for (let index = 0; index < bars; index += 1) {
        const offset = index - Math.floor(bars / 2);
        const barHeight = 14 + Math.abs(Math.sin(time * 2.4 + index * 0.8)) * 28 * energy;
        const x = centerX + offset * 6;
        context.lineWidth = index === Math.floor(bars / 2) ? 3 : 2;
        context.beginPath();
        context.moveTo(x, centerY - barHeight / 2);
        context.lineTo(x, centerY + barHeight / 2);
        context.stroke();
      }

      context.shadowBlur = 0;
      context.font = "11px ui-monospace, SFMono-Regular, Menlo, monospace";
      context.fillStyle = state === "offline" ? "rgba(91, 116, 138, 0.85)" : "rgba(176, 245, 255, 0.86)";
      context.textAlign = "center";
      context.fillText(displayState(state), centerX, centerY + radius + 54);

      if (!reducedMotion) {
        frame += 1;
        animationId = window.requestAnimationFrame(draw);
      }
    };

    resize();
    draw();
    window.addEventListener("resize", resize);

    return () => {
      window.removeEventListener("resize", resize);
      window.cancelAnimationFrame(animationId);
    };
  }, [state]);

  return <canvas className="assistant-orb" ref={canvasRef} aria-label={`Assistant state: ${state}`} />;
}