import { motion, useScroll, useTransform } from 'framer-motion';
import {
  ArrowDownRight, ArrowUpRight, Bot, Gamepad2, LineChart,
  Menu, Moon, Radio, ShieldCheck, Sparkles, Sun, Trophy, Users, X,
} from 'lucide-react';
import { useState } from 'react';
import { Link } from 'react-router-dom';
import { FormulaCar } from './FormulaCar';
import { useTheme } from '../theme/ThemeContext';
import './landing-enhancements.css';
import sportsCarImage from '../../assets/carverse-sports-car.png';
import mobileAccessQr from '../../assets/carverse-mobile-access-qr.png';

const features = [
  { icon: Trophy, kicker: 'COMPETE WITH CONTEXT', title: 'Leagues that reward the whole dealership.', copy: 'Individual, branch, and department leaderboards turn healthy performance into a live, fair contest.' },
  { icon: Gamepad2, kicker: 'MAKE WORK PLAYABLE', title: 'Every real milestone becomes momentum.', copy: 'Deterministic XP, levels, streaks, badges, quests, and boss battles make progress tangible.' },
  { icon: Radio, kicker: 'OPERATE IN REAL TIME', title: 'See the handoff before it becomes a bottleneck.', copy: 'Booking races trace every verified stage through Sales, Finance, Accounts, Customer Care, and PDI.' },
];

const metrics = [
  ['12', 'verified race stages'],
  ['5', 'collaborating departments'],
  ['LIVE', 'leaderboard movement'],
];

export function LandingPage() {
  const [menuOpen, setMenuOpen] = useState(false);
  const [driveRotation, setDriveRotation] = useState(0);
  const { theme, toggle } = useTheme();
  const { scrollYProgress } = useScroll();
  const carX = useTransform(scrollYProgress, [0, 0.18], ['-12%', '215%']);
  const heroGlow = useTransform(scrollYProgress, [0, 0.25], [1, 0.15]);

  return (
    <main className="marketing-shell">
      <div className="ambient ambient--one" aria-hidden />
      <div className="ambient ambient--two" aria-hidden />
      <motion.header className="marketing-nav" initial={{ y: -24, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ duration: 0.6 }}>
        <Link className="brand" to="/" aria-label="CarVerse home"><span className="brand-mark">CV</span><span>CARVERSE<span className="brand-dot">.</span></span></Link>
        <nav className="nav-links" aria-label="Primary navigation">
          <a href="#why">Why CarVerse</a><a href="#game">The game loop</a><a href="#platform">Platform</a><a href="#contact">Contact</a>
        </nav>
        <div className="nav-actions"><button className="landing-theme-toggle" onClick={toggle} aria-label="Toggle light and dark mode">{theme==='dark'?<Sun size={16}/>:<Moon size={16}/>}</button><Link className="text-link" to="/login">Sign in</Link><Link className="button button--primary" to="/login">Enter the grid <ArrowUpRight size={15} /></Link></div>
        <button className="menu-button" onClick={() => setMenuOpen(!menuOpen)} aria-label="Toggle navigation">{menuOpen ? <X /> : <Menu />}</button>
      </motion.header>
      {menuOpen && <nav className="mobile-menu"><a href="#why" onClick={() => setMenuOpen(false)}>Why CarVerse</a><a href="#game" onClick={() => setMenuOpen(false)}>The game loop</a><a href="#platform" onClick={() => setMenuOpen(false)}>Platform</a><Link to="/login">Sign in</Link></nav>}

      <section className="hero-section" aria-labelledby="hero-title">
        <motion.div className="hero-grid" style={{ opacity: heroGlow }} aria-hidden />
        <div className="hero-copy">
          <motion.p className="eyebrow" initial={{ opacity: 0, y: 18 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.18 }}>THE PERFORMANCE OS FOR DEALERSHIPS</motion.p>
          <motion.h1 id="hero-title" initial={{ opacity: 0, y: 28 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.28, duration: 0.7 }}>
            Work moves<br /><em>faster</em> when<br />progress is felt.
          </motion.h1>
          <motion.p className="hero-description" initial={{ opacity: 0, y: 22 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.42 }}>CarVerse transforms real dealership milestones into a connected game of momentum, mastery, and measurable teamwork.</motion.p>
          <motion.div className="hero-actions" initial={{ opacity: 0, y: 18 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.54 }}><Link className="button button--primary" to="/login">Start your drive <ArrowUpRight size={16} /></Link><a className="button button--ghost" href="#game">Explore the platform <ArrowDownRight size={16} /></a></motion.div>
        </div>
        <motion.div className="hero-spline" initial={{ opacity: 0, scale: 0.94 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: 0.2, duration: 0.9 }}>
          <div className="spline-frame"><iframe title="CarVerse performance scene" src="https://my.spline.design/pushittothelimit-2Rv9WwSovcf43w6Two761Vhc/" frameBorder="0" loading="eager" /></div>
          <span className="spline-label">LIVE PERFORMANCE / 01</span>
        </motion.div>
        <div className="race-circuit" aria-hidden>
          <span className="circuit-line" /><motion.div className="formula-car-wrap" style={{ x: carX }}><FormulaCar /></motion.div><span className="circuit-tag">MILESTONE TRACK</span>
        </div>
        <div className="hero-meta"><span>SCROLL TO ACCELERATE</span><span className="scroll-line" /><span>01 — 05</span></div>
      </section>

      <section className="metrics-strip" aria-label="CarVerse at a glance">{metrics.map(([number, label]) => <motion.div className="metric" key={label} initial={{ opacity: 0, y: 18 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }}><strong>{number}</strong><span>{label}</span></motion.div>)}</section>

      <section id="why" className="story-section story-section--why">
        <div className="section-heading"><p className="eyebrow">THE DEALERSHIP IS A TEAM SPORT</p><h2>Every handoff has<br />a <em>human</em> impact.</h2></div>
        <div className="feature-grid">{features.map(({ icon: Icon, kicker, title, copy }, index) => <motion.article className="feature-card" key={title} initial={{ opacity: 0, y: 34 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true, amount: 0.25 }} transition={{ delay: index * 0.08 }} whileHover={{ y: -8 }}><span className="feature-icon"><Icon size={20} /></span><p className="feature-kicker">{kicker}</p><h3>{title}</h3><p>{copy}</p><span className="card-index">0{index + 1}</span></motion.article>)}</div>
      </section>
      <section className="sports-car-showcase" aria-label="CarVerse performance visual">
        <img src={sportsCarImage} alt="Futuristic red sports car" />
        <div><p className="eyebrow">MOMENTUM, VISUALIZED</p><span>EVERY VERIFIED ACTION<br />PUSHES THE DRIVE FORWARD.</span></div>
      </section>
      <section id="game" className="game-section">
        <div className="game-copy"><p className="eyebrow">THE CARVERSE GAME LOOP</p><h2>From action to<br /><em>achievement.</em></h2><p>CarVerse only celebrates work the backend can verify. That keeps every streak, mission, and rank meaningful for everyone on the grid.</p><a className="text-link text-link--bright" href="#platform">Explore the command centre <ArrowDownRight size={16} /></a></div>
        <motion.div className="game-loop" initial={{ opacity: 0, rotate: -4 }} whileInView={{ opacity: 1, rotate: 0 }} viewport={{ once: true }}>
          <button className="loop-core" onPointerDown={event => event.currentTarget.setPointerCapture(event.pointerId)} onPointerMove={event => { if (!event.currentTarget.hasPointerCapture(event.pointerId)) return; const box = event.currentTarget.getBoundingClientRect(); const angle = Math.atan2(event.clientY - box.top - box.height / 2, event.clientX - box.left - box.width / 2) * 180 / Math.PI + 90; setDriveRotation(Math.max(-130, Math.min(130, angle))); }} onPointerUp={event => event.currentTarget.releasePointerCapture(event.pointerId)} onDoubleClick={() => setDriveRotation(0)} aria-label="Interactive Drive steering control: drag the steering wheel to rotate">
            <motion.svg className="drive-steering" viewBox="0 0 100 100" animate={{ rotate: driveRotation }} transition={{ type: 'spring', stiffness: 220, damping: 19 }} aria-hidden="true"><circle cx="50" cy="50" r="30" fill="none" stroke="currentColor" strokeWidth="8" /><circle cx="50" cy="50" r="8" fill="currentColor" /><path d="M50 42V21M43 55L26 69M57 55L74 69" fill="none" stroke="currentColor" strokeWidth="7" strokeLinecap="round" /></motion.svg><span>DRIVE</span><small>GRAB / STEER</small>
          </button>
          {['Verified action', 'XP & reputation', 'Quest progress', 'Team momentum'].map((label, index) => <div className={`loop-step loop-step--${index + 1}`} key={label}><span>0{index + 1}</span>{label}</div>)}
          <div className="loop-orbit" aria-hidden />
        </motion.div>
      </section>

      <section id="platform" className="platform-section">
        <div className="section-heading section-heading--split"><div><p className="eyebrow">THE COMMAND CENTRE</p><h2>Designed for<br />the <em>whole grid.</em></h2></div><p>One system for a cleaner view of booking flow, player progression, and collective performance.</p></div>
        <div className="platform-grid">
          <article className="platform-card platform-card--wide"><div><span className="feature-icon"><LineChart size={20} /></span><h3>Live leagues, without the vanity metrics.</h3><p>Branch and department standings prioritize fair, normalized performance — not just raw volume.</p></div><div className="chart-mock" aria-label="Illustrative leaderboard visual"><span className="chart-bar chart-bar--one" /><span className="chart-bar chart-bar--two" /><span className="chart-bar chart-bar--three" /><span className="chart-line" /></div></article>
          <article className="platform-card"><span className="feature-icon"><Bot size={20} /></span><h3>AI that coaches, never decides.</h3><p>Smart recap and nudge content enriches the experience while verified rules stay in control.</p></article>
          <article className="platform-card"><span className="feature-icon"><ShieldCheck size={20} /></span><h3>Trust is part of the game.</h3><p>Clear anti-gaming safeguards make every award worth earning.</p></article>
          <article className="platform-card platform-card--accent"><span className="feature-icon"><Users size={20} /></span><h3>Boss battles make collaboration visible.</h3><p>Departments rally around shared weekly targets and celebrate together.</p></article>
        </div>
      </section>

      <section className="statement-section"><Sparkles className="statement-spark" /><p>Turning every dealership into a leaderboard,<br /><em>every milestone into momentum.</em></p><Link className="button button--primary" to="/login">Build momentum <ArrowUpRight size={16} /></Link></section>

      <footer id="contact" className="marketing-footer"><div><Link className="brand" to="/"><span className="brand-mark">CV</span><span>CARVERSE<span className="brand-dot">.</span></span></Link><p>Performance, made playable.</p></div><div><p className="footer-label">SUPPORT</p><a href="mailto:vedantjain273@gmail.com">vedantjain273@gmail.com</a></div><div className="footer-mobile-access"><img src={mobileAccessQr} alt="QR code to open CarVerse Drive on a mobile device" /><div><p className="footer-label">MOBILE ACCESS</p><strong>Scan to open on<br />your mobile device</strong></div></div><div><p className="footer-label">GET STARTED</p><Link to="/login">Enter the grid <ArrowUpRight size={14} /></Link></div></footer>
    </main>
  );
}
