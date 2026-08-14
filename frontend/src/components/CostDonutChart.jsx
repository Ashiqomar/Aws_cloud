import React from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts';
import { PieChart as ChartIcon } from 'lucide-react';

const COLORS = [
  '#06b6d4', // Cyan
  '#10b981', // Emerald
  '#8b5cf6', // Purple
  '#f59e0b', // Amber
  '#ec4899', // Pink
  '#3b82f6', // Blue
  '#6366f1', // Indigo
];

export default function CostDonutChart({ data, totalCost }) {
  if (!data || data.length === 0) {
    return (
      <div className="glass-panel p-6 rounded-2xl border border-slate-800 flex flex-col items-center justify-center min-h-[320px]">
        <ChartIcon className="w-10 h-10 text-slate-600 mb-2" />
        <p className="text-slate-400 text-sm">No cost breakdown data available.</p>
        <p className="text-slate-500 text-xs mt-1">Connect an AWS account or click "Demo Data".</p>
      </div>
    );
  }

  const chartData = data.map((item) => ({
    name: item.service_name,
    value: item.amount,
    percentage: item.percentage,
  }));

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const d = payload[0].payload;
      return (
        <div className="bg-slate-900 border border-slate-700 p-3 rounded-xl shadow-xl text-xs">
          <p className="font-bold text-white mb-1">{d.name}</p>
          <p className="text-cyan-400 font-mono font-semibold">
            ${d.value.toLocaleString('en-US', { minimumFractionDigits: 2 })} / mo
          </p>
          <p className="text-slate-400 text-[11px]">{d.percentage}% of total spending</p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="glass-panel glass-panel-hover p-6 rounded-2xl border border-slate-800 flex flex-col justify-between">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-base font-bold text-white flex items-center gap-2">
            <ChartIcon className="w-4 h-4 text-cyan-400" />
            Cost by Service
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">Distribution of AWS spending</p>
        </div>
        <div className="text-right">
          <span className="text-xs text-slate-400 block">Total</span>
          <span className="text-sm font-extrabold text-cyan-400">
            ${totalCost?.toLocaleString('en-US', { minimumFractionDigits: 2 }) || '0.00'}
          </span>
        </div>
      </div>

      <div className="h-[260px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={chartData}
              cx="50%"
              cy="50%"
              innerRadius={65}
              outerRadius={95}
              paddingAngle={3}
              dataKey="value"
            >
              {chartData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} stroke="#0b0f17" strokeWidth={2} />
              ))}
            </Pie>
            <Tooltip content={<CustomTooltip />} />
            <Legend
              verticalAlign="bottom"
              height={36}
              iconType="circle"
              iconSize={8}
              formatter={(value) => <span className="text-xs text-slate-300 font-medium px-1">{value}</span>}
            />
          </PieChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
