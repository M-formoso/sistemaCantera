import { API_URL } from '@/constants'

interface RequestConfig {
  params?: Record<string, any>
  responseType?: 'json' | 'blob'
}

// Cliente API usando fetch nativo
const api = {
  async request<T>(method: string, url: string, data?: any, config?: RequestConfig): Promise<{ data: T }> {
    const token = localStorage.getItem('access_token')

    // Construir URL con params
    let fullUrl = `${API_URL}${url}`
    if (config?.params) {
      const searchParams = new URLSearchParams()
      Object.entries(config.params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          searchParams.append(key, String(value))
        }
      })
      const queryString = searchParams.toString()
      if (queryString) {
        fullUrl += (fullUrl.includes('?') ? '&' : '?') + queryString
      }
    }

    console.log('[API] Request:', method, fullUrl)

    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    }
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }

    const response = await fetch(fullUrl, {
      method,
      headers,
      body: data ? JSON.stringify(data) : undefined,
    })

    // Manejar 401 - token expirado
    if (response.status === 401 && !url.includes('/auth/login')) {
      const refreshToken = localStorage.getItem('refresh_token')
      if (refreshToken) {
        try {
          const refreshResponse = await fetch(`${API_URL}/auth/refresh`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ refresh_token: refreshToken }),
          })
          if (refreshResponse.ok) {
            const refreshData = await refreshResponse.json()
            const access_token = refreshData.access_token
            localStorage.setItem('access_token', access_token)
            // Reintentar request original
            headers['Authorization'] = `Bearer ${access_token}`
            const retryResponse = await fetch(fullUrl, {
              method,
              headers,
              body: data ? JSON.stringify(data) : undefined,
            })
            if (!retryResponse.ok) {
              throw new Error('Request failed after token refresh')
            }
            if (config?.responseType === 'blob') {
              const blobData = await retryResponse.blob()
              return { data: blobData as T }
            }
            const retryData = await retryResponse.json().catch(() => ({}))
            return { data: retryData as T }
          }
        } catch {
          localStorage.removeItem('access_token')
          localStorage.removeItem('refresh_token')
          window.location.href = '/login'
        }
      }
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      window.location.href = '/login'
    }

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Error desconocido' }))
      const err = new Error(error.detail || `HTTP ${response.status}`) as any
      err.response = { data: error, status: response.status }
      throw err
    }

    if (config?.responseType === 'blob') {
      const blobData = await response.blob()
      return { data: blobData as T }
    }

    const responseData = await response.json().catch(() => ({}))
    return { data: responseData as T }
  },

  get<T>(url: string, config?: RequestConfig): Promise<{ data: T }> {
    return this.request<T>('GET', url, undefined, config)
  },

  post<T>(url: string, data?: any, config?: RequestConfig): Promise<{ data: T }> {
    return this.request<T>('POST', url, data, config)
  },

  put<T>(url: string, data?: any, config?: RequestConfig): Promise<{ data: T }> {
    return this.request<T>('PUT', url, data, config)
  },

  delete<T>(url: string, config?: RequestConfig): Promise<{ data: T }> {
    return this.request<T>('DELETE', url, undefined, config)
  },
}

export default api

// Helper para manejar errores de API
export function getErrorMessage(error: unknown): string {
  if (error instanceof Error) {
    const err = error as any
    if (err.response?.data?.detail) {
      return err.response.data.detail
    }
    return error.message
  }
  return 'Error desconocido'
}
