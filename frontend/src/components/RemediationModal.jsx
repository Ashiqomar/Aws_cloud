import React, { useState } from 'react';
import { X, AlertTriangle, ShieldCheck, Play, Bell, Info } from 'lucide-react';

export default function RemediationModal({ isOpen, onClose, recommendation, onConfirm, isLoading }) {
  const [dryRun, setDryRun] = useState(true);
  const [webhookUrl, setWebhookUrl] = useState('');

  if (!isOpen || !recommendation) return null;

  const handleSubmit = (e) => {
    e.preventDefault();
    onConfirm({
      recommendation_id: recommendation.id,
      dry_run: dryRun,
      webhook_url: webhookUrl.trim() || null,
    });
  };

  const getActionName = (type) => {
    switch (type) {
      case 'idle_ec2':
        return 'Stop EC2 Instance';
      case 'unused_ebs':
        return 'Delete EBS Volume';
      case 'oversized_rds':
        return 'Log RDS Downsizing Plan';
      default:
        return 'Apply Remediation';
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-fadeIn">
      <div className="glass-panel w-full max-w-lg rounded-2xl border border-amber-500/30 shadow-2xl p-6 relative bg-gradient-to-b from-slate-900 to-[#0b0f17]">
        
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute right-4 top-4 text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800 transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Safety Header */}
        <div className="flex items-center gap-3 mb-4">
          <div className="p-3 rounded-2xl bg-amber-500/10 text-amber-400 border border-amber-500/30">
            <AlertTriangle className="w-6 h-6 stroke-[2.5]" />
          </div>
          <div>
            <h3 className="text-lg font-extrabold text-white">Confirm Remediation Action</h3>
            <p className="text-xs text-slate-400">AWS Boto3 Infrastructure Management</p>
          </div>
        </div>

        {/* Target Resource Summary Box */}
        <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800 space-y-2 mb-4">
          <div className="flex items-center justify-between text-xs">
            <span className="text-slate-400 font-medium">Target Resource:</span>
            <span className="font-mono font-bold text-white bg-slate-800 px-2 py-0.5 rounded border border-slate-700">
              {recommendation.resource_id}
            </span>
          </div>
          <div className="flex items-center justify-between text-xs">
            <span className="text-slate-400 font-medium">Action to Perform:</span>
            <span className="font-bold text-amber-400">{getActionName(recommendation.type)}</span>
          </div>
          <div className="flex items-center justify-between text-xs">
            <span className="text-slate-400 font-medium">Estimated Monthly Savings:</span>
            <span className="font-mono font-extrabold text-emerald-400">
              +${recommendation.estimated_savings_monthly?.toLocaleString('en-US', { minimumFractionDigits: 2 })}/mo
            </span>
          </div>
        </div>

        {/* Form Options */}
        <form onSubmit={handleSubmit} className="space-y-4 text-xs">
          
          {/* Dry Run Toggle */}
          <div className="p-3.5 rounded-xl bg-cyan-950/40 border border-cyan-800/60 flex items-start gap-3">
            <input
              type="checkbox"
              id="dryRunToggle"
              checked={dryRun}
              onChange={(e) => setDryRun(e.target.checked)}
              className="mt-0.5 rounded text-cyan-500 focus:ring-cyan-500 bg-slate-900 border-slate-700 w-4 h-4 cursor-pointer"
            />
            <label htmlFor="dryRunToggle" className="cursor-pointer select-none">
              <span className="font-bold text-cyan-300 flex items-center gap-1.5">
                <ShieldCheck className="w-4 h-4" />
                Dry Run Safety Mode (Recommended)
              </span>
              <p className="text-[11px] text-slate-400 mt-0.5">
                {dryRun
                  ? 'Validates IAM AssumeRole & Boto3 permissions without modifying resource state.'
                  : '⚠️ REAL AWS ACTION: Resource state will be modified in your AWS account.'}
              </p>
            </label>
          </div>

          {/* Webhook URL Input */}
          <div>
            <label className="block text-slate-300 font-semibold mb-1 flex items-center gap-1.5">
              <Bell className="w-3.5 h-3.5 text-slate-400" />
              Slack / Webhook Notification URL (Optional)
            </label>
            <input
              type="url"
              value={webhookUrl}
              onChange={(e) => setWebhookUrl(e.target.value)}
              placeholder="https://hooks.slack.com/services/..."
              className="w-full bg-slate-900 border border-slate-700/80 rounded-xl px-3 py-2 text-slate-200 focus:outline-none focus:border-cyan-500 font-mono text-[11px] placeholder:text-slate-600"
            />
          </div>

          {/* Confirmation Warning Notice */}
          <div className="flex items-center gap-2 text-[11px] text-slate-400 bg-slate-900/60 p-2.5 rounded-lg border border-slate-800">
            <Info className="w-4 h-4 text-cyan-400 shrink-0" />
            <span>
              Action audit events are logged and dispatched to your FinOps audit trail.
            </span>
          </div>

          {/* Action Buttons */}
          <div className="pt-2 flex justify-end gap-2.5">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-xl text-slate-400 hover:text-white bg-slate-900 hover:bg-slate-800 border border-slate-700 font-semibold"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isLoading}
              className={`px-5 py-2 rounded-xl font-bold text-slate-950 flex items-center gap-2 shadow-lg transition-all disabled:opacity-50 ${
                dryRun
                  ? 'bg-cyan-400 hover:bg-cyan-300 shadow-cyan-500/20'
                  : 'bg-amber-500 hover:bg-amber-400 shadow-amber-500/20'
              }`}
            >
              <Play className={`w-4 h-4 fill-current ${isLoading ? 'animate-spin' : ''}`} />
              <span>{isLoading ? 'Executing Boto3...' : dryRun ? 'Run Safety Test (Dry Run)' : 'Confirm & Apply Fix'}</span>
            </button>
          </div>

        </form>

      </div>
    </div>
  );
}
