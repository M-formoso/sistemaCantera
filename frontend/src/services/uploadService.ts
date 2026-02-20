const BASE_URL = 'https://backend-production-ee51.up.railway.app/api/v1'

export interface UploadResult {
  url: string
  public_id: string
  formato: string
  tamaño: number
  nombre_original: string
  content_type: string
  equipo_id?: string
  tipo_documento?: string
}

/**
 * Helper para hacer requests de upload con FormData
 */
async function uploadRequest<T>(endpoint: string, formData: FormData): Promise<T> {
  const token = localStorage.getItem('access_token')

  const headers: Record<string, string> = {}
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }
  // NO incluir Content-Type - el browser lo setea automáticamente con el boundary

  const response = await fetch(`${BASE_URL}${endpoint}`, {
    method: 'POST',
    headers,
    body: formData,
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Error al subir archivo' }))
    const err = new Error(error.detail || `HTTP ${response.status}`) as Error & { response?: { data: unknown } }
    err.response = { data: error }
    throw err
  }

  return response.json()
}

/**
 * Sube un documento general
 */
export const uploadDocumento = async (file: File, folder?: string): Promise<UploadResult> => {
  const formData = new FormData()
  formData.append('file', file)
  if (folder) {
    formData.append('folder', folder)
  }

  return uploadRequest<UploadResult>('/upload/documento', formData)
}

/**
 * Sube una imagen
 */
export const uploadImagen = async (file: File, folder?: string): Promise<UploadResult> => {
  const formData = new FormData()
  formData.append('file', file)
  if (folder) {
    formData.append('folder', folder)
  }

  return uploadRequest<UploadResult>('/upload/imagen', formData)
}

/**
 * Sube un documento asociado a un equipo (camión/máquina)
 */
export const uploadDocumentoEquipo = async (
  equipoId: string,
  tipoDocumento: string,
  file: File
): Promise<UploadResult> => {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('tipo_documento', tipoDocumento)

  return uploadRequest<UploadResult>(`/upload/equipo/${equipoId}`, formData)
}

export const uploadService = {
  uploadDocumento,
  uploadImagen,
  uploadDocumentoEquipo,
}

export default uploadService
