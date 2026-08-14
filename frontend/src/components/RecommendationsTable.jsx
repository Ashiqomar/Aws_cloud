import React, { useState, useMemo } from 'react';
import {
  Lightbulb,
  Search,
  Filter,
  ArrowUpDown,
  CheckCircle2,
  XCircle,
  Play,
  Cpu,
  HardDrive,
  Database,
  DollarSign,
  AlertTriangle,
  RefreshCw,
  Zap,
} from 'lucide-react';

export default function RecommendationsTable({
  items = [],
  onTriggerAnalysis,
  isAnalyzing,
  onApplyReco,
  onDismissReco,
  onRemediateReco,
}) {
  const [searchTerm, setSearchTerm] = useState('');
  const [typeFilter, setTypeFilter] = useState('ALL');
  const [highSavingsOnly, setHighSavingsOnly] = useState(false);
  const [sortField, setSortField] = useState('savings');
  const [sortAsc, setSortAsc] = useState(false);

  // Filter & Search logic
  const filteredItems = useMemo(() => {
    return items.filter((item) => {
      // Search term
      const matchesSearch =
        item.resource_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
        item.type.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (item.detail && item.detail.toLowerCase().includes(searchTerm.toLowerCase()));

      // Type filter
      const matchesType = typeFilter === 'ALL' || item.type === typeFilter;

      // High savings filter (> $50/mo)
      const matchesHighSavings = !highSavingsOnly || item.estimated_savings_monthly >= 50;

      return matchesSearch && matchesType && matchesHighSavings;
    }).sort((a, b) => {
      let valA = a.estimated_savings_monthly;
      let valB = b.estimated_savings_monthly;
      if (sortField === 'resource') {
        valA = a.resource_id;
        valB = b.resource_id;
      }
      if (valA < valB) return sortAsc ? -1 : 1;
      if (valA > valB) return sortAsc ? 1 : -1;
      return 0;
    });
  }, [items, searchTerm, typeFilter, highSavingsOnly, sortField, sortAsc]);

  const totalFilteredSavings = useMemo(() => {
    return filteredItems.reduce((acc, curr) => acc + (curr.estimated_savings_monthly || 0), 0);
  }, [filteredItems]);

  const getTypeBadge = (type) => {
    switch (type) {
      case 'idle_ec2':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-cyan-950/80 text-cyan-300 border border-cyan-800/60">
            <Cpu className="w-3.5 h-3.5" />
            Idle EC2
          </span>
        );
      case 'unused_ebs':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-950/80 text-amber-300 border border-amber-800/60">
            <HardDrive className="w-3.5 h-3.5" />
            Unused EBS
          </span>
        );
      case 'oversized_rds':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-purple-950/80 text-purple-300 border border-purple-800/60">
            <Database className="w-3.5 h-3.5" />
            Oversized RDS
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-slate-800 text-slate-300">
            {type}
          </span>
        );
    }
  };

  return (
    <div className="glass-panel rounded-2xl border border-slate-800 overflow-hidden">
      
      {/* Table Header & Controls Bar */}
      <div className="p-5 border-b border-slate-800/80 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <Lightbulb className="w-5 h-5 text-amber-400" />
            <h2 className="text-lg font-bold text-white">Savings Opportunities</h2>
            <span className="ml-2 px-2.5 py-0.5 rounded-full text-xs font-bold bg-cyan-950 text-cyan-400 border border-cyan-800">
              {filteredItems.length} found
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Potential monthly savings: {' '}
            <span className="font-extrabold text-emerald-400 text-sm">
              ${totalFilteredSavings.toLocaleString('en-US', { minimumFractionDigits: 2 })} / mo
            </span>
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2.5">
          {/* Search box */}
          <div className="relative flex-1 sm:flex-none min-w-[180px]">
            <Search className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search resource or detail..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full bg-slate-900 border border-slate-700/80 rounded-xl pl-9 pr-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-cyan-500 transition-all placeholder:text-slate-500"
            />
          </div>

          {/* Type Filter dropdown */}
          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            className="bg-slate-900 border border-slate-700/80 rounded-xl px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-cyan-500 transition-all cursor-pointer font-medium"
          >
            <option value="ALL">All Types</option>
            <option value="idle_ec2">Idle EC2</option>
            <option value="unused_ebs">Unused EBS</option>
            <option value="oversized_rds">Oversized RDS</option>
          </select>

          {/* High Savings filter toggle */}
          <button
            onClick={() => setHighSavingsOnly(!highSavingsOnly)}
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold border transition-all ${
              highSavingsOnly
                ? 'bg-emerald-950 text-emerald-300 border-emerald-700 shadow-md shadow-emerald-950/50'
                : 'bg-slate-900 text-slate-400 border-slate-700/80 hover:text-slate-200'
            }`}
          >
            <DollarSign className="w-3.5 h-3.5" />
            <span>High Savings (&gt;$50/mo)</span>
          </button>

          {/* Run Rules Engine trigger */}
          <button
            onClick={onTriggerAnalysis}
            disabled={isAnalyzing}
            className="flex items-center space-x-1.5 px-3.5 py-1.5 rounded-xl text-xs font-bold bg-cyan-500 hover:bg-cyan-400 text-slate-950 shadow-md shadow-cyan-500/20 transition-all disabled:opacity-50"
          >
            <Play className={`w-3.5 h-3.5 fill-current ${isAnalyzing ? 'animate-spin' : ''}`} />
            <span>{isAnalyzing ? 'Analyzing...' : 'Run Rules Engine'}</span>
          </button>
        </div>
      </div>

      {/* Recommendations Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs text-slate-300">
          <thead className="bg-slate-900/90 text-slate-400 font-semibold uppercase tracking-wider border-b border-slate-800">
            <tr>
              <th className="px-5 py-3.5 cursor-pointer hover:text-white" onClick={() => { setSortField('resource'); setSortAsc(!sortAsc); }}>
                <div className="flex items-center gap-1">
                  <span>Resource ID</span>
                  <ArrowUpDown className="w-3 h-3" />
                </div>
              </th>
              <th className="px-5 py-3.5">Category</th>
              <th className="px-5 py-3.5">Recommendation Detail / Reason</th>
              <th className="px-5 py-3.5 cursor-pointer hover:text-white" onClick={() => { setSortField('savings'); setSortAsc(!sortAsc); }}>
                <div className="flex items-center gap-1">
                  <span>Monthly Savings</span>
                  <ArrowUpDown className="w-3 h-3" />
                </div>
              </th>
              <th className="px-5 py-3.5">Status</th>
              <th className="px-5 py-3.5 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60">
            {filteredItems.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-5 py-10 text-center text-slate-500">
                  <div className="flex flex-col items-center justify-center">
                    <AlertTriangle className="w-8 h-8 text-slate-600 mb-2" />
                    <p className="text-sm font-semibold text-slate-400">No matching recommendations found.</p>
                    <p className="text-xs text-slate-500 mt-1">Try adjusting your search or click "Run Rules Engine".</p>
                  </div>
                </td>
              </tr>
            ) : (
              filteredItems.map((item) => (
                <tr key={item.id} className="hover:bg-slate-800/40 transition-colors">
                  
                  {/* Resource ID */}
                  <td className="px-5 py-4 font-mono font-bold text-white whitespace-nowrap">
                    {item.resource_id}
                  </td>

                  {/* Category Badge */}
                  <td className="px-5 py-4 whitespace-nowrap">
                    {getTypeBadge(item.type)}
                  </td>

                  {/* Reason Detail */}
                  <td className="px-5 py-4 max-w-md text-slate-300 leading-relaxed">
                    {item.detail}
                  </td>

                  {/* Estimated Savings */}
                  <td className="px-5 py-4 font-mono font-extrabold text-emerald-400 text-sm whitespace-nowrap">
                    +${item.estimated_savings_monthly?.toLocaleString('en-US', { minimumFractionDigits: 2 })}/mo
                  </td>

                  {/* Status */}
                  <td className="px-5 py-4 whitespace-nowrap">
                    <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                      item.status === 'open'
                        ? 'bg-emerald-950/80 text-emerald-400 border border-emerald-800/60'
                        : item.status === 'applied'
                        ? 'bg-cyan-950/80 text-cyan-400 border border-cyan-800/60'
                        : 'bg-slate-800 text-slate-400'
                    }`}>
                      {item.status.toUpperCase()}
                    </span>
                  </td>

                  {/* Actions */}
                  <td className="px-5 py-4 text-right whitespace-nowrap space-x-2">
                    {item.status === 'open' && (
                      <button
                        onClick={() => onRemediateReco && onRemediateReco(item)}
                        className="px-2.5 py-1.5 rounded-lg font-bold text-[11px] bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-slate-950 shadow-md shadow-amber-500/20 transition-all inline-flex items-center gap-1"
                      >
                        <Zap className="w-3.5 h-3.5 fill-current" />
                        <span>Apply Fix</span>
                      </button>
                    )}

                    <button
                      onClick={() => onApplyReco && onApplyReco(item)}
                      title="Mark as Applied"
                      className="p-1.5 rounded-lg bg-emerald-950/60 hover:bg-emerald-900/80 text-emerald-400 border border-emerald-800/60 transition-all inline-flex items-center"
                    >
                      <CheckCircle2 className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => onDismissReco && onDismissReco(item)}
                      title="Dismiss"
                      className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-slate-200 border border-slate-700 transition-all inline-flex items-center"
                    >
                      <XCircle className="w-4 h-4" />
                    </button>
                  </td>

                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

    </div>
  );
}
