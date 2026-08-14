import React from 'react';
import { Sparkles, Bot, RefreshCw, Cpu, TrendingDown, CheckCircle2 } from 'lucide-react';

export default function AIInsightsCard({ aiData, onRefreshAI, isLoading }) {
  if (!aiData) return null;

  const { ai_provider, summary, top_cost_drivers = [], top_recommendations = [], timestamp } = aiData;

  // Simple formatter to convert markdown bold/bullet points to JSX
  const renderFormattedSummary = (text) => {
    if (!text) return null;
    const lines = text.split('\n');
    return lines.map((line, idx) => {
      let content = line.trim();
      if (!content) return <div key={idx} className="h-1.5" />;

      if (content.startsWith('###') || content.startsWith('##')) {
        return (
          <h4 key={idx} className="text-sm font-bold text-cyan-300 mt-2 mb-1">
            {content.replace(/^#+\s*/, '')}
          </h4>
        );
      }

      if (content.startsWith('-') || content.startsWith('*') || /^\d+\./.test(content)) {
        const bulletText = content.replace(/^[-*\d.]+\s*/, '');
        // Replace **bold** with <span>
        const parts = bulletText.split(/(\*\*.*?\*\*)/g);
        return (
          <li key={idx} className="text-xs text-slate-300 ml-4 list-disc leading-relaxed my-1">
            {parts.map((p, pIdx) => {
              if (p.startsWith('**') && p.endsWith('**')) {
                return <strong key={pIdx} className="text-white font-semibold">{p.slice(2, -2)}</strong>;
              }
              return p;
            })}
          </li>
        );
      }

      const parts = content.split(/(\*\*.*?\*\*)/g);
      return (
        <p key={idx} className="text-xs text-slate-300 leading-relaxed my-1">
          {parts.map((p, pIdx) => {
            if (p.startsWith('**') && p.endsWith('**')) {
              return <strong key={pIdx} className="text-white font-semibold">{p.slice(2, -2)}</strong>;
            }
            return p;
          })}
        </p>
      );
    });
  };

  return (
    <div className="glass-panel glass-panel-hover p-6 rounded-2xl border border-cyan-500/30 relative overflow-hidden bg-gradient-to-br from-cyan-950/20 via-slate-900/80 to-purple-950/20 shadow-xl">
      
      {/* Background Subtle Ambient Glow */}
      <div className="absolute -top-12 -right-12 w-48 h-48 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute -bottom-12 -left-12 w-48 h-48 bg-purple-500/10 rounded-full blur-3xl pointer-events-none" />

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4 border-b border-slate-800/80 pb-3">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-gradient-to-tr from-cyan-500 to-purple-600 text-slate-950 shadow-md shadow-cyan-500/20">
            <Bot className="w-5 h-5 stroke-[2.5]" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-base font-bold text-white tracking-tight">AI FinOps Consultant Insights</h2>
              <span className="inline-flex items-center gap-1 text-[11px] font-bold px-2 py-0.5 rounded-full bg-cyan-950 text-cyan-300 border border-cyan-800">
                <Sparkles className="w-3 h-3 text-cyan-400" />
                {ai_provider || 'Google Gemini'}
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              Automated executive summary & plain-English cost optimization guidance
            </p>
          </div>
        </div>

        <button
          onClick={onRefreshAI}
          disabled={isLoading}
          className="flex items-center space-x-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold bg-slate-800/90 hover:bg-slate-700 text-cyan-400 border border-slate-700/80 transition-all disabled:opacity-50 self-start sm:self-auto"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
          <span>{isLoading ? 'Consulting Gemini...' : 'Refresh AI Summary'}</span>
        </button>
      </div>

      {/* Main Content Area */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Left 2 Cols: AI Text Summary */}
        <div className="lg:col-span-2 space-y-2 text-slate-300">
          <ul className="space-y-1">
            {renderFormattedSummary(summary)}
          </ul>
        </div>

        {/* Right 1 Col: Key Highlights Cards */}
        <div className="space-y-3 border-t lg:border-t-0 lg:border-l border-slate-800/80 pt-4 lg:pt-0 lg:pl-6">
          
          {/* Top 3 Cost Drivers Quick Glance */}
          <div>
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5 mb-2">
              <Cpu className="w-3.5 h-3.5 text-cyan-400" />
              Top Cost Drivers
            </h4>
            <div className="space-y-1.5">
              {top_cost_drivers.length === 0 ? (
                <p className="text-xs text-slate-500">No cost data available.</p>
              ) : (
                top_cost_drivers.slice(0, 3).map((item, idx) => (
                  <div key={idx} className="flex items-center justify-between p-2 rounded-lg bg-slate-900/60 border border-slate-800 text-xs">
                    <span className="font-semibold text-slate-200">{item.service_name}</span>
                    <span className="font-mono text-cyan-400 font-bold">${item.amount?.toLocaleString()}</span>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Top 3 Savings Opportunities Quick Glance */}
          <div>
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5 mb-2">
              <TrendingDown className="w-3.5 h-3.5 text-emerald-400" />
              High Savings Opportunities
            </h4>
            <div className="space-y-1.5">
              {top_recommendations.length === 0 ? (
                <p className="text-xs text-slate-500">No recommendations open.</p>
              ) : (
                top_recommendations.slice(0, 3).map((item, idx) => (
                  <div key={idx} className="p-2 rounded-lg bg-slate-900/60 border border-slate-800 text-xs flex items-center justify-between">
                    <div className="truncate max-w-[140px]">
                      <span className="font-mono font-bold text-slate-200 block truncate">{item.resource_id}</span>
                      <span className="text-[10px] text-slate-500 capitalize">{item.type?.replace('_', ' ')}</span>
                    </div>
                    <span className="font-mono font-bold text-emerald-400 whitespace-nowrap">
                      +${item.estimated_savings_monthly?.toLocaleString()}/mo
                    </span>
                  </div>
                ))
              )}
            </div>
          </div>

        </div>

      </div>

      {timestamp && (
        <div className="mt-4 pt-2 border-t border-slate-800/60 text-[10px] text-slate-500 text-right">
          Generated: {new Date(timestamp).toLocaleTimeString()} UTC
        </div>
      )}

    </div>
  );
}
