import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/Card';
import { cn } from '@/utils/cn';
import { AlertCircle, Mail, Lock, User, Building2 } from 'lucide-react';

const registerSchema = z.object({
  email: z.string().email('Email inválido'),
  password: z.string().min(8, 'Mínimo 8 caracteres'),
  confirmPassword: z.string(),
  nombre: z.string().min(2, 'Mínimo 2 caracteres'),
  rol: z.enum(['CLIENTE', 'PROVEEDOR']),
}).refine((data) => data.password === data.confirmPassword, {
  message: 'Las contraseñas no coinciden',
  path: ['confirmPassword'],
});

type RegisterForm = z.infer<typeof registerSchema>;

export function RegisterPage() {
  const { register: registerUser } = useAuth();
  const navigate = useNavigate();
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm<RegisterForm>({
    resolver: zodResolver(registerSchema),
    defaultValues: { rol: 'CLIENTE' },
  });

  const selectedRole = watch('rol');

  const onSubmit = async (data: RegisterForm) => {
    setError(null);
    setIsLoading(true);
    try {
      await registerUser({
        email: data.email,
        password: data.password,
        nombre: data.nombre,
        rol: data.rol,
      });
      navigate('/cliente/dashboard');
    } catch (err: unknown) {
      const axiosError = err as { response?: { data?: { detail?: string } } };
      setError(axiosError.response?.data?.detail || 'Error al registrarse. Intenta nuevamente.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-[calc(100vh-200px)] flex items-center justify-center px-4 py-8">
      <Card className="w-full max-w-md" padding="lg">
        <CardHeader className="text-center">
          <CardTitle className="text-2xl">Crear cuenta</CardTitle>
          <CardDescription>Únete a Agendame y gestiona tus turnos</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
            {error && (
              <div className="flex items-center gap-2 p-3 rounded-lg bg-red-50 text-red-700 dark:bg-red-900/30 dark:text-red-300" role="alert">
                <AlertCircle className="h-5 w-5 flex-shrink-0" />
                <p className="text-sm">{error}</p>
              </div>
            )}

            <div className="grid grid-cols-2 gap-4">
              <div className="flex flex-col">
                <label className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Tipo de cuenta
                </label>
                <div className="grid grid-cols-2 gap-2" role="radiogroup" aria-label="Tipo de cuenta">
                  {['CLIENTE', 'PROVEEDOR'].map((role) => (
                    <label
                      key={role}
                      className={cn(
                        'relative cursor-pointer rounded-lg border-2 p-3 text-center transition-all',
                        selectedRole === role
                          ? 'border-indigo-500 bg-indigo-50 dark:bg-indigo-900/20'
                          : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                      )}
                    >
                      <input
                        type="radio"
                        value={role}
                        {...register('rol')}
                        className="sr-only"
                        aria-label={role === 'CLIENTE' ? 'Cliente' : 'Profesional'}
                      />
                      <div className="flex flex-col items-center gap-2">
                        <span className="text-lg">
                          {role === 'CLIENTE' ? <User className="h-6 w-6" /> : <Building2 className="h-6 w-6" />}
                        </span>
                        <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                          {role === 'CLIENTE' ? 'Cliente' : 'Profesional'}
                        </span>
                      </div>
                    </label>
                  ))}
                </div>
                {errors.rol && (
                  <p className="mt-1 text-sm text-red-600 dark:text-red-400" role="alert">
                    {errors.rol.message}
                  </p>
                )}
              </div>
            </div>

            <Input
              label="Nombre completo"
              type="text"
              placeholder="Juan Pérez"
              error={errors.nombre?.message}
              {...register('nombre')}
              autoComplete="name"
              leftIcon={<User className="h-5 w-5 text-gray-400" />}
            />

            <Input
              label="Email"
              type="email"
              placeholder="tu@email.com"
              error={errors.email?.message}
              {...register('email')}
              autoComplete="email"
              leftIcon={<Mail className="h-5 w-5 text-gray-400" />}
            />

            <Input
              label="Contraseña"
              type="password"
              placeholder="••••••••"
              error={errors.password?.message}
              {...register('password')}
              autoComplete="new-password"
              leftIcon={<Lock className="h-5 w-5 text-gray-400" />}
              helperText="Mínimo 8 caracteres"
            />

            <Input
              label="Confirmar contraseña"
              type="password"
              placeholder="••••••••"
              error={errors.confirmPassword?.message}
              {...register('confirmPassword')}
              autoComplete="new-password"
              leftIcon={<Lock className="h-5 w-5 text-gray-400" />}
            />

            <Button type="submit" className="w-full" size="lg" loading={isLoading}>
              Crear cuenta
            </Button>
          </form>
        </CardContent>
        <CardFooter className="justify-center">
          <p className="text-sm text-gray-600 dark:text-gray-400">
            ¿Ya tienes cuenta?{' '}
            <Link to="/login" className="text-indigo-600 hover:text-indigo-500 font-medium">
              Inicia sesión
            </Link>
          </p>
        </CardFooter>
      </Card>
    </div>
  );
}