import { useCallback, useEffect, useState, type FormEvent } from 'react';
import { Clock, Pencil, Plus, Trash2 } from 'lucide-react';
import { api } from '@/services/api';
import { Button } from '@/components/ui/Button';
import { Dialog } from '@/components/ui/Dialog';
import { Input, Textarea } from '@/components/ui/Input';
import { Alerta } from '@/components/ui/Alerta';
import { errorDetail } from '@/components/turnos/errorDetail';
import type { Servicio } from '@/types';

const formatPrecio = (centavos: number) =>
  new Intl.NumberFormat('es-AR', { style: 'currency', currency: 'ARS' }).format(centavos / 100);

interface Form {
  nombre: string;
  descripcion: string;
  duracion_min: string;
  precio: string; // en pesos
  orden: string;
}

const FORM_VACIO: Form = { nombre: '', descripcion: '', duracion_min: '30', precio: '', orden: '0' };

function aForm(s: Servicio): Form {
  return {
    nombre: s.nombre,
    descripcion: s.descripcion ?? '',
    duracion_min: String(s.duracion_min),
    precio: String(s.precio / 100),
    orden: String(s.orden ?? 0),
  };
}

/** CU-02: servicios que ofrece el proveedor. */
export function ProfesionalServiciosPage() {
  const [servicios, setServicios] = useState<Servicio[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // null = cerrado; 'nuevo' = alta; Servicio = edición
  const [editando, setEditando] = useState<Servicio | 'nuevo' | null>(null);
  const [form, setForm] = useState<Form>(FORM_VACIO);
  const [formError, setFormError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [aDesactivar, setADesactivar] = useState<Servicio | null>(null);

  const cargar = useCallback(async () => {
    try {
      const data = await api.getMisServicios();
      setServicios([...data].sort((a, b) => (a.orden ?? 0) - (b.orden ?? 0) || a.nombre.localeCompare(b.nombre)));
      setError(null);
    } catch (err) {
      setError(errorDetail(err, 'No se pudieron cargar tus servicios'));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void cargar();
  }, [cargar]);

  const abrir = (s: Servicio | 'nuevo') => {
    setEditando(s);
    setForm(s === 'nuevo' ? FORM_VACIO : aForm(s));
    setFormError(null);
  };

  const guardar = async (e: FormEvent) => {
    e.preventDefault();
    const duracion = Number(form.duracion_min);
    const precio = Math.round(Number(form.precio.replace(',', '.')) * 100);
    if (!Number.isInteger(duracion) || duracion < 1 || duracion > 480) {
      setFormError('La duración debe ser entre 1 y 480 minutos');
      return;
    }
    if (!Number.isFinite(precio) || precio < 0) {
      setFormError('Ingresá un precio válido');
      return;
    }
    const datos = {
      nombre: form.nombre.trim(),
      descripcion: form.descripcion.trim() || undefined,
      duracion_min: duracion,
      precio,
      orden: Number(form.orden) || 0,
    };
    setSaving(true);
    setFormError(null);
    try {
      if (editando === 'nuevo') await api.crearServicio(datos);
      else if (editando) await api.actualizarServicio(editando.id, datos);
      setEditando(null);
      await cargar();
    } catch (err) {
      setFormError(errorDetail(err, 'No se pudo guardar el servicio'));
    } finally {
      setSaving(false);
    }
  };

  const desactivar = async () => {
    if (!aDesactivar) return;
    setSaving(true);
    try {
      await api.desactivarServicio(aDesactivar.id);
      setADesactivar(null);
      await cargar();
    } catch (err) {
      setError(errorDetail(err, 'No se pudo desactivar el servicio'));
      setADesactivar(null);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Servicios</h1>
          <p className="mt-1 text-gray-600 dark:text-gray-400">Lo que los clientes pueden reservar con vos</p>
        </div>
        <Button onClick={() => abrir('nuevo')}>
          <Plus className="h-4 w-4" /> Nuevo servicio
        </Button>
      </div>

      {error && <Alerta tipo="error">{error}</Alerta>}

      {loading ? (
        <p className="text-sm text-gray-500">Cargando…</p>
      ) : servicios.length === 0 ? (
        <p className="rounded-lg border border-dashed border-gray-300 p-8 text-center text-sm text-gray-500 dark:border-gray-700">
          Todavía no cargaste servicios. Sin servicios, los clientes no pueden reservar.
        </p>
      ) : (
        <ul className="space-y-3">
          {servicios.map((s) => (
            <li
              key={s.id}
              className="flex flex-wrap items-start gap-3 rounded-lg border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-900"
            >
              <div className="min-w-0 flex-1">
                <p className="font-medium text-gray-900 dark:text-white">{s.nombre}</p>
                {s.descripcion && <p className="text-sm text-gray-500 dark:text-gray-400">{s.descripcion}</p>}
                <p className="mt-1 flex items-center gap-3 text-sm text-gray-600 dark:text-gray-300">
                  <span className="flex items-center gap-1 whitespace-nowrap"><Clock className="h-4 w-4" /> {s.duracion_min} min</span>
                  <span className="whitespace-nowrap">{formatPrecio(s.precio)}</span>
                </p>
              </div>
              <div className="flex w-full justify-end gap-2 sm:w-auto">
                <Button variant="outline" size="sm" onClick={() => abrir(s)} aria-label={`Editar ${s.nombre}`}>
                  <Pencil className="h-4 w-4" /> Editar
                </Button>
                <Button variant="outline" size="sm" onClick={() => setADesactivar(s)} aria-label={`Desactivar ${s.nombre}`}>
                  <Trash2 className="h-4 w-4" /> Desactivar
                </Button>
              </div>
            </li>
          ))}
        </ul>
      )}

      <Dialog open={editando !== null} title={editando === 'nuevo' ? 'Nuevo servicio' : 'Editar servicio'} onClose={() => !saving && setEditando(null)}>
        <form onSubmit={guardar} className="space-y-4">
          <Input id="servicio-nombre" label="Nombre" value={form.nombre} onChange={(e) => setForm({ ...form, nombre: e.target.value })} required maxLength={100} />
          <Textarea id="servicio-descripcion" label="Descripción" value={form.descripcion} onChange={(e) => setForm({ ...form, descripcion: e.target.value })} rows={2} />
          <div className="grid grid-cols-2 gap-3">
            <Input id="servicio-duracion" label="Duración (min)" type="number" min={1} max={480} value={form.duracion_min} onChange={(e) => setForm({ ...form, duracion_min: e.target.value })} required />
            <Input id="servicio-precio" label="Precio ($)" type="number" min={0} step="0.01" value={form.precio} onChange={(e) => setForm({ ...form, precio: e.target.value })} required />
          </div>
          <Input id="servicio-orden" label="Orden en la lista" type="number" min={0} value={form.orden} onChange={(e) => setForm({ ...form, orden: e.target.value })} helperText="Los de menor número aparecen primero" />
          {formError && <Alerta tipo="error">{formError}</Alerta>}
          <div className="flex justify-end gap-2">
            <Button type="button" variant="outline" onClick={() => setEditando(null)} disabled={saving}>Volver</Button>
            <Button type="submit" loading={saving}>Guardar</Button>
          </div>
        </form>
      </Dialog>

      <Dialog open={aDesactivar !== null} title="Desactivar servicio" onClose={() => !saving && setADesactivar(null)}>
        <div className="space-y-4">
          <p className="text-sm text-gray-600 dark:text-gray-300">
            «{aDesactivar?.nombre}» deja de aparecer para reservar. Los turnos ya reservados no cambian.
          </p>
          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={() => setADesactivar(null)} disabled={saving}>Volver</Button>
            <Button variant="destructive" onClick={desactivar} loading={saving}>Desactivar</Button>
          </div>
        </div>
      </Dialog>
    </div>
  );
}
