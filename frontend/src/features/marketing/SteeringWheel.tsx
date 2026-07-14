import { motion, useMotionValue, useSpring } from 'framer-motion';
import { useRef } from 'react';

export function SteeringWheel() {
  const rotation = useMotionValue(0);
  const smoothRotation = useSpring(rotation, { stiffness: 180, damping: 18 });
  const active = useRef(false);
  function steer(event: React.PointerEvent<HTMLButtonElement>) {
    if (!active.current) return;
    const rect = event.currentTarget.getBoundingClientRect();
    const angle = Math.atan2(event.clientY - (rect.top + rect.height / 2), event.clientX - (rect.left + rect.width / 2)) * 180 / Math.PI;
    rotation.set(Math.max(-105, Math.min(105, angle + 90)));
  }
  return <button className="steering-wheel" onPointerDown={event => { active.current = true; event.currentTarget.setPointerCapture(event.pointerId); steer(event); }} onPointerMove={steer} onPointerUp={() => { active.current = false; }} aria-label="Interactive steering wheel: drag to steer"><motion.svg viewBox="0 0 160 160" style={{ rotate: smoothRotation }}><circle cx="80" cy="80" r="62" fill="none" stroke="currentColor" strokeWidth="12"/><circle cx="80" cy="80" r="18" fill="currentColor"/><path d="M80 62V18M63 89L27 116M97 89L133 116" stroke="currentColor" strokeWidth="10" strokeLinecap="round"/></motion.svg><span>DRAG TO STEER</span></button>;
}
