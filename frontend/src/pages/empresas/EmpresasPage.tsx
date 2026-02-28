import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
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
import { Building2, Plus, Pencil, Trash2, Truck, UserCheck, Car, X } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { empresasService, CamionCliente, CamionClienteCreate } from '@/services/empresasService'
import { Empresa, EmpresaCreate, TipoEmpresa } from '@/types'
import { useIsAdmin } from '@/hooks/useIsAdmin'

export default function EmpresasPage() {
  const queryClient = useQueryClient()
  const isAdmin = useIsAdmin()
  const [sorting, setSorting] = useState<SortingState>([])
  const [columnFilters, setColumnFilters] = useState<ColumnFiltersState>([])
  const [filtroTipo, setFiltroTipo] = useState<TipoEmpresa | 'todos'>('todos')
  const [showModal, setShowModal] = useState(false)
  const [editingEmpresa, setEditingEmpresa] = useState<Empresa | null>(null)
  const [formData, setFormData] = useState<EmpresaCreate>({
    nombre: '',
    tipo: 'cliente',
    cuit: '',
    direccion: '',
    telefono: '',
    email: '',
    contacto: '',
  })

  // Estado para gestión de camiones de clientes
  const [selectedCliente, setSelectedCliente] = useState<Empresa | null>(null)
  const [showCamionesModal, setShowCamionesModal] = useState(false)
  const [showCamionForm, setShowCamionForm] = useState(false)
  const [editingCamion, setEditingCamion] = useState<CamionCliente | null>(null)
  const [camionFormData, setCamionFormData] = useState<CamionClienteCreate>({
    patente: '',
    descripcion: '',
    chofer_habitual: '',
  })

  const { data: empresas, isLoading } = useQuery({
    queryKey: ['empresas', filtroTipo],
    queryFn: () =>
      filtroTipo === 'todos'
        ? empresasService.getAll()
        : empresasService.getAll(filtroTipo),
  })

  const createMutation = useMutation({
    mutationFn: (data: EmpresaCreate) => empresasService.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['empresas'] })
      closeModal()
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<EmpresaCreate> }) =>
      empresasService.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['empresas'] })
      closeModal()
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => empresasService.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['empresas'] })
    },
  })

  // Query para camiones del cliente seleccionado
  const { data: camiones, isLoading: loadingCamiones } = useQuery({
    queryKey: ['camiones', selectedCliente?.id],
    queryFn: () => empresasService.getCamiones(selectedCliente!.id),
    enabled: !!selectedCliente && showCamionesModal,
  })

  // Mutations para camiones
  const createCamionMutation = useMutation({
    mutationFn: (data: CamionClienteCreate) =>
      empresasService.agregarCamion(selectedCliente!.id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['camiones', selectedCliente?.id] })
      closeCamionForm()
    },
  })

  const updateCamionMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<CamionClienteCreate> }) =>
      empresasService.actualizarCamion(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['camiones', selectedCliente?.id] })
      closeCamionForm()
    },
  })

  const deleteCamionMutation = useMutation({
    mutationFn: (id: string) => empresasService.eliminarCamion(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['camiones', selectedCliente?.id] })
    },
  })

  const openCreateModal = () => {
    setEditingEmpresa(null)
    setFormData({
      nombre: '',
      tipo: 'cliente',
      cuit: '',
      direccion: '',
      telefono: '',
      email: '',
      contacto: '',
    })
    setShowModal(true)
  }

  const openEditModal = (empresa: Empresa) => {
    setEditingEmpresa(empresa)
    setFormData({
      nombre: empresa.nombre,
      tipo: empresa.tipo,
      cuit: empresa.cuit || '',
      direccion: empresa.direccion || '',
      telefono: empresa.telefono || '',
      email: empresa.email || '',
      contacto: empresa.contacto || '',
    })
    setShowModal(true)
  }

  const closeModal = () => {
    setShowModal(false)
    setEditingEmpresa(null)
    setFormData({
      nombre: '',
      tipo: 'cliente',
      cuit: '',
      direccion: '',
      telefono: '',
      email: '',
      contacto: '',
    })
  }

  // Funciones para modal de camiones
  const openCamionesModal = (empresa: Empresa) => {
    setSelectedCliente(empresa)
    setShowCamionesModal(true)
  }

  const closeCamionesModal = () => {
    setShowCamionesModal(false)
    setSelectedCliente(null)
    closeCamionForm()
  }

  const openCamionCreateForm = () => {
    setEditingCamion(null)
    setCamionFormData({
      patente: '',
      descripcion: '',
      chofer_habitual: '',
    })
    setShowCamionForm(true)
  }

  const openCamionEditForm = (camion: CamionCliente) => {
    setEditingCamion(camion)
    setCamionFormData({
      patente: camion.patente,
      descripcion: camion.descripcion || '',
      chofer_habitual: camion.chofer_habitual || '',
    })
    setShowCamionForm(true)
  }

  const closeCamionForm = () => {
    setShowCamionForm(false)
    setEditingCamion(null)
    setCamionFormData({
      patente: '',
      descripcion: '',
      chofer_habitual: '',
    })
  }

  const handleCamionSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!camionFormData.patente.trim()) {
      alert('La patente es requerida')
      return
    }

    try {
      if (editingCamion) {
        await updateCamionMutation.mutateAsync({
          id: editingCamion.id,
          data: camionFormData,
        })
      } else {
        await createCamionMutation.mutateAsync(camionFormData)
      }
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Error al guardar camión')
    }
  }

  const handleDeleteCamion = async (camion: CamionCliente) => {
    if (window.confirm(`¿Eliminar patente "${camion.patente}"?`)) {
      try {
        await deleteCamionMutation.mutateAsync(camion.id)
      } catch (error: any) {
        alert(error.response?.data?.detail || 'Error al eliminar')
      }
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!formData.nombre.trim()) {
      alert('El nombre es requerido')
      return
    }

    try {
      if (editingEmpresa) {
        await updateMutation.mutateAsync({ id: editingEmpresa.id, data: formData })
      } else {
        await createMutation.mutateAsync(formData)
      }
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Error al guardar')
    }
  }

  const handleDelete = async (id: string, nombre: string) => {
    if (window.confirm(`¿Está seguro de eliminar "${nombre}"?`)) {
      try {
        await deleteMutation.mutateAsync(id)
      } catch (error: any) {
        alert(error.response?.data?.detail || 'Error al eliminar')
      }
    }
  }

  const getTipoBadge = (tipo: TipoEmpresa) => {
    if (tipo === 'cliente') {
      return (
        <span className="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium rounded bg-blue-100 text-blue-700">
          <UserCheck className="h-3 w-3" />
          Cliente
        </span>
      )
    }
    return (
      <span className="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium rounded bg-orange-100 text-orange-700">
        <Truck className="h-3 w-3" />
        Transportista
      </span>
    )
  }

  const columns: ColumnDef<Empresa>[] = [
    {
      accessorKey: 'nombre',
      header: 'Nombre',
      cell: ({ row }) => (
        <div className="font-medium">{row.getValue('nombre')}</div>
      ),
    },
    {
      accessorKey: 'tipo',
      header: 'Tipo',
      cell: ({ row }) => getTipoBadge(row.getValue('tipo') as TipoEmpresa),
    },
    {
      accessorKey: 'cuit',
      header: 'CUIT',
      cell: ({ row }) => (
        <div className="text-sm text-gray-600">
          {row.getValue('cuit') || '-'}
        </div>
      ),
    },
    {
      accessorKey: 'telefono',
      header: 'Teléfono',
      cell: ({ row }) => (
        <div className="text-sm text-gray-600">
          {row.getValue('telefono') || '-'}
        </div>
      ),
    },
    {
      accessorKey: 'contacto',
      header: 'Contacto',
      cell: ({ row }) => (
        <div className="text-sm text-gray-600">
          {row.getValue('contacto') || '-'}
        </div>
      ),
    },
    {
      accessorKey: 'activo',
      header: 'Estado',
      cell: ({ row }) => {
        const activo = row.getValue('activo') as boolean
        return (
          <span
            className={`inline-flex px-2 py-1 text-xs font-medium rounded ${
              activo ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
            }`}
          >
            {activo ? 'Activo' : 'Inactivo'}
          </span>
        )
      },
    },
    {
      id: 'actions',
      header: 'Acciones',
      cell: ({ row }) => {
        const empresa = row.original
        return (
          <div className="flex items-center gap-2">
            {empresa.tipo === 'cliente' && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => openCamionesModal(empresa)}
                title="Ver Camiones/Patentes"
                className="text-blue-600 hover:text-blue-700"
              >
                <Car className="h-4 w-4" />
              </Button>
            )}
            <Button
              variant="ghost"
              size="sm"
              onClick={() => openEditModal(empresa)}
              title="Editar"
            >
              <Pencil className="h-4 w-4" />
            </Button>
            {isAdmin && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => handleDelete(empresa.id, empresa.nombre)}
                className="text-red-600 hover:text-red-700"
                title="Eliminar"
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
    data: empresas || [],
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
        <div className="text-gray-500">Cargando empresas...</div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <Building2 className="h-6 w-6 sm:h-8 sm:w-8 text-brand-600" />
          <div>
            <h1 className="text-2xl sm:text-3xl font-bold text-gray-900">
              Clientes y Transportistas
            </h1>
            <p className="text-gray-500 text-sm sm:text-base">
              Gestión de empresas para pesajes
            </p>
          </div>
        </div>
        <Button onClick={openCreateModal} className="w-full sm:w-auto">
          <Plus className="mr-2 h-4 w-4" />
          Nueva Empresa
        </Button>
      </div>

      {/* Filtros */}
      <Card>
        <CardHeader className="px-3 sm:px-6">
          <CardTitle className="text-lg sm:text-xl">Filtros</CardTitle>
        </CardHeader>
        <CardContent className="px-3 sm:px-6">
          <div className="flex flex-col sm:flex-row gap-4">
            <Input
              placeholder="Buscar por nombre..."
              value={(table.getColumn('nombre')?.getFilterValue() as string) ?? ''}
              onChange={(event) =>
                table.getColumn('nombre')?.setFilterValue(event.target.value)
              }
              className="flex-1"
            />
            <div className="flex gap-2">
              <Button
                variant={filtroTipo === 'todos' ? 'default' : 'outline'}
                onClick={() => setFiltroTipo('todos')}
                size="sm"
              >
                Todos
              </Button>
              <Button
                variant={filtroTipo === 'cliente' ? 'default' : 'outline'}
                onClick={() => setFiltroTipo('cliente')}
                size="sm"
              >
                <UserCheck className="mr-1 h-4 w-4" />
                Clientes
              </Button>
              <Button
                variant={filtroTipo === 'transportista' ? 'default' : 'outline'}
                onClick={() => setFiltroTipo('transportista')}
                size="sm"
              >
                <Truck className="mr-1 h-4 w-4" />
                Transportistas
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Tabla */}
      <Card>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full min-w-[700px]">
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
                      No se encontraron empresas
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

      {/* Modal de crear/editar */}
      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <Card className="w-full max-w-lg max-h-[90vh] overflow-y-auto">
            <CardHeader>
              <CardTitle>
                {editingEmpresa ? 'Editar Empresa' : 'Nueva Empresa'}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="text-sm font-medium mb-2 block">
                    Nombre *
                  </label>
                  <Input
                    value={formData.nombre}
                    onChange={(e) =>
                      setFormData({ ...formData, nombre: e.target.value })
                    }
                    placeholder="Nombre de la empresa"
                    required
                  />
                </div>

                <div>
                  <label className="text-sm font-medium mb-2 block">Tipo *</label>
                  <div className="flex gap-2">
                    <Button
                      type="button"
                      variant={formData.tipo === 'cliente' ? 'default' : 'outline'}
                      onClick={() => setFormData({ ...formData, tipo: 'cliente' })}
                      className="flex-1"
                    >
                      <UserCheck className="mr-2 h-4 w-4" />
                      Cliente
                    </Button>
                    <Button
                      type="button"
                      variant={
                        formData.tipo === 'transportista' ? 'default' : 'outline'
                      }
                      onClick={() =>
                        setFormData({ ...formData, tipo: 'transportista' })
                      }
                      className="flex-1"
                    >
                      <Truck className="mr-2 h-4 w-4" />
                      Transportista
                    </Button>
                  </div>
                </div>

                <div>
                  <label className="text-sm font-medium mb-2 block">CUIT</label>
                  <Input
                    value={formData.cuit}
                    onChange={(e) =>
                      setFormData({ ...formData, cuit: e.target.value })
                    }
                    placeholder="XX-XXXXXXXX-X"
                  />
                </div>

                <div>
                  <label className="text-sm font-medium mb-2 block">
                    Dirección
                  </label>
                  <Input
                    value={formData.direccion}
                    onChange={(e) =>
                      setFormData({ ...formData, direccion: e.target.value })
                    }
                    placeholder="Dirección"
                  />
                </div>

                <div>
                  <label className="text-sm font-medium mb-2 block">
                    Teléfono
                  </label>
                  <Input
                    value={formData.telefono}
                    onChange={(e) =>
                      setFormData({ ...formData, telefono: e.target.value })
                    }
                    placeholder="Teléfono"
                  />
                </div>

                <div>
                  <label className="text-sm font-medium mb-2 block">Email</label>
                  <Input
                    type="email"
                    value={formData.email}
                    onChange={(e) =>
                      setFormData({ ...formData, email: e.target.value })
                    }
                    placeholder="email@ejemplo.com"
                  />
                </div>

                <div>
                  <label className="text-sm font-medium mb-2 block">
                    Persona de Contacto
                  </label>
                  <Input
                    value={formData.contacto}
                    onChange={(e) =>
                      setFormData({ ...formData, contacto: e.target.value })
                    }
                    placeholder="Nombre del contacto"
                  />
                </div>

                <div className="flex gap-2 justify-end pt-4">
                  <Button type="button" variant="outline" onClick={closeModal}>
                    Cancelar
                  </Button>
                  <Button
                    type="submit"
                    disabled={createMutation.isPending || updateMutation.isPending}
                  >
                    {createMutation.isPending || updateMutation.isPending
                      ? 'Guardando...'
                      : editingEmpresa
                      ? 'Guardar Cambios'
                      : 'Crear Empresa'}
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Modal de camiones del cliente */}
      {showCamionesModal && selectedCliente && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <Card className="w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <Car className="h-5 w-5" />
                  Camiones de {selectedCliente.nombre}
                </CardTitle>
                <p className="text-sm text-gray-500 mt-1">
                  Patentes asociadas a este cliente
                </p>
              </div>
              <Button variant="ghost" size="sm" onClick={closeCamionesModal}>
                <X className="h-4 w-4" />
              </Button>
            </CardHeader>
            <CardContent>
              {/* Botón agregar camión */}
              {!showCamionForm && (
                <Button onClick={openCamionCreateForm} className="mb-4">
                  <Plus className="mr-2 h-4 w-4" />
                  Agregar Patente
                </Button>
              )}

              {/* Formulario de camión */}
              {showCamionForm && (
                <Card className="mb-4 bg-gray-50">
                  <CardContent className="pt-4">
                    <form onSubmit={handleCamionSubmit} className="space-y-3">
                      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                        <div>
                          <label className="text-sm font-medium mb-1 block">
                            Patente *
                          </label>
                          <Input
                            value={camionFormData.patente}
                            onChange={(e) =>
                              setCamionFormData({
                                ...camionFormData,
                                patente: e.target.value.toUpperCase(),
                              })
                            }
                            placeholder="ABC123"
                            required
                          />
                        </div>
                        <div>
                          <label className="text-sm font-medium mb-1 block">
                            Descripción
                          </label>
                          <Input
                            value={camionFormData.descripcion}
                            onChange={(e) =>
                              setCamionFormData({
                                ...camionFormData,
                                descripcion: e.target.value,
                              })
                            }
                            placeholder="Camión volcador"
                          />
                        </div>
                        <div>
                          <label className="text-sm font-medium mb-1 block">
                            Chofer Habitual
                          </label>
                          <Input
                            value={camionFormData.chofer_habitual}
                            onChange={(e) =>
                              setCamionFormData({
                                ...camionFormData,
                                chofer_habitual: e.target.value,
                              })
                            }
                            placeholder="Juan Pérez"
                          />
                        </div>
                      </div>
                      <div className="flex gap-2 justify-end">
                        <Button
                          type="button"
                          variant="outline"
                          size="sm"
                          onClick={closeCamionForm}
                        >
                          Cancelar
                        </Button>
                        <Button
                          type="submit"
                          size="sm"
                          disabled={
                            createCamionMutation.isPending ||
                            updateCamionMutation.isPending
                          }
                        >
                          {createCamionMutation.isPending ||
                          updateCamionMutation.isPending
                            ? 'Guardando...'
                            : editingCamion
                            ? 'Actualizar'
                            : 'Agregar'}
                        </Button>
                      </div>
                    </form>
                  </CardContent>
                </Card>
              )}

              {/* Lista de camiones */}
              {loadingCamiones ? (
                <div className="text-center py-8 text-gray-500">
                  Cargando camiones...
                </div>
              ) : camiones && camiones.length > 0 ? (
                <div className="space-y-2">
                  {camiones.map((camion) => (
                    <div
                      key={camion.id}
                      className="flex items-center justify-between p-3 bg-white border rounded-lg hover:bg-gray-50"
                    >
                      <div className="flex items-center gap-3">
                        <div className="bg-blue-100 p-2 rounded">
                          <Car className="h-4 w-4 text-blue-600" />
                        </div>
                        <div>
                          <div className="font-medium">{camion.patente}</div>
                          <div className="text-sm text-gray-500">
                            {camion.descripcion || 'Sin descripción'}
                            {camion.chofer_habitual && (
                              <span className="ml-2">
                                • Chofer: {camion.chofer_habitual}
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center gap-1">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => openCamionEditForm(camion)}
                          title="Editar"
                        >
                          <Pencil className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleDeleteCamion(camion)}
                          className="text-red-600 hover:text-red-700"
                          title="Eliminar"
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500 border rounded-lg">
                  <Car className="h-12 w-12 mx-auto mb-2 text-gray-300" />
                  <p>No hay patentes registradas</p>
                  <p className="text-sm">
                    Agregue las patentes de los camiones de este cliente
                  </p>
                </div>
              )}

              {/* Botón cerrar */}
              <div className="flex justify-end mt-4 pt-4 border-t">
                <Button variant="outline" onClick={closeCamionesModal}>
                  Cerrar
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}
