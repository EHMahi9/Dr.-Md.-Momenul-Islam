import React from 'react';
import { ShieldAlert, Activity, Database, Sparkles, BookOpen } from 'lucide-react';
import { HealthResponse } from '../types';

interface HeaderProps {
  health: HealthResponse | null;
}

export const Header: React.FC<HeaderProps> = ({ health }) => {
  return (
    <header className="bg-white border-b border-slate-200 sticky top-0 z-20 shadow-sm">
      {/* Top Banner: Research Prototype Warning */}
      <div className="bg-amber-500 text-amber-950 px-4 py-1.5 text-xs font-semibold flex items-center justify-center gap-2 shadow-inner">
        <ShieldAlert className="w-4 h-4 text-amber-950 flex-shrink-0" />
        <span>RESEARCH PROTOTYPE — NOT FOR MEDICAL DECISION-MAKING. ALL LLM GENERATION IS STRICTLY DISABLED.</span>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3.5 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-sky-700 to-sky-500 flex items-center justify-center text-white shadow-md">
            <Activity className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold text-slate-900 tracking-tight">Dr. Md. Momenul Islam</h1>
              <span className="bg-sky-100 text-sky-800 text-[10px] font-bold px-2 py-0.5 rounded-full uppercase tracking-wider border border-sky-200">
                Phase 6A
              </span>
            </div>
            <p className="text-xs text-slate-500 font-medium">
              Multilingual Clinical Evidence Retrieval System (Bangla · Banglish · English)
            </p>
          </div>
        </div>

        {/* System & Retrieval Status Badges */}
        <div className="flex items-center flex-wrap gap-2 text-xs">
          <div className="flex items-center gap-1.5 bg-slate-100 text-slate-700 px-2.5 py-1 rounded-lg border border-slate-200">
            <Database className="w-3.5 h-3.5 text-sky-600" />
            <span>Corpus: <strong>{health?.corpus_chunks_loaded ?? 68} Chunks</strong> (NHS)</span>
          </div>

          <div className="flex items-center gap-1.5 bg-sky-50 text-sky-800 px-2.5 py-1 rounded-lg border border-sky-200 font-mono text-[11px]">
            <BookOpen className="w-3.5 h-3.5 text-sky-600" />
            <span>Strategy: <strong>Dual-Anchor Fusion</strong></span>
          </div>

          <div className="flex items-center gap-1.5 bg-slate-100 text-slate-600 px-2.5 py-1 rounded-lg border border-slate-200">
            <Sparkles className="w-3.5 h-3.5 text-slate-400" />
            <span>Generation: <strong className="text-rose-600">Disabled</strong></span>
          </div>
        </div>
      </div>
    </header>
  );
};
