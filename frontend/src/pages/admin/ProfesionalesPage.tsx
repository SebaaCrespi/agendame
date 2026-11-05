import { useCallback, useEffect, useState, type FormEvent } from 'react';
import { Pencil, Plus, Power, RotateCcw } from 'lucide-react';
import { api } from '@/services/api';
import { Button } from '@/components/ui/Button';
import { Dialog } from '@/components/ui/Dialog';
import { Input } from '@/components/ui/Input';
import { Paginacion } from '@/components/ui/Paginacion';
import { Alerta, inputClass } from '@/components/ui/Alerta';
import { errorDetail } from '@/components/turnos/errorDetail';
import { cn } from '@/utils/cn';
import type { Profesional } from '@/types';

const POR_PAGINA = 20;
const DURACIONES = [10, 15, 20, 30, 45, 60, 90, 120];

type FiltroActivo = 'activos' | 'inactivos' | 'todos';

interface Form {
  nombre: string;
  apellido: string;
  email: string;
  password: string;
  telefono: string;
  slot_duracion_min: number;
}

const FORM_VACIO: Form = { nombre: '', apellido: '', email: '', password: '', telefono: '', slot_duracion_min: 30 };

/** CU-10: alta, edición, baja y reactivación de profesionales. */
export function AdminProfesionalesPage() {
  const [filtro, setFiltro] = useState<FiltroActivo>('activos');
  const [busqueda, setBusqueda] = useState('');
  const [q, setQ] = useState('');
  const [page, setPage] = useState(1);

  const [items, setItems] = useState<Profesional[]>([]);
  const [pages, setPages] = useState(0);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [aviso, setAviso] = useState<string | null>(null);

  const [editando, setEditando] = useState<Profesional | 'nuevo' | null>(null);
  const [form, setForm] = useState<Form>(FORM_VACIO);
  const [formError, setFormError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [aDesactivar, setADesactivar] = useState<Profesional | null>(null);
  const [bajaError, setBajaError] = useState<string | null>(null);

  useEffect(() => {
    const t = setTimeout(() => {
      setQ(busqueda.trim());
      setPage(1);
    }, 300);
    return () => clearTimeout(t);
  }, [busqueda]);

  const cargar = useCallback(async () => {
    setLoading(true);
    try {
      const data = await api.getProfesionalesAdmin({
        page,
        size: POR_PAGINA,
        ...(q && { q }),
        ...(filtro !== 'todos' && { activo: filtro === 'activos' }),
      });
      setItems(data.items);
      setPages(data.pages);
      setTotal(data.total);
      setError(null);
    } catch (err) {
      setError(errorDetail(err, 'No se pudieron cargar los profesionales'));
    } finally {
      setLoading(false);
    }
  }, [page, q, filtro]);

  useEffect(() => {
    void cargar();
  }, [cargar]);

  const abrir = (p: Profesional | 'nuevo') => {
    setEditando(p);
    setFormError(null);
    setForm(
      p === 'nuevo'
        ? FORM_VACIO
        : { ...FORM_VACIO, nombre: p.nombre, apellido: p.apellido, email: p.email, telefono: p.telefono ?? '', slot_duracion_min: p.slot_duracion_min }
    );
  };

  const guardar = async (e: FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setFormError(null);
    const base = {
      nombre: form.nombre.trim(),
      apellido: form.apellido.trim(),
      slot_duracion_min: form.slot_duracion_min,
    };
    try {
      if (editando === 'nuevo') {
        await api.crearProfesionalAdmin({
          ...base,
          email: form.email.trim(),
          password: form.password,
          ...(form.telefono.trim() && { telefono: form.telefono.trim() }),
        });
        setAviso(`Se dio de alta a ${base.nombre} ${base.apellido}. Pasale su email y la contraseña temporal.`);
      } else if (editando) {
        await api.actualizarProfesionalAdmin(editando.id, { ...base, telefono: form.telefono.trim() || null });
        setAviso('Cambios guardados');
      }
      setEditando(null);
      await cargar();
    } catch (err) {
      setFormError(errorDetail(err, 'No se pudo guardar el profesional'));
    } finally {
      setSaving(false);
    }
  };

  const desactivar = async () => {
    if (!aDesactivar) return;
    setSaving(true);
    setBajaError(null);
    try {
      await api.desactivarProfesionalAdmin(aDesactivar.id);
      setAviso(`Se desactivó a ${aDesactivar.nombre} ${aDesactivar.apellido}`);
      setADesactivar(null);
      await cargar();
    } catch (err) {
      setBajaError(errorDetail(err, 'No se pudo desactivar'));
    } finally {
      setSaving(false);
    }
  };

  const reactivar = async (p: Profesional) => {
    setError(null);
    try {
      await api.actualizarProfesionalAdmin(p.id, { activo: true });
      setAviso(`Se reactivó a ${p.nombre} ${p.apellido}`);
      await cargar();
    } catch (err) {
      setError(errorDetail(err, 'No se pudo reactivar'));
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Profesionales</h1>
          <p className="mt-1 text-gray-600 dark:text-gray-400">Cada uno configura sus servicios y su agenda</p>
        </div>
        <Button onClick={() => abrir('nuevo')}>
          <Plus className="h-4 w-4" /> Nuevo profesional
        </Button>
      </div>

      <div className="grid gap-3 sm:grid-cols-[1fr_200px]">
        <input
          type="search"
          aria-label="Buscar por nombre"
          placeholder="Buscar por nombre…"
          value={busqueda}
          onChange={(e) => setBusqueda(e.target.value)}
          className={inputClass}
        />
        <select
          aria-label="Estado"
          value={filtro}
          onChange={(e) => {
            setFiltro(e.target.value as FiltroActivo);
            setPage(1);
          }}
          className={inputClass}
        >
          <option value="activos">Activos</option>
          <option value="inactivos">Inactivos</option>
          <option value="todos">Todos</option>
        </select>
      </div>

      {error && <Alerta tipo="error">{error}</Alerta>}
      {aviso && <Alerta tipo="ok">{aviso}</Alerta>}

      <div className={cn('transition-opacity', loading && 'opacity-50')}>
        <p className="mb-2 text-sm text-gray-500 dark:text-gray-400">{total} {total === 1 ? 'profesional' : 'profesionales'}</p>
        {!loading && items.length === 0 ? (
          <p className="rounded-lg border border-dashed border-gray-300 p-8 text-center text-sm text-gray-500 dark:border-gray-700">
            No hay profesionales con estos filtros.
          </p>
        ) : (
          <ul className="divide-y divide-gray-200 overflow-hidden rounded-lg border border-gray-200 bg-white dark:divide-gray-700 dark:border-gray-700 dark:bg-gray-900">
            {items.map((p) => (
              <li key={p.id} className="flex flex-wrap items-center gap-x-4 gap-y-2 px-4 py-3">
                <div className="min-w-0 flex-1">
                  <p className="flex items-center gap-2 font-medium text-gray-900 dark:text-white">
                    {p.nombre} {p.apellido}
                    {!p.activo && (
                      <span className="rounded border border-gray-300 px-2 py-0.5 text-xs font-medium text-gray-500 dark:border-gray-600">Inactivo</span>
                    )}
                  </p>
                  <p className="truncate text-sm text-gray-500 dark:text-gray-400">
                    {p.email}{p.telefono && ` · ${p.telefono}`} · turnos de {p.slot_duracion_min} min
                  </p>
                </div>
                <div className="flex w-full justify-end gap-2 sm:w-auto">
                  <Button variant="outline" size="sm" onClick={() => abrir(p)} aria-label={`Editar ${p.nombre} ${p.apellido}`}>
                    <Pencil className="h-4 w-4" /> Editar
                  </Button>
                  {p.activo ? (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        setBajaError(null);
                        setADesactivar(p);
                      }}
                      aria-label={`Desactivar ${p.nombre} ${p.apellido}`}
                    >
                      <Power className="h-4 w-4" /> Desactivar
                    </Button>
                  ) : (
                    <Button variant="outline" size="sm" onClick={() => reactivar(p)} aria-label={`Reactivar ${p.nombre} ${p.apellido}`}>
                      <RotateCcw className="h-4 w-4" /> Reactivar
                    </Button>
                  )}
                </div>
              </li>
            ))}
          </ul>
        )}
        <Paginacion page={page} pages={pages} onChange={setPage} />
      </div>

      <Dialog open={editando !== null} title={editando === 'nuevo' ? 'Nuevo profesional' : 'Editar profesional'} onClose={() => !saving && setEditando(null)}>
        <form onSubmit={guardar} className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <Input id="prof-nombre" label="Nombre" value={form.nombre} onChange={(e) => setForm({ ...form, nombre: e.target.value })} required maxLength={100} />
            <Input id="prof-apellido" label="Apellido" value={form.apellido} onChange={(e) => setForm({ ...form, apellido: e.target.value })} required maxLength={100} />
          </div>
          {editando === 'nuevo' ? (
            <>
              <Input id="prof-email" label="Email" type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} required autoComplete="off" />
              <Input
                id="prof-password"
                label="Contraseña temporal"
                type="text"
                value={form.password}
                onChange={(e) => setForm({ ...form, password: e.target.value })}
                required
                minLength={8}
                maxLength={128}
                autoComplete="new-password"
                helperText="Mínimo 8 caracteres. El profesional la puede cambiar después."
              />
            </>
          ) : (
            <p className="text-sm text-gray-500 dark:text-gray-400">Email: {form.email}</p>
          )}
          <Input id="prof-telefono" label="Teléfono" type="tel" value={form.telefono} onChange={(e) => setForm({ ...form, telefono: e.target.value })} maxLength={20} />
          <div>
            <label htmlFor="prof-slot" className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">Duración base del turno</label>
            <select id="prof-slot" value={form.slot_duracion_min} onChange={(e) => setForm({ ...form, slot_duracion_min: Number(e.target.value) })} className={`${inputClass} w-full`}>
              {DURACIONES.map((m) => (
                <option key={m} value={m}>{m} minutos</option>
              ))}
            </select>
          </div>
          {formError && <Alerta tipo="error">{formError}</Alerta>}
          <div className="flex justify-end gap-2">
            <Button type="button" variant="outline" onClick={() => setEditando(null)} disabled={saving}>Volver</Button>
            <Button type="submit" loading={saving}>Guardar</Button>
          </div>
        </form>
      </Dialog>

      <Dialog open={aDesactivar !== null} title="Desactivar profesional" onClose={() => !saving && setADesactivar(null)}>
        <div className="space-y-4">
          <p className="text-sm text-gray-600 dark:text-gray-300">
            {aDesactivar?.nombre} {aDesactivar?.apellido} deja de aparecer para reservar. Se puede reactivar después.
          </p>
          {bajaError && <Alerta tipo="error">{bajaError}</Alerta>}
          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={() => setADesactivar(null)} disabled={saving}>Volver</Button>
            <Button variant="destructive" onClick={desactivar} loading={saving}>Desactivar</Button>
          </div>
        </div>
      </Dialog>
    </div>
  );
}
