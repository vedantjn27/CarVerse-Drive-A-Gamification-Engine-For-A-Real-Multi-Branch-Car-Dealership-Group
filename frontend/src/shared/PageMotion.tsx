import { motion } from 'framer-motion';
import type { PropsWithChildren } from 'react';

export function PageMotion({ children }: PropsWithChildren) {
  return <motion.main className="app-page" initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -8 }} transition={{ duration: 0.28 }}>{children}</motion.main>;
}
