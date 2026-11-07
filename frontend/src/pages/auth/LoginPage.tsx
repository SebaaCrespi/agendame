import { useState } from 'react';
import { Link, useLocation, useNavigate, useSearchParams } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Lock, Mail } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/Button';
import { Input, PasswordInput } from '@/components/ui/Input';
import { Alerta } from '@/components/ui/Alerta';
import { errorDetail } from '@/components/turnos/errorDetail';
import { destinoSeguro } from '@/utils/destino';
import { AuthLayout } from './AuthLayout';

const loginSchema = z.object({
  email: z.string().email('Email inválido'),
  password: z.string().min(1, 'Ingresá tu contraseña'),
});

type LoginForm = z.infer<typeof loginSchema>;

export function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const [params] = useSearchParams();
  // ?next= viene de la reserva sin cuenta: al entrar, se vuelve a confirmar el turno
  const next = destinoSeguro(params.get('next'));
  const from = next ?? ((location.state as { from?: Location })?.from?.pathname || '/');

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginForm>({ resolver: zodResolver(loginSchema) });

  const onSubmit = async (data: LoginForm) => {
    setError(null);
    setIsLoading(true);
    try {
      await login(data.email, data.password);
      navigate(from, { replace: true });
    } catch (err) {
      setError(errorDetail(err, 'No pudimos iniciar sesión. Revisá tus datos.'));
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <AuthLayout
      title="Iniciar sesión"
      description={next ? 'Ingresá y te llevamos de vuelta a tu reserva.' : 'Ingresá para ver y reservar tus turnos.'}
      footer={
        <>
          ¿No tenés cuenta?{' '}
          <Link to={next ? `/register?next=${encodeURIComponent(next)}` : '/register'} className="font-medium text-primary hover:underline">
            Creá una
          </Link>
        </>
      }
    >
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
        {error && <Alerta tipo="error">{error}</Alerta>}
        <Input
          label="Email"
          type="email"
          placeholder="tu@email.com"
          error={errors.email?.message}
          autoComplete="email"
          leftIcon={<Mail />}
          {...register('email')}
        />
        <PasswordInput
          label="Contraseña"
          placeholder="••••••••"
          error={errors.password?.message}
          autoComplete="current-password"
          leftIcon={<Lock />}
          {...register('password')}
        />
        <Button type="submit" className="w-full" size="lg" loading={isLoading}>
          Iniciar sesión
        </Button>
      </form>
    </AuthLayout>
  );
}
