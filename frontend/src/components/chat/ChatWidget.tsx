import { useEffect, useRef, useState, type FormEvent } from 'react';
import { ArrowUp, MessageCircle, Sparkles, X } from 'lucide-react';
import { api } from '@/services/api';
import { errorDetail } from '@/components/turnos/errorDetail';
import { EVENTO_TURNOS_CAMBIARON } from '@/components/turnos/estado';
import { cn } from '@/utils/cn';
import { MensajeMarkdown } from './MensajeMarkdown';

interface Mensaje {
  de: 'usuario' | 'asistente' | 'error';
  texto: string;
}

const CLAVE_SESION = 'agendame_chat_session';
/** Otras pantallas pueden abrir el asistente con este evento. */
export const EVENTO_ABRIR_ASISTENTE = 'agendame:abrir-asistente';

const BIENVENIDA: Mensaje = {
  de: 'asistente',
  texto: '¡Hola! Te ayudo a buscar horarios, reservar o cancelar turnos. ¿Qué necesitás?',
};

const SUGERENCIAS = ['¿Qué profesionales hay?', '¿Qué horarios hay mañana?', '¿Cuáles son mis próximos turnos?'];

function leerSesion(): string | null {
  try {
    return sessionStorage.getItem(CLAVE_SESION);
  } catch {
    return null;
  }
}

function guardarSesion(id: string) {
  try {
    sessionStorage.setItem(CLAVE_SESION, id);
  } catch {
    // sin storage: la conversación no sobrevive a la recarga, nada más
  }
}

/** Asistente de turnos (CU-05/06): burbuja flotante abajo a la derecha que abre el chat. */
export function ChatWidget() {
  const [abierto, setAbierto] = useState(false);
  const [mensajes, setMensajes] = useState<Mensaje[]>([BIENVENIDA]);
  const [texto, setTexto] = useState('');
  const [enviando, setEnviando] = useState(false);
  const finRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    finRef.current?.scrollIntoView({ block: 'end' });
  }, [mensajes, enviando, abierto]);

  useEffect(() => {
    if (abierto) inputRef.current?.focus();
  }, [abierto]);

  useEffect(() => {
    const abrir = () => setAbierto(true);
    window.addEventListener(EVENTO_ABRIR_ASISTENTE, abrir);
    return () => window.removeEventListener(EVENTO_ABRIR_ASISTENTE, abrir);
  }, []);

  useEffect(() => {
    if (!abierto) return;
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && setAbierto(false);
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [abierto]);

  const mandar = async (mensaje: string) => {
    if (!mensaje || enviando) return;
    setTexto('');
    setMensajes((m) => [...m, { de: 'usuario', texto: mensaje }]);
    setEnviando(true);
    try {
      const r = await api.enviarMensajeChat(mensaje, leerSesion());
      guardarSesion(r.session_id);
      setMensajes((m) => [...m, { de: 'asistente', texto: r.respuesta }]);
      if (r.acciones.length > 0) window.dispatchEvent(new Event(EVENTO_TURNOS_CAMBIARON));
    } catch (err) {
      setMensajes((m) => [...m, { de: 'error', texto: errorDetail(err, 'No pude responder. Probá de nuevo en un momento.') }]);
    } finally {
      setEnviando(false);
      inputRef.current?.focus();
    }
  };

  const enviar = (e: FormEvent) => {
    e.preventDefault();
    void mandar(texto.trim());
  };

  return (
    <>
      {abierto && (
        <section
          aria-label="Asistente de turnos"
          className={cn(
            'fixed z-40 flex flex-col overflow-hidden border border-line bg-surface shadow-pop',
            // Mobile: casi pantalla completa, por encima de la barra inferior
            'inset-x-2 bottom-[5.5rem] top-16 rounded-2xl',
            'md:inset-auto md:bottom-24 md:right-6 md:h-[min(600px,calc(100vh-8rem))] md:w-[380px]'
          )}
        >
          <header className="flex items-center gap-3 border-b border-line px-4 py-3">
            <span className="flex size-9 items-center justify-center rounded-full bg-primary-soft text-primary">
              <Sparkles className="size-4" aria-hidden="true" />
            </span>
            <div className="min-w-0 flex-1">
              <p className="text-sm font-semibold text-fg">Asistente Agendame</p>
              <p className="flex items-center gap-1.5 text-xs text-muted">
                <span className="size-1.5 rounded-full bg-success" aria-hidden="true" /> Disponible
              </p>
            </div>
            <button
              type="button"
              onClick={() => setAbierto(false)}
              aria-label="Cerrar asistente"
              className="rounded-md p-1.5 text-subtle transition-colors hover:bg-surface-2 hover:text-fg"
            >
              <X className="size-4" />
            </button>
          </header>

          <div className="flex-1 space-y-3 overflow-y-auto bg-canvas px-4 py-4" aria-live="polite">
            {mensajes.map((m, i) => (
              <div
                key={i}
                className={cn(
                  'max-w-[85%] rounded-2xl px-3.5 py-2.5 text-sm leading-relaxed',
                  m.de === 'usuario' && 'ml-auto whitespace-pre-wrap rounded-br-md bg-primary text-on-primary',
                  m.de === 'asistente' && 'rounded-bl-md border border-line bg-surface text-fg',
                  m.de === 'error' && 'rounded-bl-md bg-danger-soft text-danger'
                )}
              >
                {m.de === 'asistente' ? <MensajeMarkdown texto={m.texto} /> : m.texto}
              </div>
            ))}
            {enviando && (
              <div className="flex w-fit gap-1 rounded-2xl rounded-bl-md border border-line bg-surface px-4 py-3" aria-label="Escribiendo">
                {[0, 150, 300].map((d) => (
                  <span key={d} className="size-1.5 animate-bounce rounded-full bg-subtle" style={{ animationDelay: `${d}ms` }} />
                ))}
              </div>
            )}
            {mensajes.length === 1 && !enviando && (
              <div className="flex flex-wrap gap-2 pt-1">
                {SUGERENCIAS.map((s) => (
                  <button
                    key={s}
                    type="button"
                    onClick={() => void mandar(s)}
                    className="rounded-full border border-line bg-surface px-3 py-1.5 text-[13px] text-fg transition-colors hover:border-primary hover:text-primary"
                  >
                    {s}
                  </button>
                ))}
              </div>
            )}
            <div ref={finRef} />
          </div>

          <form onSubmit={enviar} className="flex items-center gap-2 border-t border-line bg-surface p-3">
            <input
              ref={inputRef}
              type="text"
              aria-label="Mensaje para el asistente"
              placeholder="Escribí tu consulta…"
              maxLength={1000}
              value={texto}
              onChange={(e) => setTexto(e.target.value)}
              className="h-10 min-w-0 flex-1 rounded-full border border-line bg-canvas px-4 text-sm text-fg placeholder:text-subtle focus:border-primary focus:outline-none focus:ring-4 focus:ring-ring"
            />
            <button
              type="submit"
              disabled={enviando || !texto.trim()}
              aria-label="Enviar"
              className="flex size-10 shrink-0 items-center justify-center rounded-full bg-primary text-on-primary transition-colors hover:bg-primary-hover disabled:opacity-40"
            >
              <ArrowUp className="size-4" />
            </button>
          </form>
        </section>
      )}

      <button
        type="button"
        onClick={() => setAbierto((a) => !a)}
        aria-label={abierto ? 'Cerrar asistente' : 'Abrir asistente'}
        aria-expanded={abierto}
        className={cn(
          'fixed bottom-[5.5rem] right-4 z-40 flex size-14 items-center justify-center rounded-full bg-primary text-on-primary shadow-pop transition-transform hover:scale-105 hover:bg-primary-hover focus-visible:ring-4 focus-visible:ring-ring md:bottom-6 md:right-6',
          abierto && 'max-md:hidden'
        )}
      >
        {abierto ? <X className="size-6" /> : <MessageCircle className="size-6" />}
      </button>
    </>
  );
}
