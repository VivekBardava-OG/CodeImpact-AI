import React, { useState } from 'react';
import { Sparkles, MessageSquare, Send, CheckCircle, HelpCircle } from 'lucide-react';
import { askQuestion } from '../api';

interface ExplanationPanelProps {
  repoId: string;
  symbolId: string;
  explanation: string;
}

export const ExplanationPanel: React.FC<ExplanationPanelProps> = ({
  repoId,
  symbolId,
  explanation,
}) => {
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState<string | null>(null);
  const [source, setSource] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const sampleQuestions = [
    'What could break if I change this function?',
    'Which tests should I run and why?',
    'Show me the shortest dependency path to tests.',
  ];

  const handleAsk = async (qText?: string) => {
    const query = qText || question;
    if (!query) return;
    try {
      setLoading(true);
      const res = await askQuestion(repoId, symbolId, query);
      setAnswer(res.answer);
      setSource(res.source);
    } catch (err: any) {
      setAnswer(`Error answering query: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 mb-6 shadow-xl space-y-5">
      <div className="flex items-center justify-between pb-3 border-b border-slate-800">
        <div className="flex items-center space-x-2">
          <Sparkles className="w-5 h-5 text-indigo-400" />
          <h2 className="text-base font-semibold text-white">Graph-Grounded Explanation</h2>
        </div>
        <span className="text-[11px] text-slate-400 font-mono">
          Deterministic FalkorDB Grounding
        </span>
      </div>

      {/* Primary Structured Explanation */}
      <div className="bg-slate-950 rounded-xl p-4 border border-slate-800 text-xs text-slate-300 leading-relaxed font-sans whitespace-pre-line space-y-2">
        {explanation}
      </div>

      {/* Interactive Natural Language Q&A */}
      <div className="pt-2 border-t border-slate-800/80">
        <div className="flex items-center gap-2 mb-2.5">
          <MessageSquare className="w-4 h-4 text-brand-400" />
          <span className="text-xs font-semibold text-white">Ask CodeImpact AI About This Component</span>
        </div>

        {/* Suggestion Chips */}
        <div className="flex items-center gap-2 flex-wrap mb-3">
          {sampleQuestions.map((sq, i) => (
            <button
              key={i}
              onClick={() => {
                setQuestion(sq);
                handleAsk(sq);
              }}
              className="text-[11px] text-slate-400 hover:text-white bg-slate-950 border border-slate-800 hover:border-slate-700 px-2.5 py-1 rounded-lg transition-all"
            >
              {sq}
            </button>
          ))}
        </div>

        {/* Question Form */}
        <div className="flex gap-2">
          <input
            type="text"
            placeholder="Ask a question about callers, test paths, or blast radius..."
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleAsk()}
            className="flex-1 bg-slate-950 border border-slate-800 rounded-xl px-4 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
          />
          <button
            onClick={() => handleAsk()}
            disabled={loading || !question}
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold rounded-xl transition-all flex items-center gap-1.5 disabled:opacity-40"
          >
            {loading ? (
              <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            ) : (
              <>
                <Send className="w-3.5 h-3.5" />
                Ask
              </>
            )}
          </button>
        </div>

        {/* Answer Box */}
        {answer && (
          <div className="mt-3 p-3.5 rounded-xl bg-slate-950 border border-indigo-500/30 text-xs text-slate-200">
            <div className="flex items-center justify-between mb-1.5 pb-1.5 border-b border-slate-800 text-[10px] text-slate-400">
              <span className="font-semibold text-indigo-400 uppercase">Answer Grounded in Graph</span>
              <span className="font-mono">{source}</span>
            </div>
            <div className="whitespace-pre-line leading-relaxed">{answer}</div>
          </div>
        )}
      </div>
    </div>
  );
};
