import React, { useState, useEffect } from 'react';
import { Header } from './components/Header';
import { RepoSelector } from './components/RepoSelector';
import { StatsOverview } from './components/StatsOverview';
import { SymbolSelector } from './components/SymbolSelector';
import { ImpactResults } from './components/ImpactResults';
import { DependencyGraph } from './components/DependencyGraph';
import { AffectedTestsList } from './components/AffectedTestsList';
import { ExplanationPanel } from './components/ExplanationPanel';
import { GitDiffView } from './components/GitDiffView';
import { CypherConsole } from './components/CypherConsole';
import {
  HealthStatus,
  Repository,
  SymbolItem,
  ImpactResult,
} from './types';
import {
  checkHealth,
  listRepositories,
  listSymbols,
  analyzeImpact,
} from './api';
import { Sparkles, GitGraph, Info, X } from 'lucide-react';

export const App: React.FC = () => {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [repositories, setRepositories] = useState<Repository[]>([]);
  const [currentRepo, setCurrentRepo] = useState<Repository | null>(null);
  const [symbols, setSymbols] = useState<SymbolItem[]>([]);
  const [selectedSymbol, setSelectedSymbol] = useState<SymbolItem | null>(null);
  const [impactResult, setImpactResult] = useState<ImpactResult | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [indexing, setIndexing] = useState(false);
  const [activeTab, setActiveTab] = useState<'impact' | 'diff' | 'cypher'>('impact');
  const [inspectNode, setInspectNode] = useState<any | null>(null);

  // Health check polling
  useEffect(() => {
    const runHealth = async () => {
      try {
        const h = await checkHealth();
        setHealth(h);
      } catch (e) {
        setHealth({ status: 'unhealthy', connected: false, host: 'localhost', port: 6379 });
      }
    };
    runHealth();
    const interval = setInterval(runHealth, 5000);
    return () => clearInterval(interval);
  }, []);

  // Initial repositories fetch
  useEffect(() => {
    const fetchRepos = async () => {
      try {
        const repos = await listRepositories();
        setRepositories(repos);
        if (repos.length > 0 && !currentRepo) {
          const sample = repos.find((r) => r.is_sample) || repos[0];
          setCurrentRepo(sample);
        }
      } catch (e) {
        console.error('Failed to load repositories', e);
      }
    };
    fetchRepos();
  }, []);

  // Fetch symbols when current repository changes or indexes
  useEffect(() => {
    if (!currentRepo || currentRepo.status !== 'indexed') {
      setSymbols([]);
      setSelectedSymbol(null);
      setImpactResult(null);
      return;
    }

    const fetchSyms = async () => {
      try {
        const res = await listSymbols(currentRepo.repo_id);
        setSymbols(res.symbols);
        // Default select 'authenticate_user' if present for instant demo readiness
        const authSym = res.symbols.find((s) => s.name === 'authenticate_user');
        if (authSym) {
          setSelectedSymbol(authSym);
        } else if (res.symbols.length > 0) {
          setSelectedSymbol(res.symbols[0]);
        }
      } catch (e) {
        console.error('Failed to load symbols', e);
      }
    };
    fetchSyms();
  }, [currentRepo]);

  const handleAnalyze = async (hops: number) => {
    if (!currentRepo || !selectedSymbol) return;
    try {
      setAnalyzing(true);
      const res = await analyzeImpact(currentRepo.repo_id, selectedSymbol.id, hops);
      setImpactResult(res);
    } catch (e) {
      console.error('Failed to analyze impact', e);
    } finally {
      setAnalyzing(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#090d16] text-slate-100 flex flex-col font-sans selection:bg-brand-500 selection:text-white">
      <Header health={health} activeTab={activeTab} setActiveTab={setActiveTab} />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Repository Ingestion Bar */}
        <RepoSelector
          repositories={repositories}
          currentRepo={currentRepo}
          onSelectRepo={(r) => setCurrentRepo(r)}
          onRepoIndexed={(r) => {
            setCurrentRepo(r);
            setRepositories((prev) =>
              prev.map((item) => (item.repo_id === r.repo_id ? r : item))
            );
          }}
          indexing={indexing}
          setIndexing={setIndexing}
        />

        {/* Repository Stats Ribbon */}
        <StatsOverview currentRepo={currentRepo} indexing={indexing} />

        {/* Tab 1: Symbol Impact Analysis */}
        {activeTab === 'impact' && (
          <div>
            {currentRepo?.status === 'indexed' ? (
              <>
                <SymbolSelector
                  symbols={symbols}
                  selectedSymbol={selectedSymbol}
                  onSelectSymbol={(sym) => setSelectedSymbol(sym)}
                  onAnalyze={handleAnalyze}
                  analyzing={analyzing}
                />

                {impactResult && (
                  <div className="space-y-6">
                    {/* Impact Blast Radius & Callers */}
                    <ImpactResults impact={impactResult} />

                    {/* Interactive React Flow Dependency Graph */}
                    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl">
                      <div className="flex items-center justify-between pb-3 border-b border-slate-800 mb-4">
                        <div className="flex items-center space-x-2">
                          <GitGraph className="w-5 h-5 text-indigo-400" />
                          <h2 className="text-base font-semibold text-white">
                            Interactive Multi-Hop Dependency Graph
                          </h2>
                        </div>
                        <span className="text-xs text-slate-400 font-mono">
                          React Flow • Drag, Zoom & Inspect Nodes
                        </span>
                      </div>

                      <DependencyGraph
                        nodes={impactResult.visualization.nodes}
                        edges={impactResult.visualization.edges}
                        onNodeClick={(node) => setInspectNode(node)}
                      />
                    </div>

                    {/* Recommended Tests Suite */}
                    <AffectedTestsList tests={impactResult.affected_tests} />

                    {/* Graph Explanation & Natural Language Q&A */}
                    <ExplanationPanel
                      repoId={currentRepo.repo_id}
                      symbolId={selectedSymbol ? selectedSymbol.id : ''}
                      explanation={impactResult.explanation}
                    />
                  </div>
                )}
              </>
            ) : (
              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-12 text-center shadow-xl">
                <Sparkles className="w-10 h-10 text-brand-400 mx-auto mb-3" />
                <h3 className="text-base font-semibold text-white">Repository Not Yet Indexed</h3>
                <p className="text-xs text-slate-400 max-w-md mx-auto mt-1 mb-6">
                  Click "Load & Index Sample" or enter a public GitHub repository URL above to parse the code into FalkorDB and start impact analysis.
                </p>
              </div>
            )}
          </div>
        )}

        {/* Tab 2: Git Diff Blast Radius */}
        {activeTab === 'diff' && currentRepo && (
          <GitDiffView repoId={currentRepo.repo_id} />
        )}

        {/* Tab 3: Live Cypher Query Console */}
        {activeTab === 'cypher' && <CypherConsole />}
      </main>

      {/* Node Details Inspection Modal Drawer */}
      {inspectNode && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-700 rounded-2xl max-w-md w-full p-5 shadow-2xl relative">
            <button
              onClick={() => setInspectNode(null)}
              className="absolute top-4 right-4 p-1 text-slate-400 hover:text-white"
            >
              <X className="w-5 h-5" />
            </button>
            <div className="flex items-center space-x-2 mb-3">
              <Info className="w-5 h-5 text-indigo-400" />
              <h3 className="text-base font-bold text-white font-mono">
                {inspectNode.data.label}()
              </h3>
            </div>
            <div className="space-y-2 text-xs font-mono text-slate-300 bg-slate-950 p-3.5 rounded-xl border border-slate-800">
              <p>
                <span className="text-slate-500 font-sans">File Path: </span>
                {inspectNode.data.sublabel}
              </p>
              <p>
                <span className="text-slate-500 font-sans">Type: </span>
                {inspectNode.data.symbol_type}
              </p>
              {inspectNode.data.hop_count !== undefined && (
                <p>
                  <span className="text-slate-500 font-sans">Graph Distance: </span>
                  {inspectNode.data.hop_count} Hops
                </p>
              )}
              {inspectNode.data.confidence && (
                <p>
                  <span className="text-slate-500 font-sans">Confidence: </span>
                  {inspectNode.data.confidence}
                </p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Footer */}
      <footer className="border-t border-slate-900 bg-slate-950 py-4 px-6 text-center text-xs text-slate-500">
        CodeImpact AI • Track 1: Agents That Act on Connected Data • FalkorDB Graph Database Engine
      </footer>
    </div>
  );
};

export default App;
