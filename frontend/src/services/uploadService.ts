import api from './api'

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
 * Sube un documento general
 */
export const uploadDocumento = async (file: File, folder?: string): Promise<UploadResult> => {
  const formData = new FormData()
  formData.append('file', file)
  if (folder) {
    formData.append('folder', folder)
  }

  const { data } = await api.post<UploadResult>('/upload/documento', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
  return data
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

  const { data } = await api.post<UploadResult>('/upload/imagen', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
  return data
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

  const { data } = await api.post<UploadResult>(`/upload/equipo/${equipoId}`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
  return data
}

export const uploadService = {
  uploadDocumento,
  uploadImagen,
  uploadDocumentoEquipo,
}

export default uploadService
