import React, { useState } from 'react';
import { X, ShieldCheck, Key, Building2, HelpCircle } from 'lucide-react';

export default function ConnectModal({ isOpen, onClose, onConnect, isLoading }) {
  const [formData, setFormData] = useState({
    account_id: '123456789012',
    organization_name: 'Acme Cloud Production',
    role_arn: 'arn:aws:iam::123456789012:role/FinOpsCrossAccountRole',
    external_id: 'finops-ext-key-99',
  });

  if (!isOpen) return null;

  const handleSubmit = (e) => {
    e.preventDefault();
    onConnect(formData);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-fadeIn">
      <div className="glass-panel w-full max-w-lg rounded-2xl border border-slate-700/80 shadow-2xl p-6 relative">
        
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute right-4 top-4 text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800 transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Title */}
        <div className="flex items-center gap-3 mb-6">
          <div className="p-2.5 rounded-xl bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
            <ShieldCheck className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-white">Connect AWS Account</h3>
            <p className="text-xs text-slate-400">Cross-account AssumeRole credentials</p>
          </div>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4 text-xs">
          
          <div>
            <label className="block text-slate-300 font-semibold mb-1">
              Organization / Account Label
            </label>
            <div className="relative">
              <Building2 className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                required
                value={formData.organization_name}
                onChange={(e) => setFormData({ ...formData, organization_name: e.target.value })}
                placeholder="e.g. Acme Production"
                className="w-full bg-slate-900 border border-slate-700 rounded-xl pl-9 pr-3 py-2 text-slate-200 focus:outline-none focus:border-cyan-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-slate-300 font-semibold mb-1">
              AWS Account ID (12 digits)
            </label>
            <input
              type="text"
              required
              maxLength={12}
              pattern="\d{12}"
              value={formData.account_id}
              onChange={(e) => setFormData({ ...formData, account_id: e.target.value })}
              placeholder="123456789012"
              className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 font-mono text-slate-200 focus:outline-none focus:border-cyan-500"
            />
          </div>

          <div>
            <label className="block text-slate-300 font-semibold mb-1">
              IAM Role ARN
            </label>
            <input
              type="text"
              required
              value={formData.role_arn}
              onChange={(e) => setFormData({ ...formData, role_arn: e.target.value })}
              placeholder="arn:aws:iam::123456789012:role/FinOpsCrossAccountRole"
              className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 font-mono text-slate-200 focus:outline-none focus:border-cyan-500"
            />
          </div>

          <div>
            <label className="block text-slate-300 font-semibold mb-1">
              External ID
            </label>
            <div className="relative">
              <Key className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                required
                value={formData.external_id}
                onChange={(e) => setFormData({ ...formData, external_id: e.target.value })}
                placeholder="finops-ext-secret"
                className="w-full bg-slate-900 border border-slate-700 rounded-xl pl-9 pr-3 py-2 font-mono text-slate-200 focus:outline-none focus:border-cyan-500"
              />
            </div>
          </div>

          {/* IAM Guidance Notice */}
          <div className="p-3 rounded-xl bg-slate-900/90 border border-slate-800 text-[11px] text-slate-400 space-y-1">
            <div className="flex items-center gap-1.5 text-cyan-400 font-semibold">
              <HelpCircle className="w-3.5 h-3.5" />
              <span>How AssumeRole Security Works</span>
            </div>
            <p>
              Your AWS account trusts our IAM principal via the External ID. No long-term AWS access keys are stored or exposed.
            </p>
          </div>

          {/* Actions */}
          <div className="pt-2 flex justify-end gap-2">
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
              className="px-5 py-2 rounded-xl text-slate-950 font-bold bg-cyan-500 hover:bg-cyan-400 shadow-lg shadow-cyan-500/20 disabled:opacity-50"
            >
              {isLoading ? 'Validating STS...' : 'Verify & Connect'}
            </button>
          </div>

        </form>
      </div>
    </div>
  );
}
