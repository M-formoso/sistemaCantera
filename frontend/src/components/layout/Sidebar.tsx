import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard,
  Truck,
  Wrench,
  Scale,
  FileText,
  Fuel,
  BarChart3,
  X,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'

interface SidebarProps {
  isOpen: boolean
  onClose: () => void
}

const menuItems = [
  {
    title: 'Dashboard',
    icon: LayoutDashboard,
    path: '/dashboard',
  },
  {
    title: 'Camiones',
    icon: Truck,
    path: '/camiones',
  },
  {
    title: 'Repuestos',
    icon: Wrench,
    path: '/repuestos',
  },
  {
    title: 'Pesajes',
    icon: Scale,
    path: '/pesajes',
  },
  {
    title: 'Remitos',
    icon: FileText,
    path: '/remitos',
  },
  {
    title: 'Combustible',
    icon: Fuel,
    path: '/combustible',
  },
  {
    title: 'Reportes',
    icon: BarChart3,
    path: '/reportes',
  },
]

export default function Sidebar({ isOpen, onClose }: SidebarProps) {
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
          {/* Header del sidebar (solo mobile) */}
          <div className="flex items-center justify-between p-4 border-b lg:hidden">
            <span className="font-semibold text-gray-900">Menú</span>
            <Button variant="ghost" size="icon" onClick={onClose}>
              <X className="h-5 w-5" />
            </Button>
          </div>

          {/* Navegación */}
          <nav className="flex-1 overflow-y-auto p-4 space-y-1">
            {menuItems.map((item) => (
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
