import { useState } from 'react'
import { DollarSign, CreditCard } from 'lucide-react'
import MovimientosTab from './MovimientosTab'
import CuentaCorrienteTab from './CuentaCorrienteTab'

type TabType = 'movimientos' | 'cuenta-corriente'

export default function FinanzasPage() {
  const [activeTab, setActiveTab] = useState<TabType>('movimientos')

  const tabs = [
    { id: 'movimientos' as TabType, label: 'Ingresos y Egresos', icon: DollarSign },
    { id: 'cuenta-corriente' as TabType, label: 'Cuenta Corriente', icon: CreditCard },
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Finanzas</h1>
        <p className="text-gray-500 mt-1">Control financiero y cuentas por cobrar</p>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {tabs.map((tab) => {
            const Icon = tab.icon
            const isActive = activeTab === tab.id
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`
                  flex items-center gap-2 py-4 px-1 border-b-2 font-medium text-sm
                  ${isActive
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }
                `}
              >
                <Icon className="h-5 w-5" />
                {tab.label}
              </button>
            )
          })}
        </nav>
      </div>

      {/* Tab Content */}
      <div>
        {activeTab === 'movimientos' && <MovimientosTab />}
        {activeTab === 'cuenta-corriente' && <CuentaCorrienteTab />}
      </div>
    </div>
  )
}
