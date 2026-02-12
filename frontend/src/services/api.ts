import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios'

// Determinar la URL base de la API
const getApiUrl = () => {
  // En producción, forzar HTTPS
  if (typeof window !== 'undefined' && window.location.protocol === 'https:') {
    const envUrl = import.meta.env.VITE_API_URL || ''
    // Si la URL del env es HTTP, convertirla a HTTPS
    if (envUrl.startsWith('http://')) {
      return envUrl.replace('http://', 'https://')
    }
    return envUrl || 'https://backend-production-ee51.up.railway.app/api/v1'
  }
  return import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'
}

const API_URL = getApiUrl()
console.log('API URL:', API_URL)

// Crear instancia de Axios
const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Interceptor para agregar el token a cada request
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = localStorage.getItem('access_token')
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Interceptor para manejar errores de respuesta
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean }

    // Si es 401 y no es el endpoint de login, intentar refrescar token
    if (error.response?.status === 401 && !originalRequest._retry && !originalRequest.url?.includes('/auth/login')) {
      originalRequest._retry = true

      try {
        const refreshToken = localStorage.getItem('refresh_token')
        if (!refreshToken) {
          throw new Error('No refresh token available')
        }

        const response = await axios.post(
          `${API_URL}/auth/refresh`,
          { refresh_token: refreshToken }
        )

        const { access_token } = response.data
        localStorage.setItem('access_token', access_token)

        // Reintentar request original
        if (originalRequest.headers) {
          originalRequest.headers.Authorization = `Bearer ${access_token}`
        }
        return api(originalRequest)
      } catch (refreshError) {
        // Si falla el refresh, limpiar tokens y redirigir a login
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        window.location.href = '/login'
        return Promise.reject(refreshError)
      }
    }

    return Promise.reject(error)
  }
)

export default api

// Helper para manejar errores de API
export function getErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    return error.response?.data?.detail || error.message || 'Error en la solicitud'
  }
  if (error instanceof Error) {
    return error.message
  }
  return 'Error desconocido'
}
