import { useEffect, useId, useRef, type ReactNode } from 'react';
import { createPortal } from 'react-dom';
import { X } from 'lucide-react';

interface DialogProps {
  open: boolean;
  title: string;
  description?: string;
  onClose: () => void;
  children: ReactNode;
}

/**
 * Diálogo modal: cierra con Escape, con el botón o tocando fuera, y pone el
 * foco en el primer campo al abrirse. Se renderiza en un portal sobre <body>.
 */
export function Dialog({ open, title, description, onClose, children }: DialogProps) {
  const panelRef = useRef<HTMLDivElement>(null);
  const titleId = useId();
  // Ref para no re-ejecutar el efecto (y robar el foco) cuando cambia onClose
  const onCloseRef = useRef(onClose);
  useEffect(() => {
    onCloseRef.current = onClose;
  }, [onClose]);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onCloseRef.current();
    };
    document.addEventListener('keydown', onKey);
    const primero = panelRef.current?.querySelector<HTMLElement>(
      'input, textarea, select, button:not([data-dialog-close])'
    );
    primero?.focus();
    const overflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => {
      document.removeEventListener('keydown', onKey);
      document.body.style.overflow = overflow;
    };
  }, [open]);

  if (!open) return null;

  return createPortal(
    <div
      className="fixed inset-0 z-[60] flex items-end justify-center bg-slate-950/50 p-0 backdrop-blur-[2px] sm:items-center sm:p-4"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div
        ref={panelRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        className="max-h-[92vh] w-full overflow-y-auto rounded-t-2xl border border-line bg-surface p-5 text-fg shadow-pop sm:max-w-md sm:rounded-xl sm:p-6"
      >
        <div className="mb-5 flex items-start justify-between gap-3">
          <div>
            <h2 id={titleId} className="text-base font-semibold">{title}</h2>
            {description && <p className="mt-1 text-[13px] text-muted">{description}</p>}
          </div>
          <button
            type="button"
            data-dialog-close
            onClick={onClose}
            aria-label="Cerrar"
            className="-m-1.5 rounded-md p-1.5 text-subtle transition-colors hover:bg-surface-2 hover:text-fg"
          >
            <X className="size-4" />
          </button>
        </div>
        {children}
      </div>
    </div>,
    document.body
  );
}
