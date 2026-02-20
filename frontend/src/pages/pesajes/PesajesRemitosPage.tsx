import { useState } from 'react'
import { Scale, ClipboardList } from 'lucide-react'
import PesajesTab from './PesajesTab'
import OrdenesEntregaTab from './OrdenesEntregaTab'

type TabType = 'pesajes' | 'ordenes'

export default function PesajesRemitosPage() {
  const [activeTab, setActiveTab] = useState<TabType>('pesajes')

  const tabs = [
    { id: 'pesajes' as TabType, label: 'Pesajes', icon: Scale },
    { id: 'ordenes' as TabType, label: 'Órdenes de Entrega', icon: ClipboardList },
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 flex items-center gap-2">
          <Scale className="h-6 w-6 sm:h-8 sm:w-8" />
          Pesajes y Remitos
        </h1>
        <p className="text-gray-500 mt-1 text-sm sm:text-base">
          Registro de pesajes y órdenes de entrega
        </p>
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
        {activeTab === 'pesajes' && <PesajesTab />}
        {activeTab === 'ordenes' && <OrdenesEntregaTab />}
      </div>
    </div>
  )
}
