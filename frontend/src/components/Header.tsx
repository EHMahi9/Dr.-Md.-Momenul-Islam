import React, { useState } from 'react';
import { Activity, Database, Sparkles, BookOpen, Info, X, Cpu } from 'lucide-react';
import { HealthResponse } from '../types';

interface HeaderProps {
  health: HealthResponse | null;
}

export const Header: React.FC<HeaderProps> = ({ health }) => {
  const [showSpecsModal, setShowSpecsModal] = useState(false);

  return (
    <header className="bg-white/95 backdrop-blur-md border-b border-stone-200 sticky top-0 z-30">
      {/* Calm Research Protocol Bar */}
      <div className="bg-teal-900 text-teal-100 px-4 py-1.5 text-xs font-medium flex items-center justify-between">
        <div className="max-w-6xl mx-auto w-full flex items-center justify-between gap-2">
          <div className="flex items-center gap-1.5 text-[11px] sm:text-xs">
            <span className="inline-block w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            <span>Clinical Information Prototype &bull; NHS Evidence Retrieval</span>
          </div>
          <div className="text-[11px] text-teal-200/80 hidden sm:block">
            Not for direct medical diagnosis or emergency prescription
          </div>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-4 sm:px-6 py-3 flex items-center justify-between gap-4">
        {/* Brand & Identity */}
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-teal-700 text-white flex items-center justify-center shadow-xs">
            <Activity className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-base sm:text-lg font-semibold text-stone-900 tracking-tight leading-tight">
              Dr. Md. Momenul Islam
            </h1>
            <p className="text-xs text-stone-500 font-normal">
              Clinical Health Intelligence
            </p>
          </div>
        </div>

        {/* Action & Status Controls */}
        <div className="flex items-center gap-2.5 text-xs">
          {/* System Health Dot */}
          <div
            className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border ${
              health
                ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
                : 'bg-stone-100 text-stone-600 border-stone-200'
            }`}
          >
            <span
              className={`w-2 h-2 rounded-full ${
                health ? 'bg-emerald-500' : 'bg-amber-400 animate-ping'
              }`}
            />
            <span className="hidden sm:inline">{health ? 'System Ready' : 'Connecting...'}</span>
          </div>

          {/* Progressive Disclosure: Clinical Architecture Trigger */}
          <button
            type="button"
            onClick={() => setShowSpecsModal(true)}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-stone-600 hover:text-teal-800 bg-stone-100 hover:bg-teal-50 border border-stone-200 hover:border-teal-200 transition-colors cursor-pointer"
            title="View system architecture and active corpus specifications"
          >
            <Info className="w-3.5 h-3.5 text-teal-700" />
            <span className="hidden sm:inline">System Specs</span>
          </button>
        </div>
      </div>

      {/* Progressive Disclosure Modal for Technical & Empirical Specifications */}
      {showSpecsModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-stone-900/40 backdrop-blur-xs animate-in fade-in duration-150">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-xl border border-stone-200 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-stone-100">
              <div className="flex items-center gap-2 text-stone-900 font-semibold text-base">
                <Cpu className="w-5 h-5 text-teal-700" />
                <span>System Architecture &amp; Clinical Specs</span>
              </div>
              <button
                type="button"
                onClick={() => setShowSpecsModal(false)}
                className="p-1 rounded-lg text-stone-400 hover:text-stone-700 hover:bg-stone-100 transition-colors cursor-pointer"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-3 text-xs text-stone-600">
              <div className="p-3 bg-stone-50 rounded-xl border border-stone-200/80 space-y-1.5">
                <div className="flex items-center gap-1.5 font-semibold text-stone-800">
                  <BookOpen className="w-4 h-4 text-teal-700" />
                  <span>Retrieval Architecture &amp; Active Strategy</span>
                </div>
                <p className="text-stone-600 text-[11px] leading-relaxed">
                  <strong>Strategy 5:</strong> Dual Topical-Lexical Anchor with contextual disambiguation (Candidate B).
                </p>
                <p className="font-mono text-[10px] text-stone-500 truncate">
                  Hash: {health?.candidate_b_hash || health?.candidate_hash || '1cc216db...'}
                </p>
              </div>

              <div className="p-3 bg-stone-50 rounded-xl border border-stone-200/80 space-y-1.5">
                <div className="flex items-center gap-1.5 font-semibold text-stone-800">
                  <Database className="w-4 h-4 text-teal-700" />
                  <span>Clinical Knowledge Base</span>
                </div>
                <p className="text-stone-600 text-[11px] leading-relaxed">
                  Active Corpus: <strong>{health?.active_corpus_chunks || 119} verified passages</strong> across 14 NHS conditions under Open Government Licence (OGL) v3.0.
                </p>
              </div>

              <div className="p-3 bg-stone-50 rounded-xl border border-stone-200/80 space-y-1.5">
                <div className="flex items-center gap-1.5 font-semibold text-stone-800">
                  <Sparkles className="w-4 h-4 text-teal-700" />
                  <span>Model Stack &amp; Safety Guardrails</span>
                </div>
                <ul className="list-disc list-inside text-[11px] space-y-1 text-stone-600">
                  <li>Embedding: <code className="text-stone-700 font-mono">intfloat/multilingual-e5-small</code></li>
                  <li>Reranker: <code className="text-stone-700 font-mono">BAAI/bge-reranker-v2-m3</code></li>
                  <li>LLM Generation: <strong className="text-stone-800">Locked / Disabled</strong> (zero synthetic hallucination risk)</li>
                </ul>
              </div>

              <div className="p-3 bg-stone-50 rounded-xl border border-stone-200/80 flex items-center justify-between text-[11px]">
                <span className="font-medium text-stone-700">Environment:</span>
                <span className="font-mono text-stone-600">{health?.environment || 'production'} &bull; v{health?.version || '0.7.0'}</span>
              </div>
            </div>

            <div className="pt-2 flex justify-end">
              <button
                type="button"
                onClick={() => setShowSpecsModal(false)}
                className="px-4 py-2 bg-teal-700 hover:bg-teal-800 text-white rounded-xl text-xs font-semibold transition-colors cursor-pointer"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </header>
  );
};
export default Header;
