import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard,
  Truck,
  Wrench,
  Scale,
  Fuel,
  BarChart3,
  Users,
  X,
  Building2,
  DollarSign,
  Wallet,
  ListOrdered,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import logo from '@/assets/logo.png'
import { useAuthStore } from '@/stores/authStore'

interface SidebarProps {
  isOpen: boolean
  onClose: () => void
}

const menuItems = [
  {
    title: 'Dashboard',
    icon: LayoutDashboard,
    path: '/dashboard',
    permiso: 'permiso_dashboard' as const,
  },
  {
    title: 'Camiones',
    icon: Truck,
    path: '/camiones',
    permiso: 'permiso_camiones' as const,
  },
  {
    title: 'Clientes/Transportistas',
    icon: Building2,
    path: '/empresas',
    permiso: 'permiso_empresas' as const,
  },
  {
    title: 'Listas de Precios',
    icon: ListOrdered,
    path: '/listas-precios',
    permiso: 'permiso_empresas' as const,
  },
  {
    title: 'Repuestos',
    icon: Wrench,
    path: '/repuestos',
    permiso: 'permiso_repuestos' as const,
  },
  {
    title: 'Pesajes',
    icon: Scale,
    path: '/pesajes-remitos',
    permiso: 'permiso_pesajes' as const,
  },
  {
    title: 'Combustible',
    icon: Fuel,
    path: '/combustible',
    permiso: 'permiso_combustible' as const,
  },
  {
    title: 'Finanzas',
    icon: DollarSign,
    path: '/finanzas',
    permiso: 'permiso_finanzas' as const,
  },
  {
    title: 'Tesorería',
    icon: Wallet,
    path: '/tesoreria',
    permiso: 'permiso_finanzas' as const,
  },
  {
    title: 'Usuarios',
    icon: Users,
    path: '/usuarios',
    permiso: 'permiso_usuarios' as const,
  },
  {
    title: 'Reportes',
    icon: BarChart3,
    path: '/reportes',
    permiso: 'permiso_reportes' as const,
  },
]

export default function Sidebar({ isOpen, onClose }: SidebarProps) {
  const { user } = useAuthStore()

  // Filtrar items según los permisos del usuario
  const filteredMenuItems = menuItems.filter((item) => {
    if (!user) return false

    // Los administradores ven todo
    if (user.rol === 'administrador') return true

    // Para otros usuarios, verificar permisos
    // Si el permiso no está definido (undefined/null), asumir acceso
    const permiso = user[item.permiso]
    return permiso === undefined || permiso === null || permiso === true
  })

  return (
    <>
      {/* Overlay para mobile */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-20 lg:hidden"
          onClick={onClose}
        />
      )}

      {/* Sidebar */}
      <aside
        className={cn(
          'fixed lg:sticky top-0 left-0 z-30 h-screen w-64 bg-white border-r border-gray-200 transition-transform duration-300 lg:translate-x-0',
          isOpen ? 'translate-x-0' : '-translate-x-full'
        )}
      >
        <div className="flex flex-col h-full">
          {/* Logo y header del sidebar */}
          <div className="p-4 border-b">
            <div className="hidden lg:flex items-center justify-center mb-2">
              <img
                src={logo}
                alt="Logo Cantera La Rufina"
                className="h-16 w-auto object-contain"
              />
            </div>
            <div className="flex items-center justify-between lg:hidden">
              <span className="font-semibold text-gray-900">Menú</span>
              <Button variant="ghost" size="icon" onClick={onClose}>
                <X className="h-5 w-5" />
              </Button>
            </div>
          </div>

          {/* Navegación */}
          <nav className="flex-1 overflow-y-auto p-4 space-y-1">
            {filteredMenuItems.map((item) => (
              <NavLink
                key={item.path}
                to={item.path}
                onClick={() => onClose()}
                className={({ isActive }) =>
                  cn(
                    'flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors',
                    isActive
                      ? 'bg-brand-50 text-brand-700'
                      : 'text-gray-700 hover:bg-gray-100 hover:text-gray-900'
                  )
                }
              >
                <item.icon className="h-5 w-5" />
                {item.title}
              </NavLink>
            ))}
          </nav>

          {/* Footer */}
          <div className="p-4 border-t border-gray-200">
            <div className="text-xs text-gray-500 text-center">
              <p>Sistema Cantera La Rufina</p>
              <p className="mt-1">v1.0.0</p>
            </div>
          </div>
        </div>
      </aside>
    </>
  )
}
