import { useCallback, useEffect, useState, type FormEvent } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Pencil, Plus, Power, RotateCcw, Search, Users } from 'lucide-react';
import { api } from '@/services/api';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Dialog } from '@/components/ui/Dialog';
import { Input, Select } from '@/components/ui/Input';
import { Paginacion } from '@/components/ui/Paginacion';
import { Alerta } from '@/components/ui/Alerta';
import { Avatar, EmptyState, PageHeader, Segmented, Spinner } from '@/components/ui/misc';
import { Badge } from '@/components/turnos/EstadoBadge';
import { errorDetail } from '@/components/turnos/errorDetail';
import { cn } from '@/utils/cn';
import { plural } from '@/utils/formato';
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
  const [params, setParams] = useSearchParams();
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

  const abrir = useCallback((p: Profesional | 'nuevo') => {
    setEditando(p);
    setFormError(null);
    setForm(
      p === 'nuevo'
        ? FORM_VACIO
        : { ...FORM_VACIO, nombre: p.nombre, apellido: p.apellido, email: p.email, telefono: p.telefono ?? '', slot_duracion_min: p.slot_duracion_min }
    );
  }, []);

  // "Nuevo profesional" desde el resumen abre el alta directamente
  useEffect(() => {
    if (params.get('nuevo')) {
      abrir('nuevo');
      setParams({}, { replace: true });
    }
  }, [params, setParams, abrir]);

  const guardar = async (e: FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setFormError(null);
    const base = { nombre: form.nombre.trim(), apellido: form.apellido.trim(), slot_duracion_min: form.slot_duracion_min };
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
    <>
      <PageHeader
        title="Profesionales"
        description="Cada profesional configura sus servicios y su agenda."
        actions={
          <Button onClick={() => abrir('nuevo')}>
            <Plus /> Nuevo profesional
          </Button>
        }
      />

      <div className="mb-4 flex flex-wrap items-center gap-3">
        <Segmented
          label="Estado"
          value={filtro}
          onChange={(v) => {
            setFiltro(v);
            setPage(1);
          }}
          options={[
            { value: 'activos', label: 'Activos' },
            { value: 'inactivos', label: 'Inactivos' },
            { value: 'todos', label: 'Todos' },
          ]}
        />
        <Input type="search" aria-label="Buscar por nombre" placeholder="Buscar por nombre…" leftIcon={<Search />} value={busqueda} onChange={(e) => setBusqueda(e.target.value)} wrapperClassName="sm:ml-auto sm:w-72" />
      </div>

      {error && <Alerta tipo="error" className="mb-4">{error}</Alerta>}
      {aviso && <Alerta tipo="ok" className="mb-4">{aviso}</Alerta>}

      <Card padding="none" className="overflow-hidden">
        {loading && items.length === 0 ? (
          <Spinner />
        ) : items.length === 0 ? (
          <EmptyState icon={Users} title="Sin profesionales" description="No hay profesionales con estos filtros." />
        ) : (
          <div className={cn('transition-opacity', loading && 'opacity-50')}>
            <p className="border-b border-line px-5 py-3 text-[13px] text-muted">{plural(total, 'profesional', 'profesionales')}</p>
            <div className="overflow-x-auto">
              <table className="w-full min-w-[640px] text-left text-sm">
                <thead className="bg-surface-2 text-xs text-muted">
                  <tr>
                    <th className="px-5 py-2.5 font-medium">Profesional</th>
                    <th className="px-5 py-2.5 font-medium">Contacto</th>
                    <th className="px-5 py-2.5 font-medium">Turno base</th>
                    <th className="px-5 py-2.5 font-medium">Estado</th>
                    <th className="px-5 py-2.5"><span className="sr-only">Acciones</span></th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-line">
                  {items.map((p) => (
                    <tr key={p.id} className="transition-colors hover:bg-surface-2/60">
                      <td className="px-5 py-3">
                        <div className="flex items-center gap-3">
                          <Avatar nombre={`${p.nombre} ${p.apellido}`} src={p.foto_url} size="sm" />
                          <span className="whitespace-nowrap font-medium text-fg">{p.nombre} {p.apellido}</span>
                        </div>
                      </td>
                      <td className="px-5 py-3 text-muted">
                        <span className="block">{p.email}</span>
                        {p.telefono && <span className="block text-xs">{p.telefono}</span>}
                      </td>
                      <td className="whitespace-nowrap px-5 py-3 text-muted tabular">{p.slot_duracion_min} min</td>
                      <td className="px-5 py-3">
                        {p.activo ? <Badge className="bg-success-soft text-success">Activo</Badge> : <Badge className="bg-surface-2 text-muted">Inactivo</Badge>}
                      </td>
                      <td className="px-5 py-3">
                        <div className="flex justify-end gap-1">
                          <Button variant="ghost" size="sm" onClick={() => abrir(p)} aria-label={`Editar ${p.nombre} ${p.apellido}`}>
                            <Pencil /> Editar
                          </Button>
                          {p.activo ? (
                            <Button
                              variant="ghost"
                              size="sm"
                              className="hover:text-danger"
                              onClick={() => {
                                setBajaError(null);
                                setADesactivar(p);
                              }}
                              aria-label={`Desactivar ${p.nombre} ${p.apellido}`}
                            >
                              <Power /> Desactivar
                            </Button>
                          ) : (
                            <Button variant="ghost" size="sm" onClick={() => reactivar(p)} aria-label={`Reactivar ${p.nombre} ${p.apellido}`}>
                              <RotateCcw /> Reactivar
                            </Button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <Paginacion page={page} pages={pages} onChange={setPage} />
          </div>
        )}
      </Card>

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
            <p className="rounded-lg bg-surface-2 px-3 py-2.5 text-[13px] text-muted">Email: {form.email}</p>
          )}
          <Input id="prof-telefono" label="Teléfono" type="tel" value={form.telefono} onChange={(e) => setForm({ ...form, telefono: e.target.value })} maxLength={20} />
          <Select id="prof-slot" label="Duración base del turno" value={form.slot_duracion_min} onChange={(e) => setForm({ ...form, slot_duracion_min: Number(e.target.value) })}>
            {DURACIONES.map((m) => (
              <option key={m} value={m}>{m} minutos</option>
            ))}
          </Select>
          {formError && <Alerta tipo="error">{formError}</Alerta>}
          <div className="flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
            <Button variant="outline" onClick={() => setEditando(null)} disabled={saving}>Volver</Button>
            <Button type="submit" loading={saving}>Guardar</Button>
          </div>
        </form>
      </Dialog>

      <Dialog
        open={aDesactivar !== null}
        title="Desactivar profesional"
        description={`${aDesactivar?.nombre ?? ''} ${aDesactivar?.apellido ?? ''} deja de aparecer para reservar. Se puede reactivar después.`}
        onClose={() => !saving && setADesactivar(null)}
      >
        <div className="space-y-4">
          {bajaError && <Alerta tipo="error">{bajaError}</Alerta>}
          <div className="flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
            <Button variant="outline" onClick={() => setADesactivar(null)} disabled={saving}>Volver</Button>
            <Button variant="destructive" onClick={desactivar} loading={saving}>Desactivar</Button>
          </div>
        </div>
      </Dialog>
    </>
  );
}
