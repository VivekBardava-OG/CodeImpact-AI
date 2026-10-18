import React, { useState } from 'react';
import { Search, Filter, Play, SlidersHorizontal, Code2 } from 'lucide-react';
import { SymbolItem } from '../types';

interface SymbolSelectorProps {
  symbols: SymbolItem[];
  selectedSymbol: SymbolItem | null;
  onSelectSymbol: (symbol: SymbolItem) => void;
  onAnalyze: (hops: number) => void;
  analyzing: boolean;
}

export const SymbolSelector: React.FC<SymbolSelectorProps> = ({
  symbols,
  selectedSymbol,
  onSelectSymbol,
  onAnalyze,
  analyzing,
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [typeFilter, setTypeFilter] = useState<string>('all');
  const [maxHops, setMaxHops] = useState<number>(5);

  const filteredSymbols = symbols.filter((s) => {
    const matchesSearch =
      s.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      s.file_path.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesType =
      typeFilter === 'all'
        ? true
        : typeFilter === 'test'
        ? s.is_test
        : s.symbol_type === typeFilter && !s.is_test;
    return matchesSearch && matchesType;
  });

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 mb-6 shadow-xl">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-800 mb-4 gap-3">
        <div>
          <h2 className="text-base font-semibold text-white flex items-center gap-2">
            <Code2 className="w-5 h-5 text-indigo-400" />
            Select Target Component
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Choose a function, method, or class to inspect its blast radius and test coverage
          </p>
        </div>

        {/* Max Graph Hops Traversals */}
        <div className="flex items-center space-x-3 bg-slate-950 px-3 py-1.5 rounded-xl border border-slate-800">
          <SlidersHorizontal className="w-3.5 h-3.5 text-slate-400" />
          <span className="text-xs text-slate-300 font-medium">Traversal Depth:</span>
          <span className="text-xs font-bold text-brand-400">{maxHops} Hops</span>
          <input
            type="range"
            min="1"
            max="8"
            value={maxHops}
            onChange={(e) => setMaxHops(parseInt(e.target.value))}
            className="w-20 accent-brand-500 cursor-pointer"
          />
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row gap-3 mb-4">
        <div className="relative flex-1">
          <Search className="w-4 h-4 text-slate-500 absolute left-3.5 top-3" />
          <input
            type="text"
            placeholder="Search function or file name (e.g. authenticate_user)..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-10 pr-4 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
          />
        </div>

        {/* Filter Pills */}
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 sm:pb-0">
          {['all', 'function', 'class', 'method', 'test'].map((type) => (
            <button
              key={type}
              onClick={() => setTypeFilter(type)}
              className={`px-3 py-2 rounded-xl text-xs font-medium capitalize transition-all whitespace-nowrap ${
                typeFilter === type
                  ? 'bg-slate-800 text-white border border-slate-700 shadow-sm'
                  : 'bg-slate-950 text-slate-400 border border-slate-800 hover:text-white'
              }`}
            >
              {type}
            </button>
          ))}
        </div>
      </div>

      {/* Search Result List */}
      <div className="max-h-56 overflow-y-auto space-y-1.5 pr-1 mb-4">
        {filteredSymbols.length === 0 ? (
          <div className="text-center py-8 text-xs text-slate-500">
            No symbols match your search criteria.
          </div>
        ) : (
          filteredSymbols.slice(0, 30).map((sym) => {
            const isSelected = selectedSymbol?.id === sym.id;
            return (
              <div
                key={sym.id}
                onClick={() => onSelectSymbol(sym)}
                className={`p-2.5 rounded-xl border cursor-pointer flex items-center justify-between transition-all ${
                  isSelected
                    ? 'bg-indigo-950/40 border-indigo-500/60 text-white shadow-sm'
                    : 'bg-slate-950/60 border-slate-800 text-slate-300 hover:bg-slate-800/40 hover:border-slate-700'
                }`}
              >
                <div className="flex items-center space-x-2.5 overflow-hidden">
                  <span
                    className={`text-[10px] uppercase font-semibold px-2 py-0.5 rounded-md ${
                      sym.is_test
                        ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                        : sym.symbol_type === 'class'
                        ? 'bg-purple-500/10 text-purple-400 border border-purple-500/20'
                        : 'bg-blue-500/10 text-blue-400 border border-blue-500/20'
                    }`}
                  >
                    {sym.is_test ? 'test' : sym.symbol_type}
                  </span>
                  <div className="truncate">
                    <span className="font-semibold text-xs text-white">{sym.name}</span>
                    <span className="text-xs text-slate-400 ml-2 font-mono truncate">
                      {sym.file_path}:{sym.start_line}
                    </span>
                  </div>
                </div>

                {isSelected && (
                  <span className="text-[11px] font-medium text-indigo-400 px-2 py-0.5 bg-indigo-500/10 rounded-md border border-indigo-500/20">
                    Selected
                  </span>
                )}
              </div>
            );
          })
        )}
      </div>

      {/* Action Footer */}
      <div className="flex flex-col sm:flex-row items-center justify-between pt-3 border-t border-slate-800 gap-3">
        <div className="text-xs text-slate-400">
          {selectedSymbol ? (
            <span>
              Target: <strong className="text-white font-mono">{selectedSymbol.name}()</strong> in{' '}
              <span className="text-slate-300 font-mono">{selectedSymbol.file_path}</span>
            </span>
          ) : (
            <span>Please select a symbol above to initiate Cypher analysis</span>
          )}
        </div>

        <button
          onClick={() => onAnalyze(maxHops)}
          disabled={!selectedSymbol || analyzing}
          className="w-full sm:w-auto px-6 py-2.5 bg-gradient-to-r from-brand-600 to-indigo-600 hover:from-brand-500 hover:to-indigo-500 text-white text-xs font-semibold rounded-xl shadow-lg shadow-indigo-600/20 transition-all flex items-center justify-center gap-2 disabled:opacity-40"
        >
          {analyzing ? (
            <>
              <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              Traversing Graph in FalkorDB...
            </>
          ) : (
            <>
              <Play className="w-3.5 h-3.5 fill-white" />
              Analyze Blast Radius
            </>
          )}
        </button>
      </div>
    </div>
  );
};
