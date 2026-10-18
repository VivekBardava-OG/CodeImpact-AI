import React from 'react';
import { FileCode2, Code, TestTube, Network } from 'lucide-react';
import { Repository } from '../types';

interface StatsOverviewProps {
  currentRepo: Repository | null;
  indexing: boolean;
}

export const StatsOverview: React.FC<StatsOverviewProps> = ({ currentRepo, indexing }) => {
  if (!currentRepo) return null;

  const stats = [
    {
      label: 'Python Files',
      value: currentRepo.total_files ?? 0,
      icon: FileCode2,
      color: 'text-blue-400',
      bg: 'bg-blue-500/10 border-blue-500/20',
    },
    {
      label: 'Extracted Symbols',
      value: currentRepo.total_symbols ?? 0,
      icon: Code,
      color: 'text-purple-400',
      bg: 'bg-purple-500/10 border-purple-500/20',
    },
    {
      label: 'Discovered Tests',
      value: currentRepo.total_tests ?? 0,
      icon: TestTube,
      color: 'text-emerald-400',
      bg: 'bg-emerald-500/10 border-emerald-500/20',
    },
    {
      label: 'FalkorDB Relationships',
      value: currentRepo.total_relationships ?? 0,
      icon: Network,
      color: 'text-amber-400',
      bg: 'bg-amber-500/10 border-amber-500/20',
    },
  ];

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-3.5 mb-6">
      {stats.map((s, idx) => {
        const Icon = s.icon;
        return (
          <div
            key={idx}
            className={`p-3.5 rounded-xl border ${s.bg} flex items-center justify-between transition-all`}
          >
            <div>
              <p className="text-xs font-medium text-slate-400">{s.label}</p>
              <p className="text-xl font-bold text-white mt-0.5">
                {indexing ? (
                  <span className="text-slate-500 text-sm animate-pulse">indexing...</span>
                ) : (
                  s.value
                )}
              </p>
            </div>
            <div className={`p-2.5 rounded-lg bg-slate-900/60 ${s.color}`}>
              <Icon className="w-5 h-5" />
            </div>
          </div>
        );
      })}
    </div>
  );
};
