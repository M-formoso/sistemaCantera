import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Plus, Edit, Trash2, Copy, DollarSign, Package, Check, X,
  ChevronDown, ChevronRight, Save, AlertCircle
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  listasPreciosService,
  ListaPrecio,
  ListaPrecioCreate,
  ItemBatchUpdate,
  ItemListaPrecioCreate
} from '@/services/listasPreciosService'
import { formatNumber } from '@/lib/utils'

// Lista de materiales disponibles
const MATERIALES_DISPONIBLES = [
  '10.30',
  '6.19',
  '0.20',
  '6.12',
  'relleno',
  'binder',
  '0.6',
  'piedra partida',
  'suelo arena',
  'retiro',
]

// Factores de conversión sugeridos
const FACTORES_SUGERIDOS: Record<string, number> = {
  '0.20': 1.66,
  '6.19': 1.5,
}

interface ItemEditable {
  material: string
  precio_unitario: number | ''
  factor_conversion_m3: number | '' | null
  unidad: 'tn' | 'm3'
}

export default function ListasPreciosPage() {
  const queryClient = useQueryClient()

  // Estados
  const [listaExpandida, setListaExpandida] = useState<string | null>(null)
  const [editandoLista, setEditandoLista] = useState<string | null>(null)
  const [editandoItems, setEditandoItems] = useState<string | null>(null)
  const [itemsEditables, setItemsEditables] = useState<ItemEditable[]>([])

  // Modal nueva lista - ahora con items
  const [showNuevaLista, setShowNuevaLista] = useState(false)
  const [nuevaListaNombre, setNuevaListaNombre] = useState('')
  const [nuevaListaDescripcion, setNuevaListaDescripcion] = useState('')
  const [nuevosItems, setNuevosItems] = useState<ItemEditable[]>([])

  // Modal duplicar
  const [showDuplicar, setShowDuplicar] = useState<string | null>(null)
  const [duplicarNombre, setDuplicarNombre] = useState('')

  // Edición inline de nombre
  const [editNombre, setEditNombre] = useState('')
  const [editDescripcion, setEditDescripcion] = useState('')

  // Query para obtener listas
  const { data: listas = [], isLoading } = useQuery({
    queryKey: ['listas-precios'],
    queryFn: () => listasPreciosService.getAll(false),
  })

  // Mutations
  const crearListaMutation = useMutation({
    mutationFn: (data: ListaPrecioCreate) => listasPreciosService.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['listas-precios'] })
      cerrarModalNuevaLista()
    },
  })

  const actualizarListaMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: { nombre?: string; descripcion?: string; activo?: boolean } }) =>
      listasPreciosService.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['listas-precios'] })
      setEditandoLista(null)
    },
  })

  const eliminarListaMutation = useMutation({
    mutationFn: (id: string) => listasPreciosService.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['listas-precios'] })
    },
  })

  const duplicarListaMutation = useMutation({
    mutationFn: ({ id, nuevoNombre }: { id: string; nuevoNombre: string }) =>
      listasPreciosService.duplicar(id, nuevoNombre),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['listas-precios'] })
      setShowDuplicar(null)
      setDuplicarNombre('')
    },
  })

  const actualizarItemsMutation = useMutation({
    mutationFn: ({ listaId, items }: { listaId: string; items: ItemBatchUpdate[] }) =>
      listasPreciosService.actualizarItemsBatch(listaId, items),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['listas-precios'] })
      setEditandoItems(null)
      setItemsEditables([])
    },
  })

  // Inicializar items para nueva lista
  const abrirModalNuevaLista = () => {
    setNuevaListaNombre('')
    setNuevaListaDescripcion('')
    // Crear items vacíos para todos los materiales
    const items: ItemEditable[] = MATERIALES_DISPONIBLES.map((material) => ({
      material,
      precio_unitario: '',
      factor_conversion_m3: FACTORES_SUGERIDOS[material] || null,
      unidad: FACTORES_SUGERIDOS[material] ? 'm3' : 'tn',
    }))
    setNuevosItems(items)
    setShowNuevaLista(true)
  }

  const cerrarModalNuevaLista = () => {
    setShowNuevaLista(false)
    setNuevaListaNombre('')
    setNuevaListaDescripcion('')
    setNuevosItems([])
  }

  // Handlers
  const handleExpandir = (listaId: string) => {
    if (listaExpandida === listaId) {
      setListaExpandida(null)
    } else {
      setListaExpandida(listaId)
    }
  }

  const handleEditarLista = (lista: ListaPrecio) => {
    setEditandoLista(lista.id)
    setEditNombre(lista.nombre)
    setEditDescripcion(lista.descripcion || '')
  }

  const handleGuardarLista = (listaId: string) => {
    actualizarListaMutation.mutate({
      id: listaId,
      data: { nombre: editNombre, descripcion: editDescripcion || undefined },
    })
  }

  const handleToggleActivo = (lista: ListaPrecio) => {
    actualizarListaMutation.mutate({
      id: lista.id,
      data: { activo: !lista.activo },
    })
  }

  const handleEditarItems = (lista: ListaPrecio) => {
    setEditandoItems(lista.id)
    setListaExpandida(lista.id)

    // Crear array con todos los materiales
    const items: ItemEditable[] = MATERIALES_DISPONIBLES.map((material) => {
      const itemExistente = lista.items.find(
        (i) => i.material.toLowerCase() === material.toLowerCase()
      )
      return {
        material,
        precio_unitario: itemExistente?.precio_unitario || '',
        factor_conversion_m3: itemExistente?.factor_conversion_m3 || FACTORES_SUGERIDOS[material] || null,
        unidad: itemExistente?.factor_conversion_m3 || FACTORES_SUGERIDOS[material] ? 'm3' : 'tn',
      }
    })
    setItemsEditables(items)
  }

  const handleItemChange = (
    items: ItemEditable[],
    setItems: React.Dispatch<React.SetStateAction<ItemEditable[]>>,
    index: number,
    field: 'precio_unitario' | 'factor_conversion_m3' | 'unidad',
    value: string
  ) => {
    const newItems = [...items]
    if (field === 'precio_unitario') {
      newItems[index].precio_unitario = value === '' ? '' : parseFloat(value)
    } else if (field === 'factor_conversion_m3') {
      newItems[index].factor_conversion_m3 = value === '' ? null : parseFloat(value)
    } else if (field === 'unidad') {
      newItems[index].unidad = value as 'tn' | 'm3'
      // Si cambia a tn, quitar factor
      if (value === 'tn') {
        newItems[index].factor_conversion_m3 = null
      } else {
        // Si cambia a m3, poner factor sugerido si existe
        newItems[index].factor_conversion_m3 = FACTORES_SUGERIDOS[newItems[index].material] || 1.5
      }
    }
    setItems(newItems)
  }

  const handleGuardarItems = (listaId: string) => {
    // Filtrar solo items con precio
    const itemsConPrecio = itemsEditables
      .filter((item) => item.precio_unitario !== '' && Number(item.precio_unitario) > 0)
      .map((item) => ({
        material: item.material,
        precio_unitario: Number(item.precio_unitario),
        factor_conversion_m3: item.unidad === 'm3' && item.factor_conversion_m3 ? Number(item.factor_conversion_m3) : null,
      }))

    actualizarItemsMutation.mutate({ listaId, items: itemsConPrecio })
  }

  const handleCrearLista = () => {
    if (!nuevaListaNombre.trim()) return

    // Convertir items editables a items de creación
    const itemsConPrecio: ItemListaPrecioCreate[] = nuevosItems
      .filter((item) => item.precio_unitario !== '' && Number(item.precio_unitario) > 0)
      .map((item) => ({
        material: item.material,
        precio_unitario: Number(item.precio_unitario),
        factor_conversion_m3: item.unidad === 'm3' && item.factor_conversion_m3 ? Number(item.factor_conversion_m3) : null,
      }))

    crearListaMutation.mutate({
      nombre: nuevaListaNombre.trim(),
      descripcion: nuevaListaDescripcion.trim() || null,
      activo: true,
      items: itemsConPrecio,
    })
  }

  const handleDuplicar = (listaId: string) => {
    if (!duplicarNombre.trim()) return
    duplicarListaMutation.mutate({ id: listaId, nuevoNombre: duplicarNombre.trim() })
  }

  const handleEliminar = (lista: ListaPrecio) => {
    if (confirm(`¿Eliminar la lista "${lista.nombre}"? Esta acción no se puede deshacer.`)) {
      eliminarListaMutation.mutate(lista.id)
    }
  }

  // Componente de tabla de items reutilizable
  const TablaItemsEditable = ({
    items,
    setItems,
    readOnly = false,
  }: {
    items: ItemEditable[]
    setItems: React.Dispatch<React.SetStateAction<ItemEditable[]>>
    readOnly?: boolean
  }) => (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b bg-gray-50">
            <th className="text-left py-3 px-3 font-semibold">Material</th>
            <th className="text-left py-3 px-3 font-semibold">Unidad</th>
            <th className="text-left py-3 px-3 font-semibold">Precio ($)</th>
            <th className="text-left py-3 px-3 font-semibold">Factor Conversión</th>
          </tr>
        </thead>
        <tbody>
          {items.map((item, index) => (
            <tr key={item.material} className="border-b hover:bg-gray-50">
              <td className="py-3 px-3 font-medium">{item.material}</td>
              <td className="py-3 px-3">
                {readOnly ? (
                  <span className={item.unidad === 'm3' ? 'text-blue-600 font-medium' : 'text-gray-600'}>
                    {item.unidad === 'm3' ? 'm³' : 'Tonelada'}
                  </span>
                ) : (
                  <select
                    value={item.unidad}
                    onChange={(e) => handleItemChange(items, setItems, index, 'unidad', e.target.value)}
                    className="h-9 rounded-md border border-input bg-background px-2 py-1 text-sm"
                  >
                    <option value="tn">Tonelada</option>
                    <option value="m3">m³</option>
                  </select>
                )}
              </td>
              <td className="py-3 px-3">
                {readOnly ? (
                  item.precio_unitario ? (
                    <span className="font-mono">${formatNumber(Number(item.precio_unitario), 2)}</span>
                  ) : (
                    <span className="text-gray-400">-</span>
                  )
                ) : (
                  <Input
                    type="number"
                    step="0.01"
                    value={item.precio_unitario}
                    onChange={(e) => handleItemChange(items, setItems, index, 'precio_unitario', e.target.value)}
                    placeholder="0.00"
                    className="w-32"
                  />
                )}
              </td>
              <td className="py-3 px-3">
                {item.unidad === 'm3' ? (
                  readOnly ? (
                    <span className="bg-blue-100 text-blue-700 px-2 py-0.5 rounded text-xs">
                      ÷ {item.factor_conversion_m3}
                    </span>
                  ) : (
                    <div className="flex items-center gap-2">
                      <Input
                        type="number"
                        step="0.01"
                        value={item.factor_conversion_m3 || ''}
                        onChange={(e) => handleItemChange(items, setItems, index, 'factor_conversion_m3', e.target.value)}
                        placeholder="1.66"
                        className="w-20"
                      />
                      <span className="text-xs text-gray-500">tn ÷ factor = m³</span>
                    </div>
                  )
                ) : (
                  <span className="text-gray-400 text-xs">No aplica</span>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Listas de Precios</h1>
          <p className="text-gray-500 mt-1">
            Gestiona las listas de precios para asignar a clientes en pesajes
          </p>
        </div>
        <Button onClick={abrirModalNuevaLista}>
          <Plus className="h-4 w-4 mr-2" />
          Nueva Lista
        </Button>
      </div>

      {/* Info */}
      <Card className="bg-blue-50 border-blue-200">
        <CardContent className="py-4">
          <div className="flex items-start gap-3">
            <AlertCircle className="h-5 w-5 text-blue-600 mt-0.5" />
            <div className="text-sm text-blue-700">
              <p className="font-medium">Cómo funcionan las unidades</p>
              <p className="mt-1">
                <strong>Tonelada:</strong> El precio se cobra por tonelada pesada directamente.
              </p>
              <p className="mt-1">
                <strong>m³:</strong> Se convierte el peso a metros cúbicos usando el factor. Ej: 20tn ÷ 1.66 = 12.05 m³
              </p>
              <p className="mt-1">
                Factores comunes: <strong>0.20 → 1.66</strong>, <strong>6.19 → 1.5</strong>
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Lista de listas */}
      {listas.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <Package className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900">No hay listas de precios</h3>
            <p className="text-gray-500 mt-2">Crea tu primera lista para comenzar</p>
            <Button onClick={abrirModalNuevaLista} className="mt-4">
              <Plus className="h-4 w-4 mr-2" />
              Crear Lista
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {listas.map((lista) => (
            <Card key={lista.id} className={!lista.activo ? 'opacity-60' : ''}>
              <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <button
                      onClick={() => handleExpandir(lista.id)}
                      className="p-1 hover:bg-gray-100 rounded"
                    >
                      {listaExpandida === lista.id ? (
                        <ChevronDown className="h-5 w-5 text-gray-500" />
                      ) : (
                        <ChevronRight className="h-5 w-5 text-gray-500" />
                      )}
                    </button>

                    {editandoLista === lista.id ? (
                      <div className="flex items-center gap-2">
                        <Input
                          value={editNombre}
                          onChange={(e) => setEditNombre(e.target.value)}
                          className="w-48"
                          placeholder="Nombre"
                        />
                        <Input
                          value={editDescripcion}
                          onChange={(e) => setEditDescripcion(e.target.value)}
                          className="w-64"
                          placeholder="Descripción (opcional)"
                        />
                        <Button
                          size="sm"
                          onClick={() => handleGuardarLista(lista.id)}
                          disabled={actualizarListaMutation.isPending}
                        >
                          <Check className="h-4 w-4" />
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => setEditandoLista(null)}
                        >
                          <X className="h-4 w-4" />
                        </Button>
                      </div>
                    ) : (
                      <div>
                        <CardTitle className="flex items-center gap-2">
                          <DollarSign className="h-5 w-5 text-green-600" />
                          {lista.nombre}
                          {!lista.activo && (
                            <span className="text-xs bg-gray-200 text-gray-600 px-2 py-0.5 rounded">
                              Inactiva
                            </span>
                          )}
                        </CardTitle>
                        {lista.descripcion && (
                          <p className="text-sm text-gray-500 mt-1">{lista.descripcion}</p>
                        )}
                      </div>
                    )}
                  </div>

                  <div className="flex items-center gap-2">
                    <span className="text-sm text-gray-500 mr-2">
                      {lista.items.length} materiales
                    </span>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleEditarLista(lista)}
                      title="Editar nombre"
                    >
                      <Edit className="h-4 w-4" />
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => {
                        setShowDuplicar(lista.id)
                        setDuplicarNombre(`${lista.nombre} (copia)`)
                      }}
                      title="Duplicar lista"
                    >
                      <Copy className="h-4 w-4" />
                    </Button>
                    <Button
                      size="sm"
                      variant={lista.activo ? 'outline' : 'default'}
                      onClick={() => handleToggleActivo(lista)}
                      title={lista.activo ? 'Desactivar' : 'Activar'}
                    >
                      {lista.activo ? 'Desactivar' : 'Activar'}
                    </Button>
                    <Button
                      size="sm"
                      variant="destructive"
                      onClick={() => handleEliminar(lista)}
                      title="Eliminar lista"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </CardHeader>

              {/* Items expandidos */}
              {listaExpandida === lista.id && (
                <CardContent>
                  <div className="border-t pt-4">
                    <div className="flex items-center justify-between mb-4">
                      <h4 className="font-medium text-gray-700">Precios por Material</h4>
                      {editandoItems !== lista.id ? (
                        <Button
                          size="sm"
                          onClick={() => handleEditarItems(lista)}
                        >
                          <Edit className="h-4 w-4 mr-2" />
                          Editar Precios
                        </Button>
                      ) : (
                        <div className="flex gap-2">
                          <Button
                            size="sm"
                            onClick={() => handleGuardarItems(lista.id)}
                            disabled={actualizarItemsMutation.isPending}
                          >
                            <Save className="h-4 w-4 mr-2" />
                            {actualizarItemsMutation.isPending ? 'Guardando...' : 'Guardar'}
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => {
                              setEditandoItems(null)
                              setItemsEditables([])
                            }}
                          >
                            Cancelar
                          </Button>
                        </div>
                      )}
                    </div>

                    {editandoItems === lista.id ? (
                      <TablaItemsEditable
                        items={itemsEditables}
                        setItems={setItemsEditables}
                      />
                    ) : (
                      // Modo visualización
                      <div className="overflow-x-auto">
                        {lista.items.length === 0 ? (
                          <p className="text-gray-500 text-center py-4">
                            No hay precios configurados. Haz clic en "Editar Precios" para agregar.
                          </p>
                        ) : (
                          <table className="w-full text-sm">
                            <thead>
                              <tr className="border-b bg-gray-50">
                                <th className="text-left py-3 px-3 font-semibold">Material</th>
                                <th className="text-left py-3 px-3 font-semibold">Unidad</th>
                                <th className="text-right py-3 px-3 font-semibold">Precio</th>
                                <th className="text-center py-3 px-3 font-semibold">Factor</th>
                              </tr>
                            </thead>
                            <tbody>
                              {lista.items.map((item) => (
                                <tr key={item.id} className="border-b hover:bg-gray-50">
                                  <td className="py-3 px-3 font-medium">{item.material}</td>
                                  <td className="py-3 px-3">
                                    {item.factor_conversion_m3 ? (
                                      <span className="text-blue-600 font-medium">m³</span>
                                    ) : (
                                      <span className="text-gray-600">Tonelada</span>
                                    )}
                                  </td>
                                  <td className="py-3 px-3 text-right font-mono">
                                    ${formatNumber(item.precio_unitario, 2)}
                                  </td>
                                  <td className="py-3 px-3 text-center">
                                    {item.factor_conversion_m3 ? (
                                      <span className="bg-blue-100 text-blue-700 px-2 py-0.5 rounded text-xs">
                                        ÷ {item.factor_conversion_m3}
                                      </span>
                                    ) : (
                                      <span className="text-gray-400">-</span>
                                    )}
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        )}
                      </div>
                    )}
                  </div>
                </CardContent>
              )}
            </Card>
          ))}
        </div>
      )}

      {/* Modal Nueva Lista - COMPLETO */}
      {showNuevaLista && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <Card className="w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">
            <CardHeader className="border-b">
              <CardTitle className="flex items-center gap-2">
                <Plus className="h-5 w-5" />
                Nueva Lista de Precios
              </CardTitle>
            </CardHeader>
            <CardContent className="flex-1 overflow-y-auto p-6 space-y-6">
              {/* Nombre y descripción */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium mb-2 block">Nombre de la lista *</label>
                  <Input
                    value={nuevaListaNombre}
                    onChange={(e) => setNuevaListaNombre(e.target.value)}
                    placeholder="Ej: Lista Mayorista, Lista 2024"
                    autoFocus
                  />
                </div>
                <div>
                  <label className="text-sm font-medium mb-2 block">Descripción (opcional)</label>
                  <Input
                    value={nuevaListaDescripcion}
                    onChange={(e) => setNuevaListaDescripcion(e.target.value)}
                    placeholder="Descripción de la lista"
                  />
                </div>
              </div>

              {/* Tabla de materiales */}
              <div>
                <h3 className="text-sm font-semibold text-gray-700 mb-3">
                  Precios por Material
                </h3>
                <p className="text-xs text-gray-500 mb-4">
                  Completa los precios para los materiales que desees incluir. Los materiales sin precio no se guardarán.
                </p>
                <TablaItemsEditable
                  items={nuevosItems}
                  setItems={setNuevosItems}
                />
              </div>
            </CardContent>

            {/* Footer con botones */}
            <div className="border-t p-4 bg-gray-50 flex justify-between items-center">
              <p className="text-sm text-gray-500">
                {nuevosItems.filter(i => i.precio_unitario !== '' && Number(i.precio_unitario) > 0).length} materiales con precio
              </p>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  onClick={cerrarModalNuevaLista}
                >
                  Cancelar
                </Button>
                <Button
                  onClick={handleCrearLista}
                  disabled={!nuevaListaNombre.trim() || crearListaMutation.isPending}
                >
                  {crearListaMutation.isPending ? 'Creando...' : 'Crear Lista de Precios'}
                </Button>
              </div>
            </div>
          </Card>
        </div>
      )}

      {/* Modal Duplicar */}
      {showDuplicar && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <Card className="w-full max-w-md">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Copy className="h-5 w-5" />
                Duplicar Lista
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="text-sm font-medium mb-2 block">Nombre para la nueva lista *</label>
                <Input
                  value={duplicarNombre}
                  onChange={(e) => setDuplicarNombre(e.target.value)}
                  placeholder="Nombre de la copia"
                  autoFocus
                />
              </div>
              <div className="flex gap-2 justify-end pt-4">
                <Button
                  variant="outline"
                  onClick={() => {
                    setShowDuplicar(null)
                    setDuplicarNombre('')
                  }}
                >
                  Cancelar
                </Button>
                <Button
                  onClick={() => handleDuplicar(showDuplicar)}
                  disabled={!duplicarNombre.trim() || duplicarListaMutation.isPending}
                >
                  {duplicarListaMutation.isPending ? 'Duplicando...' : 'Duplicar'}
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}
