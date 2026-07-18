import { AnimatePresence, motion } from 'framer-motion';
import { CarFront, Check, LockKeyhole, Sparkles, Trophy, X } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import wallpaper from '../../assets/carverse-sports-car.png';
import { GltfGarage } from './GltfGarage';
import { clearNewGarageReward, equippedKey, garageCatalog, getNewGarageReward, loadGarage, starterItem, type GarageItem } from './garageCatalog';
import './garage-experience.css';
import './garage-unlock.css';

const accent = ['#e9fb6b', '#38d6ff', '#ffb74f', '#ff6159'];
const sparks = Array.from({ length: 28 }, (_, index) => index);

function UnlockReveal({ item, close }: { item: GarageItem; close: () => void }) {
  return <motion.div className="garage-unlock-reveal" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
    {sparks.map(index => <motion.i key={index} style={{ left: '50%', top: '48%', background: index % 2 ? '#e9fb6b' : '#38d6ff' }} initial={{ scale: 0, opacity: 1 }} animate={{ x: Math.cos(index) * (90 + index % 5 * 25), y: Math.sin(index) * (90 + index % 5 * 25), opacity: [1, 1, 0], scale: [0, 1, .25] }} transition={{ duration: 1.35, delay: (index % 7) * .04 }} />)}
    <motion.article initial={{ scale: .72, y: 28 }} animate={{ scale: 1, y: 0 }}><button onClick={close} aria-label="Close unlock reveal"><X size={18} /></button><Trophy size={58} /><p>{item.grand ? 'GRAND UNLOCK ACHIEVED' : 'NEW GARAGE ASSET UNLOCKED'}</p><h2>{item.name}</h2><span>{item.description}</span><b><Check size={15} /> Added to your Driver Garage</b><button className="button button--primary" onClick={close}>View collection</button></motion.article>
  </motion.div>;
}

export function DriverGarage({ employeeId = 'local' }: { employeeId?: string }) {
  const [open, setOpen] = useState(false);
  const [inventory, setInventory] = useState(() => loadGarage(employeeId));
  const [selectedId, setSelectedId] = useState(() => localStorage.getItem(equippedKey(employeeId)) ?? loadGarage(employeeId)[0]);
  const [newId, setNewId] = useState(() => getNewGarageReward(employeeId));
  const [reveal, setReveal] = useState(false);
  useEffect(() => { const refresh = () => { const refreshed = loadGarage(employeeId); const equipped = localStorage.getItem(equippedKey(employeeId)); setInventory(refreshed); setSelectedId(refreshed.includes(equipped ?? '') ? equipped! : starterItem.id); setNewId(getNewGarageReward(employeeId)); }; window.addEventListener('carverse-garage-unlocked', refresh); return () => window.removeEventListener('carverse-garage-unlocked', refresh); }, [employeeId]);
  const selected = useMemo(() => garageCatalog.find(item => item.id === selectedId) ?? garageCatalog[0], [selectedId]);
  const newItem = garageCatalog.find(item => item.id === newId) ?? null;
  const select = (item: GarageItem) => { if (!inventory.includes(item.id)) return; setSelectedId(item.id); localStorage.setItem(equippedKey(employeeId), item.id); };
  const closeReveal = () => { setReveal(false); clearNewGarageReward(employeeId); setNewId(null); };
  return <>
    <button className="garage-entry" style={{ backgroundImage: `linear-gradient(90deg,#0b101bd9 8%,#0b101b99 48%,#0b101b1c),url(${wallpaper})` }} onClick={() => setOpen(true)}><span className="garage-entry__eyebrow"><CarFront size={16} /> DRIVER GARAGE</span><strong>Your collection<br /><em>awaits.</em></strong><p>{inventory.length}/{garageCatalog.length} assets unlocked · Enter showroom</p><span className="garage-entry__cta">Open driver garage <Sparkles size={15} /></span></button>
    {newItem && <motion.button className={`garage-new-unlock${newItem.grand ? ' garage-new-unlock--grand' : ''}`} onClick={() => setReveal(true)} initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} whileHover={{ y: -4, scale: 1.01 }} whileTap={{ scale: .98 }}><i className="garage-new-unlock__scan" aria-hidden /><span className="garage-new-unlock__glow" aria-hidden /><span className="garage-new-unlock__badge">{newItem.grand ? 'GRAND REWARD' : 'REWARD DROP'}</span><span className="garage-new-unlock__icon">{newItem.kind === 'vehicle' ? <CarFront size={30} /> : <Sparkles size={30} />}</span><span className="garage-new-unlock__copy"><small>NEW UNLOCK AVAILABLE</small><strong>{newItem.name}</strong><em>{newItem.grand ? 'Your prestige vehicle is ready.' : 'A new Garage asset is waiting for you.'}</em></span><span className="garage-new-unlock__cta">Reveal reward <Sparkles size={15} /></span></motion.button>}
    <AnimatePresence>{open && <motion.div className="garage-modal" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} role="dialog" aria-modal="true"><motion.main className="garage-modal__panel" initial={{ y: 28, scale: .98 }} animate={{ y: 0, scale: 1 }} exit={{ y: 24, opacity: 0 }}><button className="garage-close" onClick={() => setOpen(false)} aria-label="Close garage"><X size={20} /></button><header><div><p className="eyebrow">DRIVER GARAGE / COLLECTION</p><h2>Choose your <em>machine.</em></h2><p>Every asset is unlocked one at a time by completing verified Pit Stop demo actions.</p></div><span><Trophy size={18} />{inventory.length}/{garageCatalog.length} UNLOCKED</span></header><section className="garage-showroom"><GltfGarage file={selected.file} accent={accent[garageCatalog.indexOf(selected) % accent.length]} /><div className="garage-showroom__info"><p>{selected.grand ? 'GRAND UNLOCK / PRESTIGE VEHICLE' : selected.kind === 'vehicle' ? 'VEHICLE SHOWCASE' : 'COSMETIC SHOWCASE'}</p><h3>{selected.name}</h3><span>{selected.description}</span><b><Check size={14} /> Equipped in showroom</b></div></section><section className="garage-collection"><div className="garage-collection__heading"><span>COLLECTION LOCKER</span><small>Click an unlocked card to inspect it in 3D</small></div><div>{garageCatalog.map((item, index) => { const isUnlocked = inventory.includes(item.id); return <button key={item.id} className={`garage-item${selected.id === item.id ? ' selected' : ''}${!isUnlocked ? ' locked' : ''}${item.grand ? ' grand' : ''}`} onClick={() => select(item)}><span>{isUnlocked ? item.kind === 'vehicle' ? <CarFront size={18} /> : <Sparkles size={18} /> : <LockKeyhole size={18} />}</span><strong>{item.name}</strong><small>{isUnlocked ? item.grand ? 'GRAND UNLOCK' : item.kind.toUpperCase() : item.grand ? 'GRAND UNLOCK · LOCKED' : `LOCKED · PIT STOP ${index}`}</small></button>; })}</div></section></motion.main></motion.div>}</AnimatePresence>
    <AnimatePresence>{reveal && newItem && <UnlockReveal item={newItem} close={closeReveal} />}</AnimatePresence>
  </>;
}
