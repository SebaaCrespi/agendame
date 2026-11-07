import { useEffect, useState, type FormEvent } from 'react';
import { api } from '@/services/api';
import { Button } from '@/components/ui/Button';
import { Card, CardDescription, CardTitle } from '@/components/ui/Card';
import { Input, Select, Textarea } from '@/components/ui/Input';
import { Alerta } from '@/components/ui/Alerta';
import { Avatar, Spinner } from '@/components/ui/misc';
import { errorDetail } from '@/components/turnos/errorDetail';
import type { Profesional, ProfesionalUpdate } from '@/types';

const DURACIONES = [10, 15, 20, 30, 45, 60, 90, 120];

interface Form {
  nombre: string;
  apellido: string;
  telefono: string;
  bio: string;
  foto_url: string;
  slot_duracion_min: number;
}

function aForm(p: Profesional): Form {
  return {
    nombre: p.nombre,
    apellido: p.apellido,
    telefono: p.telefono ?? '',
    bio: p.bio ?? '',
    foto_url: p.foto_url ?? '',
    slot_duracion_min: p.slot_duracion_min,
  };
}

/** CU-02: datos del proveedor y duración base de sus turnos. */
export function ProfesionalPerfilPage() {
  const [perfil, setPerfil] = useState<Profesional | null>(null);
  const [form, setForm] = useState<Form | null>(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [ok, setOk] = useState<string | null>(null);

  useEffect(() => {
    api
      .getMiPerfil()
      .then(({ profesional }) => {
        setPerfil(profesional);
        setForm(aForm(profesional));
      })
      .catch((err) => setError(errorDetail(err, 'No se pudo cargar tu perfil')));
  }, []);

  if (!form || !perfil) {
    return error ? <Alerta tipo="error">{error}</Alerta> : <Spinner />;
  }

  const set = <K extends keyof Form>(campo: K, valor: Form[K]) => {
    setForm({ ...form, [campo]: valor });
    setOk(null);
  };

  const original = aForm(perfil);
  const cambios: ProfesionalUpdate = {};
  if (form.nombre.trim() !== original.nombre) cambios.nombre = form.nombre.trim();
  if (form.apellido.trim() !== original.apellido) cambios.apellido = form.apellido.trim();
  if (form.telefono.trim() !== original.telefono) cambios.telefono = form.telefono.trim() || null;
  if (form.bio !== original.bio) cambios.bio = form.bio;
  if (form.foto_url.trim() !== original.foto_url) cambios.foto_url = form.foto_url.trim();
  if (form.slot_duracion_min !== original.slot_duracion_min) cambios.slot_duracion_min = form.slot_duracion_min;
  const hayCambios = Object.keys(cambios).length > 0;

  const guardar = async (e: FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      const actualizado = await api.updateMiPerfil(cambios);
      setPerfil(actualizado);
      setForm(aForm(actualizado));
      setOk('Perfil guardado');
    } catch (err) {
      setError(errorDetail(err, 'No se pudo guardar el perfil'));
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="grid max-w-5xl items-start gap-6 lg:grid-cols-[1fr_300px]">
      <Card padding="none">
        <div className="border-b border-line px-5 py-4">
          <CardTitle>Datos</CardTitle>
          <CardDescription>Email de acceso: {perfil.email}</CardDescription>
        </div>
        <form onSubmit={guardar} className="space-y-4 p-5">
          <div className="grid gap-4 sm:grid-cols-2">
            <Input id="perfil-nombre" label="Nombre" value={form.nombre} onChange={(e) => set('nombre', e.target.value)} required maxLength={100} />
            <Input id="perfil-apellido" label="Apellido" value={form.apellido} onChange={(e) => set('apellido', e.target.value)} required maxLength={100} />
          </div>
          <Input id="perfil-telefono" label="Teléfono" type="tel" value={form.telefono} onChange={(e) => set('telefono', e.target.value)} maxLength={20} />
          <Textarea id="perfil-bio" label="Sobre vos" placeholder="Especialidad, experiencia, lo que quieras contar" value={form.bio} onChange={(e) => set('bio', e.target.value)} rows={3} />
          <Input id="perfil-foto" label="Foto (URL)" type="url" value={form.foto_url} onChange={(e) => set('foto_url', e.target.value)} maxLength={500} placeholder="https://…" />
          <Select
            id="perfil-slot"
            label="Duración base del turno"
            value={form.slot_duracion_min}
            onChange={(e) => set('slot_duracion_min', Number(e.target.value))}
            helperText="Cada cuánto empiezan los horarios que ven los clientes. Los turnos ya reservados no cambian."
          >
            {DURACIONES.map((m) => (
              <option key={m} value={m}>{m} minutos</option>
            ))}
          </Select>

          {error && <Alerta tipo="error">{error}</Alerta>}
          {ok && <Alerta tipo="ok">{ok}</Alerta>}

          <div className="flex justify-end">
            <Button type="submit" loading={saving} disabled={!hayCambios}>Guardar cambios</Button>
          </div>
        </form>
      </Card>

      {/* Vista previa: así aparece al reservar */}
      <div>
        <p className="mb-2 text-xs font-medium uppercase tracking-wide text-subtle">Así te ven al reservar</p>
        <div className="flex items-start gap-3.5 rounded-xl border border-line bg-surface p-4">
          <Avatar nombre={`${form.nombre} ${form.apellido}`} src={form.foto_url.trim() || null} />
          <div className="min-w-0">
            <p className="font-medium text-fg">{form.nombre} {form.apellido}</p>
            {form.bio && <p className="mt-0.5 line-clamp-3 text-[13px] text-muted">{form.bio}</p>}
          </div>
        </div>
      </div>
    </div>
  );
}
