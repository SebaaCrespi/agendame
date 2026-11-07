import {
  forwardRef,
  useId,
  useState,
  type InputHTMLAttributes,
  type LabelHTMLAttributes,
  type ReactNode,
  type SelectHTMLAttributes,
  type TextareaHTMLAttributes,
} from 'react';
import { ChevronDown, Eye, EyeOff } from 'lucide-react';
import { cn } from '@/utils/cn';

/** Clases compartidas por input, select y textarea. */
export const fieldClass = cn(
  'w-full rounded-lg border border-line bg-surface text-sm text-fg placeholder:text-subtle',
  'transition-colors hover:border-line-strong',
  'focus:border-primary focus:outline-none focus:ring-4 focus:ring-ring',
  'disabled:cursor-not-allowed disabled:bg-surface-2 disabled:opacity-70'
);

const errorClass = 'border-danger hover:border-danger focus:border-danger';

interface FieldWrapperProps {
  id: string;
  label?: string;
  error?: string;
  helperText?: string;
  children: ReactNode;
  className?: string;
}

function FieldWrapper({ id, label, error, helperText, children, className }: FieldWrapperProps) {
  return (
    <div className={cn('w-full', className)}>
      {label && <Label htmlFor={id}>{label}</Label>}
      {children}
      {error ? (
        <p id={`${id}-error`} className="mt-1.5 text-[13px] text-danger" role="alert">
          {error}
        </p>
      ) : helperText ? (
        <p id={`${id}-helper`} className="mt-1.5 text-[13px] text-muted">
          {helperText}
        </p>
      ) : null}
    </div>
  );
}

const describedBy = (id: string, error?: string, helperText?: string) =>
  error ? `${id}-error` : helperText ? `${id}-helper` : undefined;

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helperText?: string;
  leftIcon?: ReactNode;
  /** Elemento interactivo a la derecha del campo (ej. botón de mostrar contraseña). */
  rightElement?: ReactNode;
  wrapperClassName?: string;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className, wrapperClassName, label, error, helperText, id, leftIcon, rightElement, ...props }, ref) => {
    const autoId = useId();
    const inputId = id || autoId;
    return (
      <FieldWrapper id={inputId} label={label} error={error} helperText={helperText} className={wrapperClassName}>
        <div className="relative">
          {leftIcon && (
            <span className="pointer-events-none absolute inset-y-0 left-3 flex items-center text-subtle [&_svg]:size-4">
              {leftIcon}
            </span>
          )}
          <input
            ref={ref}
            id={inputId}
            className={cn(fieldClass, 'h-10 px-3', leftIcon && 'pl-9', rightElement && 'pr-10', error && errorClass, className)}
            aria-invalid={error ? true : undefined}
            aria-describedby={describedBy(inputId, error, helperText)}
            {...props}
          />
          {rightElement && <span className="absolute inset-y-0 right-1 flex items-center">{rightElement}</span>}
        </div>
      </FieldWrapper>
    );
  }
);
Input.displayName = 'Input';

/** Campo de contraseña con botón de ojo para mostrarla u ocultarla. */
export const PasswordInput = forwardRef<HTMLInputElement, Omit<InputProps, 'type' | 'rightElement'>>((props, ref) => {
  const [visible, setVisible] = useState(false);
  const Icono = visible ? EyeOff : Eye;
  return (
    <Input
      ref={ref}
      {...props}
      type={visible ? 'text' : 'password'}
      rightElement={
        <button
          type="button"
          onClick={() => setVisible((v) => !v)}
          aria-label={visible ? 'Ocultar contraseña' : 'Mostrar contraseña'}
          aria-pressed={visible}
          title={visible ? 'Ocultar contraseña' : 'Mostrar contraseña'}
          className="flex size-8 items-center justify-center rounded-md text-subtle transition-colors hover:bg-surface-2 hover:text-fg focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-ring"
        >
          <Icono className="size-4" aria-hidden="true" />
        </button>
      }
    />
  );
});
PasswordInput.displayName = 'PasswordInput';

export const Label = forwardRef<HTMLLabelElement, LabelHTMLAttributes<HTMLLabelElement>>(
  ({ className, children, ...props }, ref) => (
    <label ref={ref} className={cn('mb-1.5 block text-[13px] font-medium text-fg', className)} {...props}>
      {children}
    </label>
  )
);
Label.displayName = 'Label';

interface TextareaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  error?: string;
  helperText?: string;
}

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className, label, error, helperText, id, ...props }, ref) => {
    const autoId = useId();
    const textareaId = id || autoId;
    return (
      <FieldWrapper id={textareaId} label={label} error={error} helperText={helperText}>
        <textarea
          ref={ref}
          id={textareaId}
          className={cn(fieldClass, 'min-h-[80px] resize-y px-3 py-2', error && errorClass, className)}
          aria-invalid={error ? true : undefined}
          aria-describedby={describedBy(textareaId, error, helperText)}
          {...props}
        />
      </FieldWrapper>
    );
  }
);
Textarea.displayName = 'Textarea';

interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  error?: string;
  helperText?: string;
  wrapperClassName?: string;
}

export const Select = forwardRef<HTMLSelectElement, SelectProps>(
  ({ className, wrapperClassName, label, error, helperText, id, children, ...props }, ref) => {
    const autoId = useId();
    const selectId = id || autoId;
    return (
      <FieldWrapper id={selectId} label={label} error={error} helperText={helperText} className={wrapperClassName}>
        <div className="relative">
          <select
            ref={ref}
            id={selectId}
            className={cn(fieldClass, 'h-10 appearance-none pl-3 pr-9', error && errorClass, className)}
            aria-invalid={error ? true : undefined}
            aria-describedby={describedBy(selectId, error, helperText)}
            {...props}
          >
            {children}
          </select>
          <ChevronDown className="pointer-events-none absolute right-3 top-1/2 size-4 -translate-y-1/2 text-subtle" aria-hidden="true" />
        </div>
      </FieldWrapper>
    );
  }
);
Select.displayName = 'Select';
