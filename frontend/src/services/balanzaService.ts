/**
 * Servicio para comunicarse con el servidor local de la balanza.
 * El servidor corre en la PC donde está conectada la balanza.
 */

const BALANZA_URL = 'http://localhost:5555'

export interface PesoBalanza {
  peso: number
  unidad: string
  conectado: boolean
  timestamp: number | null
  error: string | null
}

export interface StatusBalanza {
  conectado: boolean
  error: string | null
}

export interface PuertoCOM {
  puerto: string
  descripcion: string
}

export const balanzaService = {
  /**
   * Obtiene el peso actual de la balanza
   */
  async getPeso(): Promise<PesoBalanza> {
    try {
      const response = await fetch(`${BALANZA_URL}/peso`, {
        method: 'GET',
        signal: AbortSignal.timeout(2000), // Timeout de 2 segundos
      })

      if (!response.ok) {
        throw new Error('Error al leer balanza')
      }

      return await response.json()
    } catch (error: any) {
      // Si no puede conectar, el servidor de balanza no está corriendo
      return {
        peso: 0,
        unidad: 'kg',
        conectado: false,
        timestamp: null,
        error: error.name === 'TimeoutError'
          ? 'Servidor de balanza no responde. Verifique que esté ejecutándose.'
          : 'No se puede conectar al servidor de balanza. Ejecute iniciar_balanza.bat',
      }
    }
  },

  /**
   * Verifica si el servidor de balanza está corriendo y conectado
   */
  async getStatus(): Promise<StatusBalanza> {
    try {
      const response = await fetch(`${BALANZA_URL}/status`, {
        method: 'GET',
        signal: AbortSignal.timeout(2000),
      })

      if (!response.ok) {
        throw new Error('Error al verificar estado')
      }

      return await response.json()
    } catch {
      return {
        conectado: false,
        error: 'Servidor de balanza no disponible',
      }
    }
  },

  /**
   * Lista los puertos COM disponibles
   */
  async getPuertos(): Promise<PuertoCOM[]> {
    try {
      const response = await fetch(`${BALANZA_URL}/puertos`, {
        method: 'GET',
        signal: AbortSignal.timeout(2000),
      })

      if (!response.ok) {
        throw new Error('Error al listar puertos')
      }

      return await response.json()
    } catch {
      return []
    }
  },
}
