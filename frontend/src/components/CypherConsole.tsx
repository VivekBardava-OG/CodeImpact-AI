import React, { useState, useEffect } from 'react';
import { Terminal, Database, Clock, RefreshCw, CheckCircle, ExternalLink } from 'lucide-react';
import { CypherRecord } from '../types';
import { getCypherHistory } from '../api';

export const CypherConsole: React.FC = () => {
  const [history, setHistory] = useState<CypherRecord[]>([]);
  const [loading, setLoading] = useState(false);

  const fetchHistory = async () => {
    try {
      setLoading(true);
      const records = await getCypherHistory();
      setHistory(records);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory();
    const interval = setInterval(fetchHistory, 4000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 mb-6 shadow-xl space-y-5">
      <div className="flex items-center justify-between pb-3 border-b border-slate-800">
        <div className="flex items-center space-x-2">
          <Terminal className="w-5 h-5 text-brand-400" />
          <h2 className="text-base font-semibold text-white">Live FalkorDB Cypher Telemetry</h2>
          <span className="text-xs px-2 py-0.5 rounded-full font-mono bg-brand-500/10 text-brand-400 border border-brand-500/20">
            Real Graph Queries
          </span>
        </div>
        <button
          onClick={fetchHistory}
          disabled={loading}
          className="p-1.5 text-slate-400 hover:text-white bg-slate-950 border border-slate-800 rounded-lg transition-all"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      <p className="text-xs text-slate-400">
        Every impact traversal, test discovery, and symbol lookup is executed directly as OpenCypher queries on FalkorDB.
        Below is the real-time execution log from the FalkorDB query engine.
      </p>

      {history.length === 0 ? (
        <div className="text-center py-10 text-xs text-slate-500 font-mono">
          No Cypher queries recorded yet. Index a repository or run an impact analysis above to observe queries.
        </div>
      ) : (
        <div className="space-y-3 max-h-[500px] overflow-y-auto pr-1">
          {history.map((record, idx) => (
            <div
              key={idx}
              className="bg-slate-950 border border-slate-800 rounded-xl p-3.5 font-mono text-xs space-y-2 hover:border-slate-700 transition-all"
            >
              <div className="flex items-center justify-between text-[11px] text-slate-400">
                <span className="flex items-center gap-1.5 text-brand-400 font-semibold">
                  <Database className="w-3.5 h-3.5" />
                  CYPHER QUERY #{history.length - idx}
                </span>
                <div className="flex items-center space-x-3 text-slate-500">
                  <span className="flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    {record.execution_time_ms} ms
                  </span>
                  <span>{record.rows_returned} rows</span>
                </div>
              </div>

              <pre className="text-slate-200 bg-slate-900/90 p-3 rounded-lg overflow-x-auto text-[11px] leading-relaxed border border-slate-800/80">
                {record.query.trim()}
              </pre>

              {record.params && Object.keys(record.params).length > 0 && (
                <div className="text-[11px] text-slate-400">
                  <span className="text-slate-500 font-sans font-bold text-[10px] uppercase">
                    Parameters:{' '}
                  </span>
                  <span className="text-indigo-300">{JSON.stringify(record.params)}</span>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
