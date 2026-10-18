import React from 'react';
import {
  ShieldAlert,
  ArrowRight,
  FileCode,
  Network,
  Layers,
  Flame,
  CheckCircle2,
} from 'lucide-react';
import { ImpactResult } from '../types';

interface ImpactResultsProps {
  impact: ImpactResult;
}

export const ImpactResults: React.FC<ImpactResultsProps> = ({ impact }) => {
  const { target, blast_radius_risk, metrics, direct_dependents, indirect_dependents, affected_files, high_impact_shared_modules } = impact;

  const getRiskColor = (risk: string) => {
    switch (risk) {
      case 'HIGH':
        return 'text-rose-400 bg-rose-500/10 border-rose-500/30';
      case 'MEDIUM':
        return 'text-amber-400 bg-amber-500/10 border-amber-500/30';
      default:
        return 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30';
    }
  };

  return (
    <div className="space-y-6 mb-6">
      {/* Target & Blast Radius Header Banner */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 pb-4 border-b border-slate-800">
          <div className="flex-1">
            <div className="flex items-center space-x-2">
              <span className="text-xs uppercase font-bold tracking-wider text-slate-400">
                Target Under Inspection
              </span>
              <span className="text-xs px-2 py-0.5 rounded-md font-mono bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                {target.symbol_type}
              </span>
            </div>
            <h2 className="text-xl font-bold font-mono text-white mt-1">
              {target.name}(<span className="text-slate-400">{target.parameters}</span>)
            </h2>
            <p className="text-xs font-mono text-slate-400 mt-0.5">
              {target.file_path} : Lines {target.start_line}–{target.end_line}
            </p>
          </div>

          <div className="flex items-center space-x-3">
            <div className={`px-4 py-2.5 rounded-xl border flex items-center gap-2.5 ${getRiskColor(blast_radius_risk)}`}>
              <Flame className="w-5 h-5" />
              <div className="flex flex-col">
                <p className="text-[10px] uppercase font-bold tracking-wider">Blast Radius Risk</p>
                <p className="text-sm font-extrabold">{blast_radius_risk}</p>
                {impact.risk_evidence && (
                  <p className="text-[9px] font-medium opacity-80 max-w-[200px] leading-tight mt-0.5">
                    {impact.risk_evidence}
                  </p>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Impact Metric Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-4">
          <div className="bg-slate-950 p-3 rounded-xl border border-slate-800/80">
            <span className="text-xs text-slate-400">Direct Callers</span>
            <p className="text-xl font-bold text-amber-400 mt-1">{metrics.direct_dependents_count}</p>
            <span className="text-[10px] text-slate-500 font-medium">1 graph hop away</span>
          </div>

          <div className="bg-slate-950 p-3 rounded-xl border border-slate-800/80">
            <span className="text-xs text-slate-400">Transitive Callers</span>
            <p className="text-xl font-bold text-indigo-400 mt-1">{metrics.indirect_dependents_count}</p>
            <span className="text-[10px] text-slate-500 font-medium">2 to {metrics.max_graph_hops} hops</span>
          </div>

          <div className="bg-slate-950 p-3 rounded-xl border border-slate-800/80">
            <span className="text-xs text-slate-400">Affected Tests</span>
            <p className="text-xl font-bold text-emerald-400 mt-1">{metrics.potentially_affected_tests_count}</p>
            <span className="text-[10px] text-slate-500 font-medium">to execute</span>
          </div>

          <div className="bg-slate-950 p-3 rounded-xl border border-slate-800/80">
            <span className="text-xs text-slate-400">Affected Files</span>
            <p className="text-xl font-bold text-blue-400 mt-1">{metrics.affected_files_count}</p>
            <span className="text-[10px] text-slate-500 font-medium">repository modules</span>
          </div>
        </div>
      </div>

      {/* Two Column Breakdown: Direct Callers & Transitive Dependents */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Direct Dependents */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800 mb-3">
            <div className="flex items-center space-x-2">
              <Network className="w-4 h-4 text-amber-400" />
              <h3 className="text-sm font-semibold text-white">Direct Dependents (1 Hop)</h3>
            </div>
            <span className="text-xs font-mono text-amber-400 bg-amber-500/10 px-2 py-0.5 rounded-full border border-amber-500/20">
              {direct_dependents.length}
            </span>
          </div>

          {direct_dependents.length === 0 ? (
            <p className="text-xs text-slate-500 py-4 text-center">No direct callers found in the codebase.</p>
          ) : (
            <div className="space-y-2.5">
              {direct_dependents.map((dep) => (
                <div
                  key={dep.id}
                  className="p-3 rounded-xl bg-slate-950/80 border border-slate-800 flex items-center justify-between"
                >
                  <div>
                    <span className="text-xs font-mono font-bold text-white">{dep.name}()</span>
                    <p className="text-[11px] font-mono text-slate-400 mt-0.5">{dep.file_path}</p>
                  </div>
                  <span className="text-[10px] uppercase font-bold text-amber-400 bg-amber-500/10 px-2 py-0.5 rounded border border-amber-500/20">
                    Verified CALLS
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Transitive Dependents */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800 mb-3">
            <div className="flex items-center space-x-2">
              <Layers className="w-4 h-4 text-indigo-400" />
              <h3 className="text-sm font-semibold text-white">Indirect Multi-Hop Dependents</h3>
            </div>
            <span className="text-xs font-mono text-indigo-400 bg-indigo-500/10 px-2 py-0.5 rounded-full border border-indigo-500/20">
              {indirect_dependents.length}
            </span>
          </div>

          {indirect_dependents.length === 0 ? (
            <p className="text-xs text-slate-500 py-4 text-center">No transitive callers found.</p>
          ) : (
            <div className="space-y-2.5 max-h-64 overflow-y-auto pr-1">
              {indirect_dependents.map((dep) => (
                <div
                  key={dep.id}
                  className="p-3 rounded-xl bg-slate-950/80 border border-slate-800 space-y-1.5"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-mono font-bold text-white">{dep.name}()</span>
                    <span className="text-[10px] uppercase font-bold text-indigo-300 bg-indigo-500/10 px-2 py-0.5 rounded border border-indigo-500/20">
                      {dep.hop_count} Hops Away
                    </span>
                  </div>
                  <p className="text-[11px] font-mono text-slate-400">{dep.file_path}</p>
                  {dep.path && (
                    <div className="flex items-center gap-1 text-[10px] font-mono text-slate-500 bg-slate-900 px-2 py-1 rounded">
                      {dep.path.map((node, i) => (
                        <React.Fragment key={node.id}>
                          <span className={i === 0 ? 'text-indigo-400' : 'text-slate-300'}>
                            {node.name}
                          </span>
                          {i < dep.path.length - 1 && <ArrowRight className="w-2.5 h-2.5 text-slate-600" />}
                        </React.Fragment>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
