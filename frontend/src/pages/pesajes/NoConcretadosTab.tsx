import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ColumnDef } from '@tanstack/react-table'
import { Trash2, AlertTriangle, Clock, XCircle } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { DataTable } from '@/components/ui/data-table'
import { pesajesService } from '@/services/pesajesService'
import { Pesaje } from '@/types'
import { formatDate, formatNumber } from '@/lib/utils'
import { useIsAdmin } from '@/hooks/useIsAdmin'

export default function NoConcretadosTab() {
  const queryClient = useQueryClient()
  const isAdmin = useIsAdmin()
  const [confirmDelete, setConfirmDelete] = useState<{ id: string; numero: number } | null>(null)

  // Query para pesajes no concretados
  const { data: pesajes = [], isLoading } = useQuery({
    queryKey: ['pesajes-no-concretados'],
    queryFn: () => pesajesService.getNoConcretados(0, 500),
  })

  // Mutation para eliminar definitivamente
  const deleteMutation = useMutation({
    mutationFn: (id: string) => pesajesService.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pesajes-no-concretados'] })
      queryClient.invalidateQueries({ queryKey: ['pesajes'] })
      setConfirmDelete(null)
    },
  })

  const handleDeleteDefinitivo = async (id: string) => {
    try {
      await deleteMutation.mutateAsync(id)
    } catch (error) {
      alert('Error al eliminar el pesaje')
    }
  }

  // Columnas
  const columns: ColumnDef<Pesaje>[] = [
    {
      accessorKey: 'numero_pesaje',
      header: '#',
      cell: ({ row }) => (
        <div className="font-medium">#{row.getValue('numero_pesaje')}</div>
      ),
    },
    {
      accessorKey: 'estado',
      header: 'Estado',
      cell: ({ row }) => {
        const estado = row.original.estado
        const estilos = {
          cancelado: 'bg-red-100 text-red-700',
          expirado: 'bg-orange-100 text-orange-700',
        }
        const iconos = {
          cancelado: <XCircle className="h-3 w-3" />,
          expirado: <Clock className="h-3 w-3" />,
        }
        const etiquetas = {
          cancelado: 'Cancelado',
          expirado: 'Expirado',
        }
        return (
          <span className={`inline-flex items-center gap-1 px-2 py-1 text-xs font-semibold rounded ${
            estilos[estado as keyof typeof estilos] || 'bg-gray-100 text-gray-700'
          }`}>
            {iconos[estado as keyof typeof iconos]}
            {etiquetas[estado as keyof typeof etiquetas] || estado}
          </span>
        )
      },
    },
    {
      accessorKey: 'fecha',
      header: 'Fecha Creación',
      cell: ({ row }) => {
        const fecha = row.getValue('fecha') as string
        return <div className="text-sm">{formatDate(fecha)}</div>
      },
    },
    {
      accessorKey: 'fecha_cancelacion',
      header: 'Fecha Cancelación/Expiración',
      cell: ({ row }) => {
        const fecha = row.original.fecha_cancelacion
        return <div className="text-sm">{fecha ? formatDate(fecha) : '-'}</div>
      },
    },
    {
      accessorKey: 'patente',
      accessorFn: (row) => row.camion_patente || row.patente_externa || '',
      header: 'Patente',
      cell: ({ row }) => {
        const patente = row.getValue('patente') as string
        return <div className="font-medium">{patente || '-'}</div>
      },
    },
    {
      accessorKey: 'cliente_nombre',
      header: 'Cliente',
      cell: ({ row }) => {
        const cliente = row.getValue('cliente_nombre') as string
        return <div className="text-sm">{cliente || '-'}</div>
      },
    },
    {
      accessorKey: 'peso_tara',
      header: 'Tara',
      cell: ({ row }) => {
        const pesoTara = row.original.peso_tara as number
        return (
          <div className="text-sm text-right">
            {pesoTara ? `${formatNumber(pesoTara)} kg` : '-'}
          </div>
        )
      },
    },
    {
      accessorKey: 'motivo_cancelacion',
      header: 'Motivo',
      cell: ({ row }) => {
        const motivo = row.original.motivo_cancelacion
        return (
          <div className="text-sm text-gray-600 max-w-[200px] truncate" title={motivo || ''}>
            {motivo || '-'}
          </div>
        )
      },
    },
    {
      id: 'actions',
      header: 'Acciones',
      cell: ({ row }) => {
        const pesaje = row.original

        return (
          <div className="flex items-center gap-1">
            {isAdmin && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => setConfirmDelete({ id: pesaje.id, numero: pesaje.numero_pesaje })}
                disabled={deleteMutation.isPending}
                title="Eliminar definitivamente"
                className="text-red-600 hover:text-red-700 hover:bg-red-50"
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            )}
          </div>
        )
      },
    },
  ]

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-gray-500">Cargando pesajes no concretados...</div>
      </div>
    )
  }

  const totalExpirados = pesajes.filter(p => p.estado === 'expirado').length
  const totalCancelados = pesajes.filter(p => p.estado === 'cancelado').length

  return (
    <div className="space-y-6">
      {/* Info */}
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 flex items-start gap-3">
        <AlertTriangle className="h-5 w-5 text-yellow-600 flex-shrink-0 mt-0.5" />
        <div className="text-sm text-yellow-800">
          <p className="font-medium">Pesajes No Concretados</p>
          <p className="mt-1">
            Esta sección muestra los pesajes que fueron <strong>cancelados</strong> manualmente
            o que <strong>expiraron</strong> automáticamente por no completarse en 7 días.
            Desde aquí puedes eliminarlos definitivamente si es necesario.
          </p>
        </div>
      </div>

      {/* Estadísticas */}
      <div className="grid grid-cols-1 gap-3 sm:gap-4 sm:grid-cols-3">
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">Total No Concretados</div>
            <div className="text-2xl font-bold text-gray-700">{pesajes.length}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground flex items-center gap-1">
              <Clock className="h-4 w-4 text-orange-500" />
              Expirados
            </div>
            <div className="text-2xl font-bold text-orange-600">{totalExpirados}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground flex items-center gap-1">
              <XCircle className="h-4 w-4 text-red-500" />
              Cancelados
            </div>
            <div className="text-2xl font-bold text-red-600">{totalCancelados}</div>
          </CardContent>
        </Card>
      </div>

      {/* Tabla */}
      <Card>
        <CardHeader className="px-3 sm:px-6">
          <CardTitle className="text-lg sm:text-xl">Lista de Pesajes No Concretados</CardTitle>
        </CardHeader>
        <CardContent className="px-3 sm:px-6">
          {pesajes.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              <AlertTriangle className="h-12 w-12 mx-auto mb-4 text-gray-300" />
              <p>No hay pesajes cancelados o expirados</p>
            </div>
          ) : (
            <DataTable
              columns={columns}
              data={pesajes}
              searchPlaceholder="Buscar por patente, cliente..."
              defaultPageSize={10}
            />
          )}
        </CardContent>
      </Card>

      {/* Modal de confirmación de eliminación definitiva */}
      {confirmDelete && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <Card className="w-full max-w-md">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-red-600">
                <AlertTriangle className="h-5 w-5" />
                Eliminar Definitivamente
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-gray-700">
                ¿Estás seguro de eliminar <strong>definitivamente</strong> el pesaje <strong>#{confirmDelete.numero}</strong>?
              </p>
              <p className="text-sm text-red-600 bg-red-50 p-3 rounded">
                Esta acción no se puede deshacer. El pesaje se eliminará permanentemente de la base de datos.
              </p>
              <div className="flex justify-end gap-3">
                <Button
                  variant="outline"
                  onClick={() => setConfirmDelete(null)}
                  disabled={deleteMutation.isPending}
                >
                  Cancelar
                </Button>
                <Button
                  variant="destructive"
                  onClick={() => handleDeleteDefinitivo(confirmDelete.id)}
                  disabled={deleteMutation.isPending}
                >
                  {deleteMutation.isPending ? 'Eliminando...' : 'Eliminar Definitivamente'}
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}
