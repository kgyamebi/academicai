/**
 * Shared motion helpers — no animation library.
 * Quiet, expo-eased value animation for premium academic UX.
 */

export function prefersReducedMotion(): boolean {
  if (typeof window === "undefined") return false;
  return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

/** Expo-out: fast start, soft landing (Apple/Linear feel). */
export function easeOutExpo(t: number): number {
  return t >= 1 ? 1 : 1 - Math.pow(2, -10 * t);
}

/** Ease that accelerates then decelerates (score count-up). */
export function easeInOutCubic(t: number): number {
  return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
}

export type AnimateValueOptions = {
  from?: number;
  to: number;
  duration?: number;
  ease?: (t: number) => number;
  onUpdate: (value: number) => void;
  onComplete?: () => void;
};

export function animateValue({
  from = 0,
  to,
  duration = 900,
  ease = easeOutExpo,
  onUpdate,
  onComplete,
}: AnimateValueOptions): () => void {
  if (prefersReducedMotion() || duration <= 0) {
    onUpdate(to);
    onComplete?.();
    return () => undefined;
  }

  let frame = 0;
  const start = performance.now();

  const tick = (now: number) => {
    const t = Math.min(1, (now - start) / duration);
    onUpdate(from + (to - from) * ease(t));
    if (t < 1) {
      frame = requestAnimationFrame(tick);
    } else {
      onUpdate(to);
      onComplete?.();
    }
  };

  frame = requestAnimationFrame(tick);
  return () => cancelAnimationFrame(frame);
}
