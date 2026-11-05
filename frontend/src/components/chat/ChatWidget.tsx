import { useEffect, useRef, useState, type FormEvent } from 'react';
import { MessageCircle, Send, X } from 'lucide-react';
import { api } from '@/services/api';
import { errorDetail } from '@/components/turnos/errorDetail';
import { cn } from '@/utils/cn';

interface Mensaje {
  de: 'usuario' | 'asistente' | 'error';
  texto: string;
}

interface ChatWidgetProps {
  /** Se llama cuando el asistente reservó o canceló un turno. */
  onCambioTurnos?: () => void;
}

const CLAVE_SESION = 'agendame_chat_session';
const BIENVENIDA: Mensaje = {
  de: 'asistente',
  texto: '¡Hola! Te ayudo a buscar horarios y reservar. Por ejemplo: «¿Qué horarios tiene Juan mañana para un corte?»',
};

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

/** Asistente de turnos (CU-05/06): botón flotante con la conversación. */
export function ChatWidget({ onCambioTurnos }: ChatWidgetProps) {
  const [abierto, setAbierto] = useState(false);
  const [mensajes, setMensajes] = useState<Mensaje[]>([BIENVENIDA]);
  const [texto, setTexto] = useState('');
  const [enviando, setEnviando] = useState(false);
  const finRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    finRef.current?.scrollIntoView({ block: 'end' });
  }, [mensajes, enviando]);

  useEffect(() => {
    if (abierto) inputRef.current?.focus();
  }, [abierto]);

  const enviar = async (e: FormEvent) => {
    e.preventDefault();
    const mensaje = texto.trim();
    if (!mensaje || enviando) return;
    setTexto('');
    setMensajes((m) => [...m, { de: 'usuario', texto: mensaje }]);
    setEnviando(true);
    try {
      const r = await api.enviarMensajeChat(mensaje, leerSesion());
      guardarSesion(r.session_id);
      setMensajes((m) => [...m, { de: 'asistente', texto: r.respuesta }]);
      if (r.acciones.length > 0) onCambioTurnos?.();
    } catch (err) {
      setMensajes((m) => [...m, { de: 'error', texto: errorDetail(err, 'No pude responder. Probá de nuevo en un momento.') }]);
    } finally {
      setEnviando(false);
      inputRef.current?.focus();
    }
  };

  return (
    <>
      {abierto && (
        <section
          aria-label="Asistente de turnos"
          className="fixed bottom-20 left-4 right-4 z-40 flex max-h-[70vh] flex-col overflow-hidden rounded-xl border border-gray-200 bg-white shadow-2xl sm:left-auto sm:w-96 dark:border-gray-700 dark:bg-gray-900"
        >
          <header className="flex items-center justify-between border-b border-gray-200 px-4 py-3 dark:border-gray-700">
            <div>
              <p className="font-semibold text-gray-900 dark:text-white">Asistente Agendame</p>
              <p className="text-xs text-gray-500 dark:text-gray-400">Consultá horarios y reservá conversando</p>
            </div>
            <button type="button" onClick={() => setAbierto(false)} aria-label="Cerrar asistente" className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200">
              <X className="h-5 w-5" />
            </button>
          </header>

          <div className="flex-1 space-y-3 overflow-y-auto px-4 py-3" aria-live="polite">
            {mensajes.map((m, i) => (
              <div
                key={i}
                className={cn(
                  'max-w-[85%] whitespace-pre-wrap rounded-lg px-3 py-2 text-sm',
                  m.de === 'usuario' && 'ml-auto bg-indigo-600 text-white',
                  m.de === 'asistente' && 'bg-gray-100 text-gray-900 dark:bg-gray-800 dark:text-gray-100',
                  m.de === 'error' && 'bg-red-50 text-red-700 dark:bg-red-900/30 dark:text-red-300'
                )}
              >
                {m.texto}
              </div>
            ))}
            {enviando && (
              <div className="w-fit rounded-lg bg-gray-100 px-3 py-2 text-sm text-gray-500 dark:bg-gray-800 dark:text-gray-400">
                Escribiendo…
              </div>
            )}
            <div ref={finRef} />
          </div>

          <form onSubmit={enviar} className="flex gap-2 border-t border-gray-200 p-3 dark:border-gray-700">
            <input
              ref={inputRef}
              type="text"
              aria-label="Mensaje para el asistente"
              placeholder="Escribí tu consulta…"
              maxLength={1000}
              value={texto}
              onChange={(e) => setTexto(e.target.value)}
              className="min-w-0 flex-1 rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-indigo-500 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100"
            />
            <button
              type="submit"
              disabled={enviando || !texto.trim()}
              aria-label="Enviar"
              className="rounded-lg bg-indigo-600 px-3 text-white hover:bg-indigo-700 disabled:opacity-50"
            >
              <Send className="h-4 w-4" />
            </button>
          </form>
        </section>
      )}

      <button
        type="button"
        onClick={() => setAbierto((a) => !a)}
        aria-label={abierto ? 'Cerrar asistente' : 'Abrir asistente'}
        aria-expanded={abierto}
        className="fixed bottom-4 right-4 z-40 flex h-14 w-14 items-center justify-center rounded-full bg-indigo-600 text-white shadow-lg hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
      >
        {abierto ? <X className="h-6 w-6" /> : <MessageCircle className="h-6 w-6" />}
      </button>
    </>
  );
}
