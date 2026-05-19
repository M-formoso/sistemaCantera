import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  ColumnDef,
  flexRender,
  getCoreRowModel,
  useReactTable,
  getSortedRowModel,
  SortingState,
  getFilteredRowModel,
  getPaginationRowModel,
  ColumnFiltersState,
} from '@tanstack/react-table'
import { Building2, Plus, Pencil, Trash2, Truck, UserCheck, Car, X, ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight, DollarSign, RotateCcw, Archive, ListOrdered, Check } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { empresasService, CamionCliente, CamionClienteCreate } from '@/services/empresasService'
import { listasPreciosService } from '@/services/listasPreciosService'
import { Empresa, EmpresaCreate, TipoEmpresa } from '@/types'
import { useIsAdmin } from '@/hooks/useIsAdmin'

export default function EmpresasPage() {
  const queryClient = useQueryClient()
  const isAdmin = useIsAdmin()
  const [sorting, setSorting] = useState<SortingState>([])
  const [columnFilters, setColumnFilters] = useState<ColumnFiltersState>([])
  const [filtroTipo, setFiltroTipo] = useState<TipoEmpresa | 'todos'>('todos')
  const [mostrarInactivos, setMostrarInactivos] = useState(false)
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

  // Estado para gestión de precios (listas de precios)
  const [showPreciosModal, setShowPreciosModal] = useState(false)
  const [listaSeleccionada, setListaSeleccionada] = useState<string | null>(null)
  const [guardandoPrecios, setGuardandoPrecios] = useState(false)

  useEffect(() => {
    if (!showPreciosModal) return
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') closePreciosModal()
    }
    window.addEventListener('keydown', handleKey)
    return () => window.removeEventListener('keydown', handleKey)
  }, [showPreciosModal])

  const { data: empresas, isLoading } = useQuery({
    queryKey: ['empresas', filtroTipo, mostrarInactivos],
    queryFn: () =>
      filtroTipo === 'todos'
        ? empresasService.getAll(undefined, !mostrarInactivos)
        : empresasService.getAll(filtroTipo, !mostrarInactivos),
  })

  // Query para listas de precios
  const { data: listasPrecios = [] } = useQuery({
    queryKey: ['listas-precios-resumen'],
    queryFn: () => listasPreciosService.getResumen(true),
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

  const reactivarMutation = useMutation({
    mutationFn: (id: string) => empresasService.reactivar(id),
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

  // Funciones para modal de precios (asignar lista de precios)
  const openPreciosModal = (empresa: Empresa) => {
    setSelectedCliente(empresa)
    setListaSeleccionada(empresa.lista_precio_id || null)
    setShowPreciosModal(true)
    setGuardandoPrecios(false)
  }

  const closePreciosModal = () => {
    setShowPreciosModal(false)
    setSelectedCliente(null)
    setListaSeleccionada(null)
  }

  const handleGuardarListaPrecio = async () => {
    if (!selectedCliente) return

    setGuardandoPrecios(true)

    try {
      await empresasService.asignarListaPrecio(selectedCliente.id, listaSeleccionada)
      queryClient.invalidateQueries({ queryKey: ['empresas'] })
      alert(listaSeleccionada ? 'Lista de precios asignada correctamente' : 'Lista de precios removida')
      closePreciosModal()
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Error al asignar lista de precios')
    } finally {
      setGuardandoPrecios(false)
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
    if (window.confirm(`¿Está seguro de desactivar "${nombre}"?\n\nLa empresa quedará inactiva pero podrá reactivarla desde la sección "Ver desactivados".`)) {
      try {
        await deleteMutation.mutateAsync(id)
      } catch (error: any) {
        alert(error.response?.data?.detail || 'Error al desactivar')
      }
    }
  }

  const handleReactivar = async (id: string, nombre: string) => {
    if (window.confirm(`¿Desea reactivar "${nombre}"?`)) {
      try {
        await reactivarMutation.mutateAsync(id)
      } catch (error: any) {
        alert(error.response?.data?.detail || 'Error al reactivar')
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
        const esInactivo = !empresa.activo

        // Si está inactivo, mostrar solo botón de reactivar
        if (esInactivo) {
          return (
            <div className="flex items-center gap-2">
              {isAdmin && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleReactivar(empresa.id, empresa.nombre)}
                  className="text-green-600 hover:text-green-700"
                  title="Reactivar"
                >
                  <RotateCcw className="h-4 w-4" />
                </Button>
              )}
            </div>
          )
        }

        return (
          <div className="flex items-center gap-2">
            {empresa.tipo === 'cliente' && (
              <>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => openPreciosModal(empresa)}
                  title="Configurar Precios"
                  className="text-green-600 hover:text-green-700"
                >
                  <DollarSign className="h-4 w-4" />
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => openCamionesModal(empresa)}
                  title="Ver Camiones/Patentes"
                  className="text-blue-600 hover:text-blue-700"
                >
                  <Car className="h-4 w-4" />
                </Button>
              </>
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
                className="text-orange-600 hover:text-orange-700"
                title="Desactivar"
              >
                <Archive className="h-4 w-4" />
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
    getPaginationRowModel: getPaginationRowModel(),
    onSortingChange: setSorting,
    onColumnFiltersChange: setColumnFilters,
    state: {
      sorting,
      columnFilters,
    },
    initialState: {
      pagination: {
        pageSize: 10,
      },
    },
  })

  const currentPage = table.getState().pagination.pageIndex + 1
  const totalPages = table.getPageCount()
  const pageSize = table.getState().pagination.pageSize
  const totalRows = table.getFilteredRowModel().rows.length

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
            <div className="flex gap-2 flex-wrap">
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
              <div className="border-l mx-2" />
              <Button
                variant={mostrarInactivos ? 'default' : 'outline'}
                onClick={() => setMostrarInactivos(!mostrarInactivos)}
                size="sm"
                className={mostrarInactivos ? 'bg-orange-600 hover:bg-orange-700' : ''}
              >
                <Archive className="mr-1 h-4 w-4" />
                {mostrarInactivos ? 'Mostrando desactivados' : 'Ver desactivados'}
              </Button>
            </div>
          </div>
          {mostrarInactivos && (
            <div className="mt-3 p-2 bg-orange-50 border border-orange-200 rounded-md text-sm text-orange-700">
              <Archive className="h-4 w-4 inline mr-1" />
              Mostrando empresas desactivadas. Puede reactivarlas usando el botón <RotateCcw className="h-3 w-3 inline mx-1" /> en la columna de acciones.
            </div>
          )}
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

          {/* Paginación */}
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4 p-4 border-t">
            <div className="flex items-center gap-4 text-sm text-gray-600">
              <span>
                Mostrando {table.getRowModel().rows.length} de {totalRows}
              </span>
              <div className="flex items-center gap-2">
                <span>Por página:</span>
                <select
                  value={pageSize}
                  onChange={(e) => table.setPageSize(Number(e.target.value))}
                  className="h-8 rounded-md border border-input bg-background px-2 text-sm"
                >
                  {[10, 25, 50, 100].map((size) => (
                    <option key={size} value={size}>{size}</option>
                  ))}
                </select>
              </div>
            </div>

            {totalPages > 1 && (
              <div className="flex items-center gap-1">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => table.setPageIndex(0)}
                  disabled={!table.getCanPreviousPage()}
                  className="h-8 w-8 p-0"
                >
                  <ChevronsLeft className="h-4 w-4" />
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => table.previousPage()}
                  disabled={!table.getCanPreviousPage()}
                  className="h-8 w-8 p-0"
                >
                  <ChevronLeft className="h-4 w-4" />
                </Button>

                <span className="px-2 text-sm text-muted-foreground">
                  Página {currentPage} de {totalPages}
                </span>

                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => table.nextPage()}
                  disabled={!table.getCanNextPage()}
                  className="h-8 w-8 p-0"
                >
                  <ChevronRight className="h-4 w-4" />
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => table.setPageIndex(table.getPageCount() - 1)}
                  disabled={!table.getCanNextPage()}
                  className="h-8 w-8 p-0"
                >
                  <ChevronsRight className="h-4 w-4" />
                </Button>
              </div>
            )}
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

      {/* Modal de precios del cliente (seleccionar lista de precios) */}
      {showPreciosModal && selectedCliente && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
          onClick={closePreciosModal}
        >
          <Card
            className="w-full max-w-md flex flex-col max-h-[75vh]"
            onClick={(e) => e.stopPropagation()}
          >
            <CardHeader className="flex flex-row items-center justify-between flex-shrink-0 border-b p-4 space-y-0">
              <div className="min-w-0">
                <CardTitle className="flex items-center gap-2 text-base">
                  <ListOrdered className="h-4 w-4" />
                  Lista de Precios
                </CardTitle>
                <p className="text-xs text-gray-500 mt-0.5 truncate">
                  {selectedCliente.nombre}
                  {selectedCliente.lista_precio_nombre && (
                    <span className="ml-1">· Actual: <span className="font-medium text-gray-700">{selectedCliente.lista_precio_nombre}</span></span>
                  )}
                </p>
              </div>
              <Button variant="ghost" size="sm" onClick={closePreciosModal} className="flex-shrink-0">
                <X className="h-4 w-4" />
              </Button>
            </CardHeader>
            <CardContent className="flex-1 overflow-y-auto p-4">
              {/* Selector de lista */}
              {listasPrecios.length > 0 ? (
                <div className="space-y-1.5">
                  {/* Opción: Sin lista */}
                  <button
                    type="button"
                    onClick={() => setListaSeleccionada(null)}
                    className={`w-full px-3 py-2 rounded-md border text-left flex items-center justify-between transition-colors ${
                      listaSeleccionada === null
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-200 hover:bg-gray-50'
                    }`}
                  >
                    <div className="min-w-0">
                      <p className="text-sm font-medium text-gray-700">Sin lista de precios</p>
                      <p className="text-xs text-gray-500 truncate">Ingresar precios manualmente</p>
                    </div>
                    {listaSeleccionada === null && (
                      <Check className="h-4 w-4 text-blue-600 flex-shrink-0 ml-2" />
                    )}
                  </button>

                  {/* Listas disponibles */}
                  {listasPrecios.map((lista) => (
                    <button
                      key={lista.id}
                      type="button"
                      onClick={() => setListaSeleccionada(lista.id)}
                      className={`w-full px-3 py-2 rounded-md border text-left flex items-center justify-between transition-colors ${
                        listaSeleccionada === lista.id
                          ? 'border-green-500 bg-green-50'
                          : 'border-gray-200 hover:bg-gray-50'
                      }`}
                    >
                      <div className="min-w-0">
                        <p className="text-sm font-medium truncate">{lista.nombre}</p>
                        <p className="text-xs text-gray-500 truncate">
                          {lista.cantidad_items} materiales
                          {lista.descripcion && ` • ${lista.descripcion}`}
                        </p>
                      </div>
                      {listaSeleccionada === lista.id && (
                        <Check className="h-4 w-4 text-green-600 flex-shrink-0 ml-2" />
                      )}
                    </button>
                  ))}
                </div>
              ) : (
                <div className="text-center py-6 text-gray-500 border rounded-lg">
                  <ListOrdered className="h-10 w-10 mx-auto mb-2 text-gray-300" />
                  <p className="text-sm">No hay listas de precios creadas</p>
                  <a
                    href="/listas-precios"
                    className="text-blue-600 underline text-sm mt-2 inline-block"
                  >
                    Crear lista de precios
                  </a>
                </div>
              )}
            </CardContent>

            {/* Botones (footer fijo, siempre visible) */}
            <div className="flex justify-end gap-2 px-4 py-3 border-t bg-white rounded-b-lg flex-shrink-0">
              <Button variant="outline" size="sm" onClick={closePreciosModal}>
                Cancelar
              </Button>
              <Button size="sm" onClick={handleGuardarListaPrecio} disabled={guardandoPrecios}>
                {guardandoPrecios ? 'Guardando...' : 'Guardar'}
              </Button>
            </div>
          </Card>
        </div>
      )}
    </div>
  )
}
