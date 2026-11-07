import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from 'react';

export type PreferenciaTema = 'light' | 'dark' | 'system';

const CLAVE = 'agendame_tema';

interface ThemeContextType {
  preferencia: PreferenciaTema;
  /** Tema efectivo en pantalla. */
  tema: 'light' | 'dark';
  setPreferencia: (p: PreferenciaTema) => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

function leerPreferencia(): PreferenciaTema {
  try {
    const v = localStorage.getItem(CLAVE);
    if (v === 'light' || v === 'dark' || v === 'system') return v;
  } catch {
    // sin storage: se usa el del sistema
  }
  return 'system';
}

const mediaOscuro = () => window.matchMedia('(prefers-color-scheme: dark)');

function resolver(p: PreferenciaTema): 'light' | 'dark' {
  if (p === 'system') return mediaOscuro().matches ? 'dark' : 'light';
  return p;
}

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [preferencia, setPref] = useState<PreferenciaTema>(leerPreferencia);
  const [tema, setTema] = useState<'light' | 'dark'>(() => resolver(leerPreferencia()));

  useEffect(() => {
    const aplicar = () => {
      const t = resolver(preferencia);
      setTema(t);
      document.documentElement.dataset.theme = t;
    };
    aplicar();
    if (preferencia !== 'system') return;
    const mq = mediaOscuro();
    mq.addEventListener('change', aplicar);
    return () => mq.removeEventListener('change', aplicar);
  }, [preferencia]);

  const setPreferencia = useCallback((p: PreferenciaTema) => {
    setPref(p);
    try {
      localStorage.setItem(CLAVE, p);
    } catch {
      // no se recuerda entre visitas, nada más
    }
  }, []);

  return <ThemeContext.Provider value={{ preferencia, tema, setPreferencia }}>{children}</ThemeContext.Provider>;
}

export function useTheme() {
  const ctx = useContext(ThemeContext);
  if (!ctx) throw new Error('useTheme debe usarse dentro de ThemeProvider');
  return ctx;
}
