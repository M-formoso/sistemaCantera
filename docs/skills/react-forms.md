# Skill: React Forms Pattern

## Objetivo
Crear formularios React con validación, manejo de estado y estilo usando shadcn/ui.

## Patrón de Implementación

### 1. Schema de Validación (Zod)
```typescript
// src/types/{entidad}.ts
import { z } from 'zod';

export const {entidad}Schema = z.object({
  nombre: z.string()
    .min(1, 'El nombre es requerido')
    .max(255, 'El nombre no puede exceder 255 caracteres'),
  descripcion: z.string().optional(),
  precio: z.number()
    .positive('El precio debe ser mayor a 0')
    .optional(),
});

export type {Entidad}FormData = z.infer<typeof {entidad}Schema>;

export interface {Entidad} {
  id: string;
  nombre: string;
  descripcion?: string;
  precio?: number;
  activo: boolean;
  createdAt: string;
  updatedAt: string;
}
```

### 2. Componente de Formulario
```typescript
// src/components/{entidad}/{Entidad}Form.tsx
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { {entidad}Schema, type {Entidad}FormData, type {Entidad} } from '@/types/{entidad}';
import { {entidad}Service } from '@/services/{entidad}Service';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import { useToast } from '@/components/ui/use-toast';

interface {Entidad}FormProps {
  {entidad}?: {Entidad};
  onSuccess?: () => void;
  onCancel?: () => void;
}

export function {Entidad}Form({ {entidad}, onSuccess, onCancel }: {Entidad}FormProps) {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const isEditing = !!{entidad};

  const form = useForm<{Entidad}FormData>({
    resolver: zodResolver({entidad}Schema),
    defaultValues: {
      nombre: {entidad}?.nombre || '',
      descripcion: {entidad}?.descripcion || '',
      precio: {entidad}?.precio || undefined,
    },
  });

  const mutation = useMutation({
    mutationFn: (data: {Entidad}FormData) => {
      if (isEditing) {
        return {entidad}Service.update({entidad}.id, data);
      }
      return {entidad}Service.create(data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['{entidades}'] });
      toast({
        title: isEditing ? 'Actualizado' : 'Creado',
        description: `El {entidad} fue ${isEditing ? 'actualizado' : 'creado'} exitosamente.`,
      });
      onSuccess?.();
    },
    onError: (error: any) => {
      toast({
        variant: 'destructive',
        title: 'Error',
        description: error.response?.data?.detail || 'Ocurrió un error al guardar.',
      });
    },
  });

  const onSubmit = (data: {Entidad}FormData) => {
    mutation.mutate(data);
  };

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
        <FormField
          control={form.control}
          name="nombre"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Nombre</FormLabel>
              <FormControl>
                <Input placeholder="Ingrese el nombre" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="descripcion"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Descripción</FormLabel>
              <FormControl>
                <Textarea
                  placeholder="Ingrese una descripción (opcional)"
                  {...field}
                />
              </FormControl>
              <FormDescription>
                Opcional: agregue detalles adicionales
              </FormDescription>
              <FormMessage />
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="precio"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Precio</FormLabel>
              <FormControl>
                <Input
                  type="number"
                  step="0.01"
                  placeholder="0.00"
                  {...field}
                  onChange={(e) => field.onChange(parseFloat(e.target.value))}
                />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <div className="flex gap-2 justify-end">
          {onCancel && (
            <Button
              type="button"
              variant="outline"
              onClick={onCancel}
              disabled={mutation.isPending}
            >
              Cancelar
            </Button>
          )}
          <Button
            type="submit"
            disabled={mutation.isPending}
            className="bg-amber-600 hover:bg-amber-700"
          >
            {mutation.isPending
              ? 'Guardando...'
              : isEditing
              ? 'Actualizar'
              : 'Crear'}
          </Button>
        </div>
      </form>
    </Form>
  );
}
```

### 3. Modal de Formulario
```typescript
// src/components/{entidad}/{Entidad}Modal.tsx
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { {Entidad}Form } from './{Entidad}Form';
import { type {Entidad} } from '@/types/{entidad}';

interface {Entidad}ModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  {entidad}?: {Entidad};
}

export function {Entidad}Modal({ open, onOpenChange, {entidad} }: {Entidad}ModalProps) {
  const isEditing = !!{entidad};

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>
            {isEditing ? 'Editar' : 'Crear'} {Entidad}
          </DialogTitle>
          <DialogDescription>
            {isEditing
              ? 'Modifique los datos del {entidad}'
              : 'Complete el formulario para crear un nuevo {entidad}'}
          </DialogDescription>
        </DialogHeader>
        <{Entidad}Form
          {entidad}={{entidad}}
          onSuccess={() => onOpenChange(false)}
          onCancel={() => onOpenChange(false)}
        />
      </DialogContent>
    </Dialog>
  );
}
```

### 4. Formulario con Cálculo Automático
```typescript
// src/components/pesajes/PesajeForm.tsx
import { useEffect } from 'react';
import { useForm } from 'react-hook-form';

export function PesajeForm() {
  const form = useForm({
    defaultValues: {
      pesoTara: 0,
      pesoBruto: 0,
      pesoNeto: 0,
    },
  });

  const pesoTara = form.watch('pesoTara');
  const pesoBruto = form.watch('pesoBruto');

  // Calcular peso neto automáticamente
  useEffect(() => {
    const neto = pesoBruto - pesoTara;
    if (neto >= 0) {
      form.setValue('pesoNeto', neto);
    }
  }, [pesoTara, pesoBruto, form]);

  return (
    <Form {...form}>
      {/* Campos del formulario */}

      {/* Mostrar peso neto calculado */}
      <div className="p-4 bg-amber-50 rounded-lg border border-amber-200">
        <p className="text-sm text-amber-700 font-medium">
          Peso Neto Calculado
        </p>
        <p className="text-2xl font-bold text-amber-900">
          {form.watch('pesoNeto').toLocaleString('es-AR', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
          })}{' '}
          kg
        </p>
      </div>
    </Form>
  );
}
```

### 5. Formato Argentino
```typescript
// src/utils/formatters.ts
export const formatNumber = (value: number): string => {
  return new Intl.NumberFormat('es-AR', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value);
};

export const formatCurrency = (value: number): string => {
  return new Intl.NumberFormat('es-AR', {
    style: 'currency',
    currency: 'ARS',
  }).format(value);
};

export const formatDate = (date: string | Date): string => {
  return new Intl.DateTimeFormat('es-AR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  }).format(new Date(date));
};

export const formatDateTime = (date: string | Date): string => {
  return new Intl.DateTimeFormat('es-AR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(date));
};
```

## Checklist de Implementación

- [ ] Crear schema de validación Zod en `types/{entidad}.ts`
- [ ] Crear componente de formulario en `components/{entidad}/{Entidad}Form.tsx`
- [ ] Crear modal de formulario (si es necesario)
- [ ] Implementar cálculos automáticos con `useEffect` y `watch`
- [ ] Usar formateo argentino para números y fechas
- [ ] Agregar loading states durante mutaciones
- [ ] Implementar toast notifications para feedback
- [ ] Manejar errores con mensajes claros

## Consideraciones Especiales

1. **Validación**: Usar Zod para schema validation
2. **Estado**: React Hook Form para manejo de estado de formularios
3. **Mutations**: TanStack Query para operaciones asíncronas
4. **Formato**: Usar Intl API para formato argentino
5. **Feedback**: Toast notifications para confirmar acciones
6. **Loading**: Deshabilitar botones durante operaciones
7. **Colores**: Usar paleta ámbar/naranja (#f59e0b, #fb923c) para botones primarios
