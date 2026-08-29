import React, { useState } from 'react';
import { ExternalLink, CheckCircle2, ChevronDown, ChevronUp, FileText, Activity } from 'lucide-react';
import { RetrievedEvidenceChunk } from '../types';

interface EvidenceCardProps {
  chunk: RetrievedEvidenceChunk;
  isTopRank?: boolean;
}

export const EvidenceCard: React.FC<EvidenceCardProps> = ({ chunk, isTopRank = false }) => {
  const [showResearchDetails, setShowResearchDetails] = useState(false);

  return (
    <div
      className={`rounded-xl border transition-all duration-200 p-4 ${
        isTopRank
          ? 'bg-gradient-to-b from-sky-50/80 via-white to-white border-sky-300 shadow-sm ring-1 ring-sky-200'
          : 'bg-white border-slate-200 hover:border-slate-300 shadow-xs'
      }`}
    >
      {/* Header Row: Rank badge, Clean Source Title, NHS Source Link */}
      <div className="flex items-start justify-between gap-3 mb-2.5">
        <div className="flex items-center gap-2 flex-wrap">
          <span
            className={`inline-flex items-center justify-center font-bold text-xs px-2.5 py-0.5 rounded-md ${
              isTopRank
                ? 'bg-sky-600 text-white shadow-xs'
                : 'bg-slate-100 text-slate-700 border border-slate-200'
            }`}
          >
            #{chunk.rank} Evidence
          </span>
          <h4 className="text-sm font-semibold text-slate-900">{chunk.source_title}</h4>
          <span className="text-[10px] bg-slate-100 text-slate-600 font-medium px-2 py-0.5 rounded border border-slate-200">
            Source: NHS (Active Corpus)
          </span>
        </div>

        <a
          href={chunk.source_url}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1 text-[11px] font-medium text-sky-700 hover:text-sky-900 bg-sky-50 hover:bg-sky-100 px-2 py-1 rounded-md border border-sky-200 transition-colors flex-shrink-0"
        >
          <span>View NHS Page</span>
          <ExternalLink className="w-3 h-3" />
        </a>
      </div>

      {/* Primary Evidence Excerpt Text */}
      <div className="text-xs leading-relaxed text-slate-800 whitespace-pre-line bg-slate-50/50 p-3.5 rounded-lg border border-slate-200 font-sans my-2.5">
        <div className="flex items-center gap-1.5 text-[11px] font-bold text-slate-600 mb-1.5 pb-1 border-b border-slate-200/60">
          <FileText className="w-3.5 h-3.5 text-sky-600" />
          <span>Clinical Guidance Excerpt</span>
        </div>
        {chunk.text}
      </div>

      {/* Collapsible Research Observability Accordion */}
      <div className="mt-2 pt-2 border-t border-slate-100">
        <div className="flex items-center justify-between">
          <button
            type="button"
            onClick={() => setShowResearchDetails(!showResearchDetails)}
            className="inline-flex items-center gap-1 text-[11px] font-medium text-slate-500 hover:text-sky-700 transition-colors cursor-pointer"
          >
            <Activity className="w-3 h-3 text-sky-600" />
            <span>Research & Ranking Observability</span>
            {showResearchDetails ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
          </button>

          <div className="flex items-center gap-1 text-[10px] text-slate-400">
            <CheckCircle2 className="w-3 h-3 text-emerald-600" />
            <span>OGL v3.0 Grounding</span>
          </div>
        </div>

        {showResearchDetails && (
          <div className="mt-2 bg-slate-50 border border-slate-200/80 rounded-lg p-2.5 text-[11px] font-mono text-slate-600 space-y-1">
            <div className="flex items-center justify-between flex-wrap gap-2">
              <span><strong>Chunk ID:</strong> {chunk.chunk_id}</span>
              <span className="text-sky-700 font-bold"><strong>Fused Score:</strong> {chunk.rerank_score.toFixed(4)}</span>
            </div>
            <div className="flex items-center justify-between flex-wrap gap-2 text-slate-500 text-[10px]">
              {chunk.raw_dense_score !== undefined && (
                <span><strong>Dense Cosine:</strong> {chunk.raw_dense_score.toFixed(4)}</span>
              )}
              {chunk.lexical_overlap !== undefined && (
                <span><strong>Lexical Overlap:</strong> {(chunk.lexical_overlap * 100).toFixed(1)}%</span>
              )}
              <span><strong>Document:</strong> {chunk.parent_source_id}</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
