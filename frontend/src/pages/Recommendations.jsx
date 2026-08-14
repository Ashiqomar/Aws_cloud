import React from 'react';
import RecommendationsTable from '../components/RecommendationsTable';
import { Lightbulb, DollarSign, Cpu, HardDrive, Database } from 'lucide-react';

export default function Recommendations({
  recommendations = [],
  recoSummary = {},
  onTriggerAnalysis,
  isAnalyzing,
  onApplyReco,
  onDismissReco,
  onRemediateReco,
}) {
  const summaryList = recoSummary?.summary || [];
  const totalSavings = recoSummary?.total_estimated_savings || 0;

  return (
    <div className="space-y-6">
      
      {/* Header Banner */}
      <div className="glass-panel p-6 rounded-2xl border border-slate-800 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl sm:text-2xl font-extrabold text-white flex items-center gap-2">
            <Lightbulb className="w-6 h-6 text-amber-400" />
            FinOps Savings Recommendations
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Heuristic rules engine results for idle compute, unattached storage, and oversized database clusters.
          </p>
        </div>

        <div className="bg-emerald-950/80 border border-emerald-800/80 rounded-2xl px-5 py-3 text-right">
          <span className="text-xs font-semibold text-emerald-400 uppercase tracking-wider block">
            Total Open Savings
          </span>
          <span className="text-2xl font-mono font-extrabold text-emerald-300">
            ${totalSavings.toLocaleString('en-US', { minimumFractionDigits: 2 })} / mo
          </span>
        </div>
      </div>

      {/* Category Breakdown Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        
        {/* Idle EC2 Summary Card */}
        {(() => {
          const ec2Info = summaryList.find((s) => s.type === 'idle_ec2') || { count: 0, estimated_savings: 0 };
          return (
            <div className="glass-panel p-4 rounded-2xl border border-cyan-500/20 flex items-center justify-between">
              <div>
                <span className="text-xs font-semibold text-slate-400 flex items-center gap-1.5">
                  <Cpu className="w-4 h-4 text-cyan-400" />
                  Idle EC2 Instances
                </span>
                <div className="text-xl font-bold text-white mt-1">
                  {ec2Info.count} detected
                </div>
                <span className="text-xs font-mono font-semibold text-cyan-400">
                  ${ec2Info.estimated_savings.toLocaleString()}/mo savings
                </span>
              </div>
            </div>
          );
        })()}

        {/* Unused EBS Summary Card */}
        {(() => {
          const ebsInfo = summaryList.find((s) => s.type === 'unused_ebs') || { count: 0, estimated_savings: 0 };
          return (
            <div className="glass-panel p-4 rounded-2xl border border-amber-500/20 flex items-center justify-between">
              <div>
                <span className="text-xs font-semibold text-slate-400 flex items-center gap-1.5">
                  <HardDrive className="w-4 h-4 text-amber-400" />
                  Unused EBS Volumes
                </span>
                <div className="text-xl font-bold text-white mt-1">
                  {ebsInfo.count} detected
                </div>
                <span className="text-xs font-mono font-semibold text-amber-400">
                  ${ebsInfo.estimated_savings.toLocaleString()}/mo savings
                </span>
              </div>
            </div>
          );
        })()}

        {/* Oversized RDS Summary Card */}
        {(() => {
          const rdsInfo = summaryList.find((s) => s.type === 'oversized_rds') || { count: 0, estimated_savings: 0 };
          return (
            <div className="glass-panel p-4 rounded-2xl border border-purple-500/20 flex items-center justify-between">
              <div>
                <span className="text-xs font-semibold text-slate-400 flex items-center gap-1.5">
                  <Database className="w-4 h-4 text-purple-400" />
                  Oversized RDS Databases
                </span>
                <div className="text-xl font-bold text-white mt-1">
                  {rdsInfo.count} detected
                </div>
                <span className="text-xs font-mono font-semibold text-purple-400">
                  ${rdsInfo.estimated_savings.toLocaleString()}/mo savings
                </span>
              </div>
            </div>
          );
        })()}

      </div>

      {/* Main Recommendations Table */}
      <RecommendationsTable
        items={recommendations}
        onTriggerAnalysis={onTriggerAnalysis}
        isAnalyzing={isAnalyzing}
        onApplyReco={onApplyReco}
        onDismissReco={onDismissReco}
        onRemediateReco={onRemediateReco}
      />

    </div>
  );
}
