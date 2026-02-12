// Cliente API usando fetch nativo con URL hardcodeada
const BASE_URL = 'https://backend-production-ee51.up.railway.app/api/v1'

interface RequestConfig {
  params?: Record<string, any>
  responseType?: 'json' | 'blob'
}

function buildUrl(endpoint: string, params?: Record<string, any>): string {
  // Estos endpoints NO llevan barra
  let normalizedEndpoint = endpoint
  const noSlash = endpoint.startsWith('/auth') ||
                  endpoint.startsWith('/dashboard') ||
                  endpoint.startsWith('/combustible') ||
                  endpoint.startsWith('/usuarios')

  if (!noSlash && !endpoint.endsWith('/') && !endpoint.includes('?')) {
    normalizedEndpoint = endpoint + '/'
  }

  let url = `${BASE_URL}${normalizedEndpoint}`
  if (params) {
    const searchParams = new URLSearchParams()
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        searchParams.append(key, String(value))
      }
    })
    const queryString = searchParams.toString()
    if (queryString) {
      url += (url.includes('?') ? '&' : '?') + queryString
    }
  }
  return url
}

async function request<T>(method: string, endpoint: string, data?: any, config?: RequestConfig): Promise<{ data: T }> {
  const token = localStorage.getItem('access_token')
  const url = buildUrl(endpoint, config?.params)

  console.log('[API] Fetching:', method, url)

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  }
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  const response = await fetch(url, {
    method,
    headers,
    body: data ? JSON.stringify(data) : undefined,
  })

  // Manejar 401 - token expirado
  if (response.status === 401 && !endpoint.includes('/auth/login')) {
    const refreshToken = localStorage.getItem('refresh_token')
    if (refreshToken) {
      try {
        const refreshResponse = await fetch(`${BASE_URL}/auth/refresh`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ refresh_token: refreshToken }),
        })
        if (refreshResponse.ok) {
          const refreshData = await refreshResponse.json()
          localStorage.setItem('access_token', refreshData.access_token)
          headers['Authorization'] = `Bearer ${refreshData.access_token}`
          const retryResponse = await fetch(url, {
            method,
            headers,
            body: data ? JSON.stringify(data) : undefined,
          })
          if (config?.responseType === 'blob') {
            return { data: await retryResponse.blob() as T }
          }
          return { data: await retryResponse.json().catch(() => ({})) as T }
        }
      } catch {
        // Ignore
      }
    }
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    window.location.href = '/login'
    throw new Error('Unauthorized')
  }

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Error desconocido' }))
    const err = new Error(error.detail || `HTTP ${response.status}`) as any
    err.response = { data: error, status: response.status }
    throw err
  }

  if (config?.responseType === 'blob') {
    return { data: await response.blob() as T }
  }

  return { data: await response.json().catch(() => ({})) as T }
}

const api = {
  get<T>(endpoint: string, config?: RequestConfig): Promise<{ data: T }> {
    return request<T>('GET', endpoint, undefined, config)
  },
  post<T>(endpoint: string, data?: any, config?: RequestConfig): Promise<{ data: T }> {
    return request<T>('POST', endpoint, data, config)
  },
  put<T>(endpoint: string, data?: any, config?: RequestConfig): Promise<{ data: T }> {
    return request<T>('PUT', endpoint, data, config)
  },
  delete<T>(endpoint: string, config?: RequestConfig): Promise<{ data: T }> {
    return request<T>('DELETE', endpoint, undefined, config)
  },
}

export default api

export function getErrorMessage(error: unknown): string {
  if (error instanceof Error) {
    const err = error as any
    return err.response?.data?.detail || error.message
  }
  return 'Error desconocido'
}
