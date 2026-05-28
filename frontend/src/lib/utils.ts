import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

/**
 * Combina clases de Tailwind CSS de manera inteligente
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/**
 * Formatea un número como moneda argentina
 */
export function formatCurrency(value: number): string {
  return new Intl.NumberFormat('es-AR', {
    style: 'currency',
    currency: 'ARS',
    minimumFractionDigits: 2,
  }).format(value)
}

/**
 * Formatea un número con separador de miles argentino
 */
export function formatNumber(value: number, decimals: number = 2): string {
  return new Intl.NumberFormat('es-AR', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value)
}

/**
 * Formatea una fecha en formato DD/MM/YYYY.
 *
 * Importante: si recibe un string "YYYY-MM-DD" (sin hora), lo trata como
 * fecha local. `new Date("2026-05-28")` parsearía como UTC y en AR (UTC-3)
 * caería al día anterior — por eso evitamos ese camino.
 */
export function formatDate(date: Date | string): string {
  if (typeof date === 'string') {
    const dateOnly = date.match(/^(\d{4})-(\d{2})-(\d{2})$/)
    if (dateOnly) {
      const [, y, m, d] = dateOnly
      return `${d}/${m}/${y}`
    }
    return new Intl.DateTimeFormat('es-AR').format(new Date(date))
  }
  return new Intl.DateTimeFormat('es-AR').format(date)
}

/**
 * Formatea una fecha con hora en formato DD/MM/YYYY HH:mm.
 * Si recibe sólo "YYYY-MM-DD" no le inventa hora — la muestra como 00:00 local.
 */
export function formatDateTime(date: Date | string): string {
  let d: Date
  if (typeof date === 'string') {
    const dateOnly = date.match(/^(\d{4})-(\d{2})-(\d{2})$/)
    if (dateOnly) {
      const [, y, m, day] = dateOnly
      d = new Date(Number(y), Number(m) - 1, Number(day))
    } else {
      d = new Date(date)
    }
  } else {
    d = date
  }
  return new Intl.DateTimeFormat('es-AR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(d)
}

/**
 * Trunca un texto a una longitud máxima
 */
export function truncate(text: string, length: number): string {
  if (text.length <= length) return text
  return text.substring(0, length) + '...'
}

/**
 * Obtiene las iniciales de un nombre
 */
export function getInitials(name: string): string {
  return name
    .split(' ')
    .map(n => n[0])
    .join('')
    .toUpperCase()
    .substring(0, 2)
}

/**
 * Obtiene la fecha actual en formato YYYY-MM-DD usando la hora local
 * (evita problemas con toISOString() que convierte a UTC)
 */
export function getTodayLocalDate(): string {
  const now = new Date()
  const year = now.getFullYear()
  const month = String(now.getMonth() + 1).padStart(2, '0')
  const day = String(now.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}
