import React, { useState } from 'react';
import { ExternalLink, CheckCircle2, ChevronDown, ChevronUp, FileText, BarChart2 } from 'lucide-react';
import { RetrievedEvidenceChunk } from '../types';

interface EvidenceCardProps {
  chunk: RetrievedEvidenceChunk;
  isTopRank?: boolean;
}

export const EvidenceCard: React.FC<EvidenceCardProps> = ({ chunk, isTopRank = false }) => {
  const [showMetrics, setShowMetrics] = useState(false);

  return (
    <div
      className={`rounded-xl border transition-all duration-200 p-4 sm:p-5 ${
        isTopRank
          ? 'bg-white border-teal-200 shadow-sm ring-1 ring-teal-100'
          : 'bg-white border-stone-200 hover:border-stone-300 shadow-xs'
      }`}
    >
      {/* Header Row: Rank indicator, Source Title, NHS Link */}
      <div className="flex items-start justify-between gap-3 mb-3">
        <div className="flex items-center gap-2 flex-wrap">
          <span
            className={`inline-flex items-center justify-center font-semibold text-xs px-2.5 py-0.5 rounded-md ${
              isTopRank
                ? 'bg-teal-700 text-white shadow-2xs'
                : 'bg-stone-100 text-stone-700 border border-stone-200'
            }`}
          >
            Evidence #{chunk.rank}
          </span>
          <h4 className="text-sm sm:text-base font-semibold text-stone-900 leading-snug">
            {chunk.source_title}
          </h4>
          <span className="text-[11px] bg-stone-100 text-stone-600 font-normal px-2 py-0.5 rounded border border-stone-200">
            NHS England
          </span>
        </div>

        <a
          href={chunk.source_url}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1.5 text-xs font-medium text-teal-700 hover:text-teal-900 bg-teal-50 hover:bg-teal-100 px-2.5 py-1 rounded-lg border border-teal-200 transition-colors flex-shrink-0"
        >
          <span>NHS Source</span>
          <ExternalLink className="w-3.5 h-3.5" />
        </a>
      </div>

      {/* Primary Evidence Excerpt Text */}
      <div className="text-sm leading-relaxed text-stone-800 whitespace-pre-line bg-stone-50/70 p-4 rounded-xl border border-stone-200/80 my-3 font-sans">
        <div className="flex items-center gap-1.5 text-xs font-medium text-stone-500 mb-2 pb-1.5 border-b border-stone-200/60">
          <FileText className="w-3.5 h-3.5 text-teal-700" />
          <span>Clinical Guidance Excerpt</span>
        </div>
        <p className="text-stone-800">{chunk.text}</p>
      </div>

      {/* Footer Row: OGL v3.0 note + Progressive disclosure for metrics */}
      <div className="mt-3 pt-2.5 border-t border-stone-100 flex items-center justify-between flex-wrap gap-2 text-xs">
        <div className="flex items-center gap-1.5 text-[11px] text-stone-400">
          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
          <span>Open Government Licence v3.0 Grounding</span>
        </div>

        <button
          type="button"
          onClick={() => setShowMetrics(!showMetrics)}
          className="inline-flex items-center gap-1 text-[11px] font-medium text-stone-500 hover:text-teal-800 transition-colors cursor-pointer"
        >
          <BarChart2 className="w-3 h-3 text-teal-600" />
          <span>{showMetrics ? 'Hide Technical Metrics' : 'Technical Metrics'}</span>
          {showMetrics ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
        </button>
      </div>

      {/* Progressive Disclosure: Technical Scores & Chunk Provenance */}
      {showMetrics && (
        <div className="mt-3 p-3 bg-stone-50 rounded-xl border border-stone-200 text-xs font-mono text-stone-600 space-y-1.5">
          <div className="flex items-center justify-between flex-wrap gap-2">
            <span><strong>Chunk ID:</strong> {chunk.chunk_id}</span>
            <span className="text-teal-800 font-bold"><strong>Reranker Score:</strong> {chunk.rerank_score.toFixed(4)}</span>
          </div>
          <div className="flex items-center justify-between flex-wrap gap-2 text-stone-500 text-[11px]">
            {chunk.raw_dense_score !== undefined && (
              <span><strong>Dense Cosine:</strong> {chunk.raw_dense_score.toFixed(4)}</span>
            )}
            {chunk.lexical_overlap !== undefined && (
              <span><strong>Lexical Overlap:</strong> {(chunk.lexical_overlap * 100).toFixed(1)}%</span>
            )}
            <span><strong>Doc ID:</strong> {chunk.parent_source_id}</span>
          </div>
        </div>
      )}
    </div>
  );
};
export default EvidenceCard;
