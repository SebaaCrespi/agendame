import { Monitor, Moon, Sun } from 'lucide-react';
import { useTheme, type PreferenciaTema } from '@/contexts/ThemeContext';
import { cn } from '@/utils/cn';

const OPCIONES: { value: PreferenciaTema; label: string; icon: typeof Sun }[] = [
  { value: 'light', label: 'Claro', icon: Sun },
  { value: 'dark', label: 'Oscuro', icon: Moon },
  { value: 'system', label: 'Sistema', icon: Monitor },
];

/** Selector de tema claro / oscuro / sistema. */
export function ThemeToggle({ className }: { className?: string }) {
  const { preferencia, setPreferencia } = useTheme();
  return (
    <div role="radiogroup" aria-label="Tema" className={cn('inline-flex rounded-lg bg-surface-2 p-0.5', className)}>
      {OPCIONES.map(({ value, label, icon: Icon }) => (
        <button
          key={value}
          type="button"
          role="radio"
          aria-checked={preferencia === value}
          aria-label={label}
          title={label}
          onClick={() => setPreferencia(value)}
          className={cn(
            'flex h-7 flex-1 items-center justify-center rounded-md px-2 transition-colors',
            preferencia === value ? 'bg-surface text-fg shadow-sm' : 'text-subtle hover:text-fg'
          )}
        >
          <Icon className="size-3.5" aria-hidden="true" />
        </button>
      ))}
    </div>
  );
}

/** Botón único que alterna claro/oscuro (para la landing y el login). */
export function ThemeSwitch({ className }: { className?: string }) {
  const { tema, setPreferencia } = useTheme();
  const Icon = tema === 'dark' ? Sun : Moon;
  return (
    <button
      type="button"
      onClick={() => setPreferencia(tema === 'dark' ? 'light' : 'dark')}
      aria-label={tema === 'dark' ? 'Usar tema claro' : 'Usar tema oscuro'}
      className={cn('flex size-9 items-center justify-center rounded-lg text-muted transition-colors hover:bg-surface-2 hover:text-fg', className)}
    >
      <Icon className="size-4" aria-hidden="true" />
    </button>
  );
}
