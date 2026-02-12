// Constantes de la aplicación
export const API_URL = import.meta.env.VITE_API_URL || 'https://backend-production-ee51.up.railway.app/api/v1';

// Debug en producción
console.log('[CONSTANTS] VITE_API_URL:', import.meta.env.VITE_API_URL);
console.log('[CONSTANTS] API_URL final:', API_URL);
