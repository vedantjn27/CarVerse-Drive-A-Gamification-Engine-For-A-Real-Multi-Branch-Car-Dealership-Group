import { motion } from 'framer-motion';
import { ArrowLeft } from 'lucide-react';
import { Link } from 'react-router-dom';

export function NotFoundPage() {
  return (
    <main className="not-found">
      <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}>
        <p className="eyebrow">404 / LOST ON THE CIRCUIT</p>
        <h1>This route is not on the map.</h1>
        <Link to="/" className="button button--primary"><ArrowLeft size={16} /> Return to CarVerse</Link>
      </motion.div>
    </main>
  );
}
