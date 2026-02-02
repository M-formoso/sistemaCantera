import api from './api'
import { DashboardResumen, EstadisticasMes } from '@/types'

export const dashboardService = {
  /**
   * Obtiene el resumen del día
   */
  async getResumenDia(): Promise<DashboardResumen> {
    const response = await api.get<DashboardResumen>('/dashboard/resumen-dia')
    return response.data
  },

  /**
   * Obtiene estadísticas del mes
   */
  async getEstadisticasMes(): Promise<EstadisticasMes> {
    const response = await api.get<EstadisticasMes>('/dashboard/estadisticas-mes')
    return response.data
  },
}
