import React, { useState } from 'react';
import { GitCompare, Play, AlertCircle, CheckCircle2, ArrowRight } from 'lucide-react';
import { DiffResult } from '../types';
import { analyzeDiff } from '../api';

interface GitDiffViewProps {
  repoId: string;
}

const SAMPLE_DIFF = `diff --git a/auth/security.py b/auth/security.py
index e69de29..b1a8d12 100644
--- a/auth/security.py
+++ b/auth/security.py
@@ -19,4 +19,6 @@ def authenticate_user(username: str, password: str) -> Optional[User]:
+    # Updated password validation security threshold
+    # This contract change affects authentication callers
`;

export const GitDiffView: React.FC<GitDiffViewProps> = ({ repoId }) => {
  const [diffText, setDiffText] = useState(SAMPLE_DIFF);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<DiffResult | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleRunDiff = async () => {
    if (!diffText.trim()) return;
    try {
      setLoading(true);
      setErrorMsg(null);
      const res = await analyzeDiff(repoId, diffText);
      setResult(res);
    } catch (err: any) {
      setErrorMsg(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 mb-6 shadow-xl space-y-5">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-3 border-b border-slate-800 gap-3">
        <div>
          <h2 className="text-base font-semibold text-white flex items-center gap-2">
            <GitCompare className="w-5 h-5 text-indigo-400" />
            Git Diff Blast Radius Analysis
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Paste a standard unified git diff to discover modified symbols and their combined blast radius
          </p>
        </div>

        <button
          onClick={() => setDiffText(SAMPLE_DIFF)}
          className="text-xs text-slate-400 hover:text-white bg-slate-950 border border-slate-800 px-3 py-1.5 rounded-lg transition-all"
        >
          Load Sample Diff
        </button>
      </div>

      {errorMsg && (
        <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-xs text-rose-300 flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-rose-400 flex-shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      <div>
        <label className="block text-xs font-medium text-slate-300 mb-1.5">
          Unified Git Diff Content:
        </label>
        <textarea
          rows={7}
          value={diffText}
          onChange={(e) => setDiffText(e.target.value)}
          placeholder="diff --git a/... b/..."
          className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 font-mono text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
        />
      </div>

      <div className="flex justify-end">
        <button
          onClick={handleRunDiff}
          disabled={loading || !diffText.trim()}
          className="px-6 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold rounded-xl shadow-lg transition-all flex items-center gap-2 disabled:opacity-40"
        >
          {loading ? (
            <>
              <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              Mapping Diff to FalkorDB...
            </>
          ) : (
            <>
              <Play className="w-3.5 h-3.5 fill-white" />
              Analyze Diff Impact
            </>
          )}
        </button>
      </div>

      {result && (
        <div className="pt-4 border-t border-slate-800 space-y-4">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
              <span className="text-xs text-slate-400">Changed Files</span>
              <p className="text-lg font-bold text-white mt-0.5">{result.changed_files_count}</p>
            </div>
            <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
              <span className="text-xs text-slate-400">Enclosed Symbols</span>
              <p className="text-lg font-bold text-indigo-400 mt-0.5">{result.changed_symbols_count}</p>
            </div>
            <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
              <span className="text-xs text-slate-400">Total Affected Callers</span>
              <p className="text-lg font-bold text-amber-400 mt-0.5">{result.aggregate_affected_symbols_count}</p>
            </div>
            <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
              <span className="text-xs text-slate-400">Affected Tests</span>
              <p className="text-lg font-bold text-emerald-400 mt-0.5">{result.aggregate_affected_tests_count}</p>
            </div>
          </div>

          {/* Changed Symbols Identified */}
          <div>
            <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
              Modified Symbols Identified:
            </h4>
            <div className="space-y-1.5">
              {result.changed_symbols.map((sym, idx) => (
                <div
                  key={idx}
                  className="bg-slate-950 p-2.5 rounded-xl border border-slate-800 flex items-center justify-between text-xs"
                >
                  <span className="font-mono text-white font-bold">{sym.name}()</span>
                  <span className="text-slate-400 font-mono">
                    {sym.file_path} (Lines {sym.start_line}–{sym.end_line})
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
