import { createContext, useContext, useEffect, useState, type PropsWithChildren } from 'react';
type Theme = 'dark' | 'light';
const ThemeContext = createContext<{ theme: Theme; toggle: () => void } | undefined>(undefined);
export function ThemeProvider({ children }: PropsWithChildren) { const [theme, setTheme] = useState<Theme>(() => (localStorage.getItem('carverse.theme') as Theme) || 'dark'); useEffect(() => { document.documentElement.dataset.theme = theme; localStorage.setItem('carverse.theme', theme); }, [theme]); return <ThemeContext.Provider value={{ theme, toggle: () => setTheme(value => value === 'dark' ? 'light' : 'dark') }}>{children}</ThemeContext.Provider>; }
export function useTheme() { const context = useContext(ThemeContext); if (!context) throw new Error('useTheme must be used within ThemeProvider'); return context; }
