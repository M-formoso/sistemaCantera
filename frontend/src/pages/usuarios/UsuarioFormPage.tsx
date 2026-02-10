import { useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft, Save, Shield, Edit, Eye } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { usuariosService } from '@/services/usuariosService'
import { UsuarioCreate, UsuarioUpdate } from '@/types'

const usuarioSchema = z.object({
  email: z.string().email('Email inválido'),
  nombre: z.string().min(1, 'El nombre es requerido').max(100, 'Máximo 100 caracteres'),
  rol: z.enum(['administrador', 'operador', 'solo_lectura'], {
    errorMap: () => ({ message: 'Seleccione un rol válido' }),
  }),
  password: z.string().optional(),
  activo: z.boolean().optional(),
})

type UsuarioFormData = z.infer<typeof usuarioSchema>

export default function UsuarioFormPage() {
  const navigate = useNavigate()
  const { id } = useParams()
  const queryClient = useQueryClient()
  const isEditing = Boolean(id)

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
  } = useForm<UsuarioFormData>({
    resolver: zodResolver(
      isEditing
        ? usuarioSchema.extend({ password: z.string().min(8).optional().or(z.literal('')) })
        : usuarioSchema.extend({ password: z.string().min(8, 'La contraseña debe tener al menos 8 caracteres') })
    ),
    defaultValues: {
      activo: true,
    },
  })

  // Obtener datos del usuario si estamos editando
  const { data: usuario, isLoading } = useQuery({
    queryKey: ['usuario', id],
    queryFn: () => usuariosService.getById(id!),
    enabled: isEditing,
  })

  // Llenar el formulario cuando cargue el usuario
  useEffect(() => {
    if (usuario) {
      reset({
        email: usuario.email,
        nombre: usuario.nombre,
        rol: usuario.rol,
        activo: usuario.activo,
      })
    }
  }, [usuario, reset])

  // Mutación para crear
  const createMutation = useMutation({
    mutationFn: (data: UsuarioCreate) => usuariosService.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['usuarios'] })
      navigate('/usuarios')
    },
  })

  // Mutación para actualizar
  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: UsuarioUpdate }) =>
      usuariosService.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['usuarios'] })
      queryClient.invalidateQueries({ queryKey: ['usuario', id] })
      navigate('/usuarios')
    },
  })

  const onSubmit = async (data: UsuarioFormData) => {
    try {
      if (isEditing) {
        // En edición, no enviamos password a menos que se haya ingresado uno nuevo
        const { password, ...updateData } = data
        await updateMutation.mutateAsync({ id: id!, data: updateData })
      } else {
        // En creación, password es obligatorio
        if (!data.password) {
          alert('La contraseña es requerida')
          return
        }
        await createMutation.mutateAsync(data as UsuarioCreate)
      }
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Error al guardar el usuario')
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Cargando usuario...</div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" onClick={() => navigate('/usuarios')}>
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div>
          <h1 className="text-3xl font-bold text-gray-900">
            {isEditing ? 'Editar Usuario' : 'Nuevo Usuario'}
          </h1>
          <p className="text-gray-500">
            {isEditing ? 'Actualizar información del usuario' : 'Crear un nuevo usuario del sistema'}
          </p>
        </div>
      </div>

      {/* Formulario */}
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle>Información del Usuario</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Nombre */}
            <div className="space-y-2">
              <label htmlFor="nombre" className="text-sm font-medium">
                Nombre Completo <span className="text-red-500">*</span>
              </label>
              <Input
                id="nombre"
                type="text"
                placeholder="Ej: Juan Pérez"
                {...register('nombre')}
              />
              {errors.nombre && (
                <p className="text-sm text-red-500">{errors.nombre.message}</p>
              )}
            </div>

            {/* Email */}
            <div className="space-y-2">
              <label htmlFor="email" className="text-sm font-medium">
                Email <span className="text-red-500">*</span>
              </label>
              <Input
                id="email"
                type="email"
                placeholder="usuario@example.com"
                {...register('email')}
              />
              {errors.email && (
                <p className="text-sm text-red-500">{errors.email.message}</p>
              )}
            </div>

            {/* Rol */}
            <div className="space-y-2">
              <label htmlFor="rol" className="text-sm font-medium">
                Rol <span className="text-red-500">*</span>
              </label>
              <select
                id="rol"
                {...register('rol')}
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
              >
                <option value="">Seleccione un rol</option>
                <option value="administrador">
                  Administrador - Acceso total al sistema
                </option>
                <option value="operador">
                  Operador - Puede crear y modificar registros
                </option>
                <option value="solo_lectura">
                  Solo Lectura - Solo puede visualizar información
                </option>
              </select>
              {errors.rol && (
                <p className="text-sm text-red-500">{errors.rol.message}</p>
              )}

              {/* Descripción de roles */}
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 space-y-2 text-sm">
                <p className="font-medium text-blue-900">Permisos por rol:</p>
                <div className="space-y-1 text-blue-800">
                  <div className="flex items-start gap-2">
                    <Shield className="h-4 w-4 mt-0.5 flex-shrink-0" />
                    <span>
                      <strong>Administrador:</strong> Acceso completo a todas las funcionalidades,
                      incluyendo gestión de usuarios y configuración del sistema.
                    </span>
                  </div>
                  <div className="flex items-start gap-2">
                    <Edit className="h-4 w-4 mt-0.5 flex-shrink-0" />
                    <span>
                      <strong>Operador:</strong> Puede crear, editar y eliminar registros de
                      camiones, repuestos, servicios, pesajes y combustible.
                    </span>
                  </div>
                  <div className="flex items-start gap-2">
                    <Eye className="h-4 w-4 mt-0.5 flex-shrink-0" />
                    <span>
                      <strong>Solo Lectura:</strong> Solo puede visualizar información, sin
                      permisos para crear o modificar registros.
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* Password (solo en creación o si se quiere cambiar) */}
            {!isEditing && (
              <div className="space-y-2">
                <label htmlFor="password" className="text-sm font-medium">
                  Contraseña <span className="text-red-500">*</span>
                </label>
                <Input
                  id="password"
                  type="password"
                  placeholder="Mínimo 8 caracteres"
                  {...register('password')}
                />
                {errors.password && (
                  <p className="text-sm text-red-500">{errors.password.message}</p>
                )}
                <p className="text-xs text-gray-500">
                  La contraseña debe tener al menos 8 caracteres
                </p>
              </div>
            )}

            {isEditing && (
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                <p className="text-sm text-yellow-800">
                  Para cambiar la contraseña de este usuario, use el botón "Resetear contraseña" en
                  la lista de usuarios.
                </p>
              </div>
            )}

            {/* Estado (solo en edición) */}
            {isEditing && (
              <div className="flex items-center gap-2">
                <input
                  id="activo"
                  type="checkbox"
                  {...register('activo')}
                  className="h-4 w-4 rounded border-gray-300"
                />
                <label htmlFor="activo" className="text-sm font-medium">
                  Usuario activo
                </label>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Botones */}
        <div className="flex gap-4 justify-end">
          <Button type="button" variant="outline" onClick={() => navigate('/usuarios')}>
            Cancelar
          </Button>
          <Button
            type="submit"
            disabled={createMutation.isPending || updateMutation.isPending}
          >
            {createMutation.isPending || updateMutation.isPending ? (
              <>Guardando...</>
            ) : (
              <>
                <Save className="mr-2 h-4 w-4" />
                {isEditing ? 'Actualizar Usuario' : 'Crear Usuario'}
              </>
            )}
          </Button>
        </div>
      </form>
    </div>
  )
}
