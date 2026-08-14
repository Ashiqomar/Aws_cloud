import React from 'react';
import { DollarSign, Lightbulb, TrendingDown, Layers, Server } from 'lucide-react';
import StatCard from '../components/StatCard';
import CostDonutChart from '../components/CostDonutChart';
import CostTrendChart from '../components/CostTrendChart';
import AIInsightsCard from '../components/AIInsightsCard';

export default function Dashboard({
  costSummary,
  recoSummary,
  aiData,
  onRefreshAI,
  isAILoading,
  onNavigateToRecos,
  onSeedDemo
}) {
  const totalCost = costSummary?.total_monthly_cost || 0;
  const serviceBreakdown = costSummary?.service_breakdown || [];
  const dailyTrends = costSummary?.daily_trends || [];

  const totalSavings = recoSummary?.total_estimated_savings || 0;
  const totalOpenRecos = recoSummary?.total_open || 0;

  return (
    <div className="space-y-6">
      
      {/* Top Welcome / Header Banner */}
      <div className="glass-panel p-6 rounded-2xl border border-slate-800 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl sm:text-2xl font-extrabold text-white">
            Cloud Cost & Optimization Overview
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Real-time AWS multi-account spending visibility, asset inventory, and FinOps analytics.
          </p>
        </div>

        {totalCost === 0 && (
          <button
            onClick={onSeedDemo}
            className="px-4 py-2 rounded-xl text-xs font-bold bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-400 hover:to-teal-400 text-slate-950 shadow-lg shadow-emerald-500/20 transition-all flex items-center gap-2 whitespace-nowrap"
          >
            <DollarSign className="w-4 h-4" />
            <span>Seed FinOps Demo Data</span>
          </button>
        )}
      </div>

      {/* AI FinOps Advisor Insights Card */}
      <AIInsightsCard
        aiData={aiData}
        onRefreshAI={onRefreshAI}
        isLoading={isAILoading}
      />

      {/* Metric Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        
        {/* Total Monthly Cost Card */}
        <StatCard
          title="Total Monthly Cost"
          value={`$${totalCost.toLocaleString('en-US', { minimumFractionDigits: 2 })}`}
          subtitle="Past 30 days AWS expenditure"
          icon={DollarSign}
          trend={{ value: '30-Day Window', isPositive: true }}
          color="cyan"
        />

        {/* Projected Monthly Savings */}
        <StatCard
          title="Identified Savings"
          value={`$${totalSavings.toLocaleString('en-US', { minimumFractionDigits: 2 })}`}
          subtitle={`${totalOpenRecos} active recommendations`}
          icon={TrendingDown}
          trend={{ value: 'Rules Engine', isPositive: true }}
          color="emerald"
        />

        {/* Total AWS Services Active */}
        <StatCard
          title="Active Services"
          value={serviceBreakdown.length}
          subtitle="Generating expenditures"
          icon={Layers}
          color="purple"
        />

        {/* Actionable Optimizations Card */}
        <div
          onClick={onNavigateToRecos}
          className="glass-panel glass-panel-hover p-5 rounded-2xl border border-amber-500/20 hover:border-amber-500/40 cursor-pointer flex flex-col justify-between"
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              Open Opportunities
            </span>
            <div className="p-2.5 rounded-xl bg-amber-500/10 text-amber-400">
              <Lightbulb className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline justify-between">
            <div className="text-2xl sm:text-3xl font-extrabold text-amber-400">
              {totalOpenRecos}
            </div>
            <span className="text-xs text-amber-400 font-semibold underline">View All →</span>
          </div>
          <p className="mt-1 text-xs text-slate-400">Click to inspect recommendation details</p>
        </div>

      </div>

      {/* Main Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* TASK 2 Requirement: Donut Chart showing Cost by Service */}
        <CostDonutChart data={serviceBreakdown} totalCost={totalCost} />

        {/* Daily Spending Trend Chart */}
        <CostTrendChart data={dailyTrends} />

      </div>

      {/* Top Cost Services Summary Bar */}
      {serviceBreakdown.length > 0 && (
        <div className="glass-panel p-5 rounded-2xl border border-slate-800">
          <h3 className="text-sm font-bold text-white mb-3 flex items-center gap-2">
            <Server className="w-4 h-4 text-cyan-400" />
            Top Cost Driving Services
          </h3>
          <div className="space-y-3">
            {serviceBreakdown.slice(0, 4).map((srv, idx) => (
              <div key={idx} className="space-y-1">
                <div className="flex items-center justify-between text-xs font-medium">
                  <span className="text-slate-200">{srv.service_name}</span>
                  <div className="space-x-2">
                    <span className="font-mono text-cyan-400">${srv.amount.toLocaleString()}</span>
                    <span className="text-slate-500">({srv.percentage}%)</span>
                  </div>
                </div>
                <div className="w-full h-2 bg-slate-900 rounded-full overflow-hidden border border-slate-800">
                  <div
                    className="h-full bg-gradient-to-r from-cyan-500 to-emerald-400 rounded-full transition-all duration-500"
                    style={{ width: `${srv.percentage}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

    </div>
  );
}
