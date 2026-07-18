export type GarageItem = { id: string; name: string; kind: 'vehicle' | 'cosmetic'; file: string; description: string; starter?: boolean; grand?: boolean };

export const garageCatalog: GarageItem[] = [
  { id: 'audi-tt', name: '2003 Audi TT', kind: 'vehicle', file: '/garage-assets/2003_audi_tt.glb', description: 'Your starter performance coupe.', starter: true },
  { id: 'alfa-montreal', name: '1970 Alfa Romeo Montreal', kind: 'vehicle', file: '/garage-assets/1970_alfa_romeo_montreal.glb', description: 'A classic grand-tourer unlocked through consistent verified work.' },
  { id: 'detomaso-p900', name: '2023 De Tomaso P900', kind: 'vehicle', file: '/garage-assets/2023_de_tomaso_p900.glb', description: 'A track-focused hypercar for elite performers.' },
  { id: 'cheetax-bike', name: 'Cheetax Bike', kind: 'cosmetic', file: '/garage-assets/f61-cheetax.glb', description: 'A rare mobility collectible for your showroom.' },
  { id: 'racing-helmet', name: 'Racing Helmet', kind: 'cosmetic', file: '/garage-assets/motorcycle_helmet_-_racing_helmet.glb', description: 'A driver cosmetic earned after your first verified pit stop.' },
  { id: 'rally-wheel', name: 'Fifteen52 Rally Wheel', kind: 'cosmetic', file: '/garage-assets/fifteen52_rally_sport.glb', description: 'A precision wheel cosmetic for the pit crew.' },
  { id: 'audi-r8-etron', name: 'Audi R8 e-tron', kind: 'vehicle', file: '/garage-assets/audi_r8_e-tron_2016_optimized.glb', description: 'The optimized prestige electric supercar reserved for the final achievement.', grand: true },
];

export const starterItem = garageCatalog.find(item => item.starter)!;
export const unlockItems = garageCatalog.filter(item => !item.starter);

// Garage rewards are a demo layer, but their lifetime matches one backend run.
// When FastAPI restarts, /health reports a new process_started_at value and a
// fresh garage namespace is used automatically.
const backendRunKey = 'carverse.garage.backend-run.v1';
const currentRun = () => localStorage.getItem(backendRunKey) ?? 'awaiting-backend';
const inventoryKey = (employeeId: string) => `carverse.garage.v5.${currentRun()}.${employeeId}`;
export const equippedKey = (employeeId: string) => `carverse.garage.equipped.v5.${currentRun()}.${employeeId}`;
const newRewardKey = (employeeId: string) => `carverse.garage.new.v5.${currentRun()}.${employeeId}`;

export const setGarageBackendRun = (processStartedAt: string) => {
  if (localStorage.getItem(backendRunKey) === processStartedAt) return;
  localStorage.setItem(backendRunKey, processStartedAt);
  window.dispatchEvent(new Event('carverse-garage-unlocked'));
};

export const loadGarage = (employeeId: string) => {
  try {
    const items = JSON.parse(localStorage.getItem(inventoryKey(employeeId)) ?? 'null') as string[] | null;
    return items?.length ? items : [starterItem.id];
  } catch { return [starterItem.id]; }
};

export const getNewGarageReward = (employeeId: string) => localStorage.getItem(newRewardKey(employeeId));
export const clearNewGarageReward = (employeeId: string) => localStorage.removeItem(newRewardKey(employeeId));
export const awardNextGarageItem = (employeeId: string) => {
  const unlocked = loadGarage(employeeId);
  const next = unlockItems.find(item => !unlocked.includes(item.id));
  if (!next) return null;
  localStorage.setItem(inventoryKey(employeeId), JSON.stringify([...unlocked, next.id]));
  localStorage.setItem(newRewardKey(employeeId), next.id);
  window.dispatchEvent(new Event('carverse-garage-unlocked'));
  return next;
};
