import React from 'react';
import { TestTube, AlertTriangle, ArrowRight, CheckCircle } from 'lucide-react';
import { AffectedTest } from '../types';

interface AffectedTestsListProps {
  tests: AffectedTest[];
}

export const AffectedTestsList: React.FC<AffectedTestsListProps> = ({ tests }) => {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 mb-6 shadow-xl">
      <div className="flex items-center justify-between pb-3 border-b border-slate-800 mb-4">
        <div className="flex items-center space-x-2">
          <TestTube className="w-5 h-5 text-emerald-400" />
          <h2 className="text-base font-semibold text-white">Recommended Test Suite</h2>
          <span className="text-xs px-2 py-0.5 rounded-full font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            {tests.length} Discovered
          </span>
        </div>
        <div className="text-[11px] text-amber-400/90 bg-amber-500/10 border border-amber-500/20 px-2.5 py-1 rounded-lg flex items-center gap-1.5">
          <AlertTriangle className="w-3.5 h-3.5" />
          <span>Tests not yet executed</span>
        </div>
      </div>

      {tests.length === 0 ? (
        <div className="text-center py-8 text-xs text-slate-400">
          No automated tests were found reaching this component in FalkorDB.
          <p className="mt-1 text-slate-500">Consider creating test coverage for this module.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {tests.map((test) => {
            const isHigh = test.confidence === 'high';
            return (
              <div
                key={test.id}
                className="bg-slate-950/80 border border-slate-800 hover:border-slate-700 rounded-xl p-3.5 transition-all"
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-2">
                  <div className="flex items-center space-x-2">
                    <span className="font-mono font-bold text-xs text-emerald-300">
                      {test.name}()
                    </span>
                    <span className="text-xs text-slate-400 font-mono">
                      {test.file_path}:{test.start_line}
                    </span>
                  </div>

                  <div className="flex items-center space-x-2">
                    <span
                      className={`text-[10px] uppercase font-bold px-2 py-0.5 rounded-md border ${
                        isHigh
                          ? 'bg-rose-500/10 text-rose-300 border-rose-500/30'
                          : 'bg-amber-500/10 text-amber-300 border-amber-500/30'
                      }`}
                    >
                      {test.confidence} Confidence ({test.hop_count} {test.hop_count === 1 ? 'hop' : 'hops'})
                    </span>
                    <span className="text-[10px] bg-slate-800 text-slate-400 font-mono px-2 py-0.5 rounded">
                      STATUS: NOT_RUN
                    </span>
                  </div>
                </div>

                <p className="text-xs text-slate-300 mb-2.5 leading-relaxed">
                  {test.recommendation_reason}
                </p>

                {/* Call Path */}
                {test.path && test.path.length > 1 && (
                  <div className="flex items-center flex-wrap gap-1.5 text-[11px] font-mono bg-slate-900/90 px-3 py-1.5 rounded-lg border border-slate-800 text-slate-400">
                    <span className="text-slate-500 text-[10px] uppercase font-sans font-bold">
                      Graph Path:
                    </span>
                    {test.path.map((node, idx) => (
                      <React.Fragment key={node.id}>
                        <span
                          className={
                            idx === 0
                              ? 'text-emerald-400 font-semibold'
                              : idx === test.path.length - 1
                              ? 'text-indigo-400 font-semibold'
                              : 'text-slate-300'
                          }
                        >
                          {node.name}
                        </span>
                        {idx < test.path.length - 1 && (
                          <ArrowRight className="w-3 h-3 text-slate-600 flex-shrink-0" />
                        )}
                      </React.Fragment>
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
