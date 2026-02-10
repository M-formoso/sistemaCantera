import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import {
  ColumnDef,
  flexRender,
  getCoreRowModel,
  useReactTable,
  getSortedRowModel,
  SortingState,
  getFilteredRowModel,
  ColumnFiltersState,
} from '@tanstack/react-table'
import { Users, Plus, Pencil, Trash2, Key, Shield, Eye, Edit } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { usuariosService } from '@/services/usuariosService'
import { User } from '@/types'
import { useAuthStore } from '@/stores/authStore'
import { format } from 'date-fns'
import { es } from 'date-fns/locale'

export default function UsuariosPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { user: currentUser } = useAuthStore()
  const [sorting, setSorting] = useState<SortingState>([])
  const [columnFilters, setColumnFilters] = useState<ColumnFiltersState>([])
  const [showResetPassword, setShowResetPassword] = useState<string | null>(null)
  const [newPassword, setNewPassword] = useState('')

  const { data: response, isLoading } = useQuery({
    queryKey: ['usuarios'],
    queryFn: () => usuariosService.getAll({ limit: 100 }),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => usuariosService.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['usuarios'] })
    },
  })

  const resetPasswordMutation = useMutation({
    mutationFn: ({ id, password }: { id: string; password: string }) =>
      usuariosService.resetPassword(id, password),
    onSuccess: () => {
      setShowResetPassword(null)
      setNewPassword('')
      alert('Contraseña restablecida correctamente')
    },
  })

  const handleDelete = async (id: string, nombre: string) => {
    if (window.confirm(`¿Está seguro de eliminar al usuario ${nombre}?`)) {
      try {
        await deleteMutation.mutateAsync(id)
      } catch (error: any) {
        alert(error.response?.data?.detail || 'Error al eliminar el usuario')
      }
    }
  }

  const handleResetPassword = async (id: string) => {
    if (newPassword.length < 8) {
      alert('La contraseña debe tener al menos 8 caracteres')
      return
    }

    if (window.confirm('¿Está seguro de restablecer la contraseña de este usuario?')) {
      try {
        await resetPasswordMutation.mutateAsync({ id, password: newPassword })
      } catch (error: any) {
        alert(error.response?.data?.detail || 'Error al restablecer la contraseña')
      }
    }
  }

  const getRoleBadgeColor = (rol: string) => {
    switch (rol) {
      case 'administrador':
        return 'bg-purple-100 text-purple-700'
      case 'operador':
        return 'bg-blue-100 text-blue-700'
      case 'solo_lectura':
        return 'bg-gray-100 text-gray-700'
      default:
        return 'bg-gray-100 text-gray-700'
    }
  }

  const getRoleIcon = (rol: string) => {
    switch (rol) {
      case 'administrador':
        return <Shield className="h-3 w-3" />
      case 'operador':
        return <Edit className="h-3 w-3" />
      case 'solo_lectura':
        return <Eye className="h-3 w-3" />
      default:
        return null
    }
  }

  const columns: ColumnDef<User>[] = [
    {
      accessorKey: 'nombre',
      header: 'Nombre',
      cell: ({ row }) => (
        <div className="font-medium">{row.getValue('nombre')}</div>
      ),
    },
    {
      accessorKey: 'email',
      header: 'Email',
      cell: ({ row }) => (
        <div className="text-sm text-gray-600">{row.getValue('email')}</div>
      ),
    },
    {
      accessorKey: 'rol',
      header: 'Rol',
      cell: ({ row }) => {
        const rol = row.getValue('rol') as string
        return (
          <span
            className={`inline-flex items-center gap-1 px-2 py-1 text-xs font-medium rounded ${getRoleBadgeColor(rol)}`}
          >
            {getRoleIcon(rol)}
            {rol.replace('_', ' ')}
          </span>
        )
      },
    },
    {
      accessorKey: 'activo',
      header: 'Estado',
      cell: ({ row }) => {
        const activo = row.getValue('activo') as boolean
        return (
          <span
            className={`inline-flex px-2 py-1 text-xs font-medium rounded ${
              activo
                ? 'bg-green-100 text-green-700'
                : 'bg-red-100 text-red-700'
            }`}
          >
            {activo ? 'Activo' : 'Inactivo'}
          </span>
        )
      },
    },
    {
      accessorKey: 'ultimo_acceso',
      header: 'Último acceso',
      cell: ({ row }) => {
        const fecha = row.getValue('ultimo_acceso') as string | undefined
        if (!fecha) return <span className="text-gray-400 text-sm">Nunca</span>
        return (
          <div className="text-sm text-gray-600">
            {format(new Date(fecha), "dd/MM/yyyy HH:mm", { locale: es })}
          </div>
        )
      },
    },
    {
      id: 'actions',
      header: 'Acciones',
      cell: ({ row }) => {
        const usuario = row.original
        const isCurrentUser = usuario.id === currentUser?.id

        return (
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => navigate(`/usuarios/${usuario.id}/editar`)}
              title="Editar usuario"
            >
              <Pencil className="h-4 w-4" />
            </Button>

            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                setShowResetPassword(usuario.id)
                setNewPassword('')
              }}
              title="Resetear contraseña"
            >
              <Key className="h-4 w-4" />
            </Button>

            {!isCurrentUser && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => handleDelete(usuario.id, usuario.nombre)}
                className="text-red-600 hover:text-red-700"
                title="Eliminar usuario"
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            )}
          </div>
        )
      },
    },
  ]

  const table = useReactTable({
    data: response?.items || [],
    columns,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    onSortingChange: setSorting,
    onColumnFiltersChange: setColumnFilters,
    state: {
      sorting,
      columnFilters,
    },
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Cargando usuarios...</div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Users className="h-8 w-8 text-brand-600" />
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Usuarios</h1>
            <p className="text-gray-500">Gestión de usuarios del sistema</p>
          </div>
        </div>
        <Button onClick={() => navigate('/usuarios/nuevo')}>
          <Plus className="mr-2 h-4 w-4" />
          Nuevo Usuario
        </Button>
      </div>

      {/* Filtros */}
      <Card>
        <CardHeader>
          <CardTitle>Filtros</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-4">
            <div className="flex-1">
              <Input
                placeholder="Buscar por nombre o email..."
                value={(table.getColumn('nombre')?.getFilterValue() as string) ?? ''}
                onChange={(event) =>
                  table.getColumn('nombre')?.setFilterValue(event.target.value)
                }
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Tabla */}
      <Card>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b">
                {table.getHeaderGroups().map((headerGroup) => (
                  <tr key={headerGroup.id}>
                    {headerGroup.headers.map((header) => (
                      <th
                        key={header.id}
                        className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                      >
                        {header.isPlaceholder
                          ? null
                          : flexRender(
                              header.column.columnDef.header,
                              header.getContext()
                            )}
                      </th>
                    ))}
                  </tr>
                ))}
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {table.getRowModel().rows.length === 0 ? (
                  <tr>
                    <td
                      colSpan={columns.length}
                      className="px-6 py-8 text-center text-gray-500"
                    >
                      No se encontraron usuarios
                    </td>
                  </tr>
                ) : (
                  table.getRowModel().rows.map((row) => (
                    <tr key={row.id} className="hover:bg-gray-50">
                      {row.getVisibleCells().map((cell) => (
                        <td key={cell.id} className="px-6 py-4 whitespace-nowrap">
                          {flexRender(cell.column.columnDef.cell, cell.getContext())}
                        </td>
                      ))}
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Modal de resetear contraseña */}
      {showResetPassword && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <Card className="w-full max-w-md">
            <CardHeader>
              <CardTitle>Resetear Contraseña</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="text-sm font-medium mb-2 block">Nueva Contraseña</label>
                <Input
                  type="password"
                  placeholder="Mínimo 8 caracteres"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                />
              </div>
              <div className="flex gap-2 justify-end">
                <Button
                  variant="outline"
                  onClick={() => {
                    setShowResetPassword(null)
                    setNewPassword('')
                  }}
                >
                  Cancelar
                </Button>
                <Button onClick={() => handleResetPassword(showResetPassword)}>
                  Resetear Contraseña
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}
