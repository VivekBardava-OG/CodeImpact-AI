import React from 'react';
import { Database, Activity, GitGraph, Sparkles } from 'lucide-react';
import { HealthStatus } from '../types';

interface HeaderProps {
  health: HealthStatus | null;
  activeTab: 'impact' | 'diff' | 'cypher';
  setActiveTab: (tab: 'impact' | 'diff' | 'cypher') => void;
}

export const Header: React.FC<HeaderProps> = ({ health, activeTab, setActiveTab }) => {
  return (
    <header className="border-b border-slate-800 bg-slate-900/90 backdrop-blur sticky top-0 z-50 px-6 py-3.5 flex items-center justify-between">
      <div className="flex items-center space-x-4">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-brand-600 to-indigo-600 flex items-center justify-center shadow-lg shadow-brand-500/20">
            <GitGraph className="w-6 h-6 text-white" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-xl font-bold tracking-tight text-white">CodeImpact AI</h1>
              <span className="text-xs px-2 py-0.5 rounded-full font-medium bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                Track 1
              </span>
            </div>
            <p className="text-xs text-slate-400">
              Deterministic Codebase Impact Analysis Powered by <span className="text-brand-400 font-semibold">FalkorDB</span> Graph
            </p>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="hidden md:flex items-center ml-8 bg-slate-950 p-1 rounded-lg border border-slate-800">
          <button
            onClick={() => setActiveTab('impact')}
            className={`px-3.5 py-1.5 text-xs font-medium rounded-md transition-all ${
              activeTab === 'impact'
                ? 'bg-slate-800 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Symbol Impact
          </button>
          <button
            onClick={() => setActiveTab('diff')}
            className={`px-3.5 py-1.5 text-xs font-medium rounded-md transition-all ${
              activeTab === 'diff'
                ? 'bg-slate-800 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Git Diff Blast Radius
          </button>
          <button
            onClick={() => setActiveTab('cypher')}
            className={`px-3.5 py-1.5 text-xs font-medium rounded-md transition-all ${
              activeTab === 'cypher'
                ? 'bg-slate-800 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Live Cypher Queries
          </button>
        </div>
      </div>

      {/* Database Connection Pill */}
      <div className="flex items-center space-x-3">
        {health?.connected ? (
          <div className="flex items-center space-x-2 bg-emerald-950/40 border border-emerald-500/30 px-3 py-1.5 rounded-full text-xs text-emerald-300">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
            </span>
            <Database className="w-3.5 h-3.5" />
            <span className="font-medium">FalkorDB Connected</span>
            <span className="text-emerald-500/80">({health.latency_ms}ms)</span>
          </div>
        ) : (
          <div className="flex items-center space-x-2 bg-rose-950/40 border border-rose-500/30 px-3 py-1.5 rounded-full text-xs text-rose-300">
            <span className="h-2 w-2 rounded-full bg-rose-500"></span>
            <Activity className="w-3.5 h-3.5" />
            <span className="font-medium">FalkorDB Disconnected</span>
          </div>
        )}
      </div>
    </header>
  );
};
