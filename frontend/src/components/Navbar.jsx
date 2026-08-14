import React from 'react';
import { Cloud, LayoutDashboard, Lightbulb, PlusCircle, RefreshCw, Sparkles, Building2 } from 'lucide-react';

export default function Navbar({
  activeTab,
  setActiveTab,
  tenants,
  selectedTenant,
  setSelectedTenant,
  onOpenConnect,
  onSeedDemo,
  onSyncData,
  isSyncing
}) {
  return (
    <header className="sticky top-0 z-40 bg-[#0b0f17]/90 backdrop-blur-md border-b border-slate-800/80">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          
          {/* Logo & Brand */}
          <div className="flex items-center space-x-3 cursor-pointer" onClick={() => setActiveTab('dashboard')}>
            <div className="p-2 rounded-xl bg-gradient-to-tr from-cyan-600 via-cyan-500 to-emerald-400 text-slate-950 shadow-lg shadow-cyan-500/20">
              <Cloud className="w-6 h-6 stroke-[2.5]" />
            </div>
            <div>
              <span className="text-lg font-bold bg-gradient-to-r from-white via-slate-200 to-cyan-400 bg-clip-text text-transparent">
                CloudOptix
              </span>
              <span className="hidden sm:inline-block ml-2 text-xs font-semibold px-2 py-0.5 rounded-full bg-cyan-950/80 text-cyan-400 border border-cyan-800/50">
                FinOps
              </span>
            </div>
          </div>

          {/* Navigation Tabs */}
          <nav className="flex items-center space-x-1 sm:space-x-2 bg-slate-900/90 p-1 rounded-xl border border-slate-800">
            <button
              onClick={() => setActiveTab('dashboard')}
              className={`flex items-center space-x-2 px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
                activeTab === 'dashboard'
                  ? 'bg-cyan-500 text-slate-950 font-semibold shadow-md shadow-cyan-500/20'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
              }`}
            >
              <LayoutDashboard className="w-4 h-4" />
              <span>Overview</span>
            </button>

            <button
              onClick={() => setActiveTab('recommendations')}
              className={`flex items-center space-x-2 px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
                activeTab === 'recommendations'
                  ? 'bg-cyan-500 text-slate-950 font-semibold shadow-md shadow-cyan-500/20'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
              }`}
            >
              <Lightbulb className="w-4 h-4" />
              <span>Recommendations</span>
            </button>
          </nav>

          {/* Controls & Account Switcher */}
          <div className="flex items-center space-x-2 sm:space-x-3">
            
            {/* Tenant selector if available */}
            {tenants.length > 0 && (
              <div className="relative hidden md:flex items-center space-x-2 bg-slate-900 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-300">
                <Building2 className="w-3.5 h-3.5 text-cyan-400" />
                <select
                  value={selectedTenant?.id || ''}
                  onChange={(e) => {
                    const t = tenants.find((item) => item.id === e.target.value);
                    setSelectedTenant(t || null);
                  }}
                  className="bg-transparent text-slate-200 text-xs focus:outline-none cursor-pointer font-medium pr-1"
                >
                  <option value="" className="bg-slate-900 text-slate-200">All Accounts</option>
                  {tenants.map((t) => (
                    <option key={t.id} value={t.id} className="bg-slate-900 text-slate-200">
                      {t.organization_name} ({t.account_id})
                    </option>
                  ))}
                </select>
              </div>
            )}

            {/* Demo Data button */}
            <button
              onClick={onSeedDemo}
              title="Seed mock FinOps data"
              className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-emerald-950/60 hover:bg-emerald-900/80 text-emerald-300 border border-emerald-800/60 transition-all"
            >
              <Sparkles className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Demo Data</span>
            </button>

            {/* Sync button */}
            <button
              onClick={onSyncData}
              disabled={isSyncing}
              className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition-all disabled:opacity-50"
            >
              <RefreshCw className={`w-3.5 h-3.5 text-cyan-400 ${isSyncing ? 'animate-spin' : ''}`} />
              <span className="hidden sm:inline">{isSyncing ? 'Syncing...' : 'Sync AWS'}</span>
            </button>

            {/* Connect Account button */}
            <button
              onClick={onOpenConnect}
              className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-bold bg-gradient-to-r from-cyan-500 to-teal-500 hover:from-cyan-400 hover:to-teal-400 text-slate-950 shadow-md shadow-cyan-500/20 transition-all"
            >
              <PlusCircle className="w-4 h-4 stroke-[2.5]" />
              <span className="hidden sm:inline">Connect Account</span>
            </button>
          </div>

        </div>
      </div>
    </header>
  );
}
