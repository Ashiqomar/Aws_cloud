import React from 'react';
import { CheckCircle2, AlertCircle, Info, X } from 'lucide-react';

export default function Toast({ toast, onClose }) {
  if (!toast) return null;

  const iconMap = {
    success: <CheckCircle2 className="w-5 h-5 text-emerald-400" />,
    error: <AlertCircle className="w-5 h-5 text-rose-400" />,
    info: <Info className="w-5 h-5 text-cyan-400" />,
  };

  const borderMap = {
    success: 'border-emerald-800 bg-emerald-950/90 text-emerald-200',
    error: 'border-rose-800 bg-rose-950/90 text-rose-200',
    info: 'border-cyan-800 bg-cyan-950/90 text-cyan-200',
  };

  return (
    <div className="fixed bottom-5 right-5 z-50 animate-slideUp">
      <div className={`flex items-center gap-3 px-4 py-3 rounded-xl border shadow-xl backdrop-blur-md text-xs font-medium ${borderMap[toast.type] || borderMap.info}`}>
        {iconMap[toast.type]}
        <span>{toast.message}</span>
        <button onClick={onClose} className="ml-2 hover:opacity-75">
          <X className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}
