import { motion } from 'framer-motion';

export function FormulaCar() {
  return (
    <motion.svg className="formula-car" viewBox="0 0 260 96" fill="none" xmlns="http://www.w3.org/2000/svg" animate={{ y: [0, -3, 0], rotate: [-1, 1, -1] }} transition={{ duration: 1.8, repeat: Infinity, ease: 'easeInOut' }}>
      <path d="M17 46H67L84 28H172L190 46H243L253 59H196L179 78H84L66 59H7L17 46Z" fill="currentColor" />
      <path d="M86 28L102 11H155L174 28" stroke="currentColor" strokeWidth="9" strokeLinejoin="round" />
      <path d="M99 47L112 30H151L164 47" fill="#11151E" />
      <path d="M118 30L124 18H141L148 30" fill="#E9FB6B" />
      <path d="M42 47V63M219 47V63" stroke="#11151E" strokeWidth="15" strokeLinecap="round" />
      <path d="M8 59H58M202 59H252" stroke="#E9FB6B" strokeWidth="5" />
      <path d="M93 78L103 91H158L170 78" stroke="currentColor" strokeWidth="7" />
      <circle cx="80" cy="72" r="14" fill="#07090E" /><circle cx="181" cy="72" r="14" fill="#07090E" />
    </motion.svg>
  );
}
