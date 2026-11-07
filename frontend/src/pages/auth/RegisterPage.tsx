import { useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Briefcase, Lock, Mail, User } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/Button';
import { Input, PasswordInput } from '@/components/ui/Input';
import { Alerta } from '@/components/ui/Alerta';
import { errorDetail, erroresPorCampo } from '@/components/turnos/errorDetail';
import { cn } from '@/utils/cn';
import { destinoSeguro } from '@/utils/destino';
import { AuthLayout } from './AuthLayout';

/** Las mismas que rechaza el backend (schemas/auth.py). */
const PASSWORDS_COMUNES = new Set(['password', '12345678', 'password123', 'admin123', 'qwerty123']);

const registerSchema = z
  .object({
    email: z.string().email('Email inválido'),
    password: z
      .string()
      .min(8, 'Mínimo 8 caracteres')
      .refine((p) => !PASSWORDS_COMUNES.has(p.toLowerCase()), 'La contraseña es demasiado común. Elegí otra.'),
    confirmPassword: z.string(),
    nombre: z.string().min(2, 'Mínimo 2 caracteres'),
    rol: z.enum(['CLIENTE', 'PROVEEDOR']),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: 'Las contraseñas no coinciden',
    path: ['confirmPassword'],
  });

type RegisterForm = z.infer<typeof registerSchema>;

const ROLES = [
  { value: 'CLIENTE', label: 'Quiero reservar', icon: User },
  { value: 'PROVEEDOR', label: 'Soy profesional', icon: Briefcase },
] as const;

export function RegisterPage() {
  const { register: registerUser } = useAuth();
  const navigate = useNavigate();
  const [params] = useSearchParams();
  // ?next= viene de la reserva sin cuenta: se crea cuenta de cliente y se vuelve al turno
  const next = destinoSeguro(params.get('next'));
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const {
    register,
    handleSubmit,
    watch,
    setError: setErrorCampo,
    formState: { errors },
  } = useForm<RegisterForm>({
    resolver: zodResolver(registerSchema),
    defaultValues: { rol: !next && params.get('rol') === 'PROVEEDOR' ? 'PROVEEDOR' : 'CLIENTE' },
  });

  const rol = watch('rol');

  const onSubmit = async (data: RegisterForm) => {
    setError(null);
    setIsLoading(true);
    try {
      await registerUser({ email: data.email, password: data.password, nombre: data.nombre, rol: data.rol });
      // "/" lleva al panel de cada rol; con ?next= se vuelve a la reserva
      navigate(next ?? '/', { replace: true });
    } catch (err) {
      // Errores de validación del backend: se muestran debajo de cada campo
      const porCampo = erroresPorCampo(err);
      const conocidos = (['email', 'password', 'nombre'] as const).filter((c) => porCampo[c]);
      conocidos.forEach((c) => setErrorCampo(c, { message: porCampo[c] }));
      if (conocidos.length === 0) setError(errorDetail(err, 'No pudimos crear la cuenta. Probá de nuevo.'));
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <AuthLayout
      title="Crear cuenta"
      description={next ? 'Creá tu cuenta y confirmá el turno que elegiste.' : 'Te lleva menos de un minuto.'}
      footer={
        <>
          ¿Ya tenés cuenta?{' '}
          <Link to={next ? `/login?next=${encodeURIComponent(next)}` : '/login'} className="font-medium text-primary hover:underline">
            Iniciá sesión
          </Link>
        </>
      }
    >
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
        {error && <Alerta tipo="error">{error}</Alerta>}

        {next && <Alerta tipo="info">Tu turno queda guardado. Después de crear la cuenta volvés a confirmarlo.</Alerta>}

        {/* Desde una reserva la cuenta es de cliente: no se elige tipo */}
        <fieldset className={next ? 'hidden' : undefined}>
          <legend className="mb-1.5 text-[13px] font-medium text-fg">Tipo de cuenta</legend>
          <div className="grid grid-cols-2 gap-2">
            {ROLES.map(({ value, label, icon: Icon }) => (
              <label
                key={value}
                className={cn(
                  'flex cursor-pointer items-center gap-2.5 rounded-lg border px-3 py-2.5 text-[13px] font-medium transition-colors has-[:focus-visible]:ring-4 has-[:focus-visible]:ring-ring',
                  rol === value ? 'border-primary bg-primary-soft text-primary' : 'border-line bg-surface text-muted hover:border-line-strong'
                )}
              >
                <input type="radio" value={value} className="sr-only" {...register('rol')} />
                <Icon className="size-4" aria-hidden="true" />
                {label}
              </label>
            ))}
          </div>
        </fieldset>

        <Input label="Nombre completo" placeholder="Juan Pérez" error={errors.nombre?.message} autoComplete="name" leftIcon={<User />} {...register('nombre')} />
        <Input label="Email" type="email" placeholder="tu@email.com" error={errors.email?.message} autoComplete="email" leftIcon={<Mail />} {...register('email')} />
        <PasswordInput
          label="Contraseña"
          placeholder="••••••••"
          error={errors.password?.message}
          helperText="Mínimo 8 caracteres"
          autoComplete="new-password"
          leftIcon={<Lock />}
          {...register('password')}
        />
        <PasswordInput
          label="Repetir contraseña"
          placeholder="••••••••"
          error={errors.confirmPassword?.message}
          autoComplete="new-password"
          leftIcon={<Lock />}
          {...register('confirmPassword')}
        />
        <Button type="submit" className="w-full" size="lg" loading={isLoading}>
          Crear cuenta
        </Button>
      </form>
    </AuthLayout>
  );
}
