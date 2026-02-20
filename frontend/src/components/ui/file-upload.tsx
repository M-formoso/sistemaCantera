import { useState, useRef } from 'react'
import { Upload, X, FileText, Image, Loader2, ExternalLink } from 'lucide-react'
import { Button } from './button'
import { cn } from '@/lib/utils'

interface FileUploadProps {
  value?: string
  onChange: (url: string | undefined) => void
  onUpload: (file: File) => Promise<{ url: string }>
  accept?: string
  maxSizeMB?: number
  label?: string
  placeholder?: string
  disabled?: boolean
  className?: string
}

export function FileUpload({
  value,
  onChange,
  onUpload,
  accept = "image/*,.pdf",
  maxSizeMB = 10,
  label,
  placeholder = "Seleccionar archivo...",
  disabled = false,
  className,
}: FileUploadProps) {
  const [isUploading, setIsUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [fileName, setFileName] = useState<string | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    setError(null)

    // Validar tamaño
    const sizeMB = file.size / (1024 * 1024)
    if (sizeMB > maxSizeMB) {
      setError(`El archivo excede el tamaño máximo de ${maxSizeMB}MB`)
      return
    }

    setIsUploading(true)
    setFileName(file.name)

    try {
      const result = await onUpload(file)
      onChange(result.url)
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string } } }
      setError(error.response?.data?.detail || 'Error al subir el archivo')
      setFileName(null)
    } finally {
      setIsUploading(false)
      // Reset input para permitir subir el mismo archivo otra vez
      if (inputRef.current) {
        inputRef.current.value = ''
      }
    }
  }

  const handleRemove = () => {
    onChange(undefined)
    setFileName(null)
    setError(null)
  }

  const isImage = value?.match(/\.(jpg|jpeg|png|gif|webp)$/i)
  const isPDF = value?.match(/\.pdf$/i)

  return (
    <div className={cn("space-y-2", className)}>
      {label && <label className="text-sm font-medium">{label}</label>}

      {/* Input oculto */}
      <input
        ref={inputRef}
        type="file"
        accept={accept}
        onChange={handleFileSelect}
        disabled={disabled || isUploading}
        className="hidden"
      />

      {/* Si hay valor, mostrar preview */}
      {value ? (
        <div className="border rounded-lg p-3 bg-gray-50">
          <div className="flex items-center justify-between gap-3">
            <div className="flex items-center gap-3 min-w-0">
              {isImage ? (
                <div className="w-12 h-12 rounded overflow-hidden flex-shrink-0">
                  <img src={value} alt="Preview" className="w-full h-full object-cover" />
                </div>
              ) : isPDF ? (
                <div className="w-12 h-12 rounded bg-red-100 flex items-center justify-center flex-shrink-0">
                  <FileText className="h-6 w-6 text-red-600" />
                </div>
              ) : (
                <div className="w-12 h-12 rounded bg-blue-100 flex items-center justify-center flex-shrink-0">
                  <FileText className="h-6 w-6 text-blue-600" />
                </div>
              )}
              <div className="min-w-0">
                <p className="text-sm font-medium truncate">
                  {fileName || 'Archivo cargado'}
                </p>
                <a
                  href={value}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs text-blue-600 hover:underline flex items-center gap-1"
                >
                  Ver archivo <ExternalLink className="h-3 w-3" />
                </a>
              </div>
            </div>
            <div className="flex items-center gap-2 flex-shrink-0">
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => inputRef.current?.click()}
                disabled={disabled || isUploading}
              >
                Cambiar
              </Button>
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={handleRemove}
                disabled={disabled || isUploading}
              >
                <X className="h-4 w-4 text-red-500" />
              </Button>
            </div>
          </div>
        </div>
      ) : (
        /* Botón para seleccionar archivo */
        <div
          onClick={() => !disabled && !isUploading && inputRef.current?.click()}
          className={cn(
            "border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors",
            disabled || isUploading
              ? "bg-gray-100 cursor-not-allowed"
              : "hover:border-blue-400 hover:bg-blue-50"
          )}
        >
          {isUploading ? (
            <div className="flex flex-col items-center gap-2">
              <Loader2 className="h-8 w-8 text-blue-500 animate-spin" />
              <p className="text-sm text-gray-600">Subiendo {fileName}...</p>
            </div>
          ) : (
            <div className="flex flex-col items-center gap-2">
              <div className="p-3 bg-gray-100 rounded-full">
                {accept.includes('image') ? (
                  <Image className="h-6 w-6 text-gray-400" />
                ) : (
                  <Upload className="h-6 w-6 text-gray-400" />
                )}
              </div>
              <div>
                <p className="text-sm font-medium text-gray-700">{placeholder}</p>
                <p className="text-xs text-gray-500 mt-1">
                  Máximo {maxSizeMB}MB
                </p>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Error */}
      {error && (
        <p className="text-sm text-red-600">{error}</p>
      )}
    </div>
  )
}
