import React from 'react';
import { ExternalLink, CheckCircle2 } from 'lucide-react';
import { RetrievedEvidenceChunk } from '../types';

interface EvidenceCardProps {
  chunk: RetrievedEvidenceChunk;
  isTopRank?: boolean;
}

export const EvidenceCard: React.FC<EvidenceCardProps> = ({ chunk, isTopRank = false }) => {
  return (
    <div
      className={`rounded-xl border transition-all duration-200 p-4 ${
        isTopRank
          ? 'bg-gradient-to-b from-sky-50/70 to-white border-sky-300 shadow-sm ring-1 ring-sky-200'
          : 'bg-white border-slate-200 hover:border-slate-300 shadow-xs'
      }`}
    >
      {/* Header Row: Rank badge, Source title, Link */}
      <div className="flex items-start justify-between gap-3 mb-2.5">
        <div className="flex items-center gap-2">
          <span
            className={`inline-flex items-center justify-center font-bold text-xs px-2 py-0.5 rounded-md ${
              isTopRank
                ? 'bg-sky-600 text-white shadow-xs'
                : 'bg-slate-100 text-slate-700 border border-slate-200'
            }`}
          >
            #{chunk.rank} Evidence
          </span>
          <h4 className="text-sm font-semibold text-slate-900 line-clamp-1">{chunk.source_title}</h4>
        </div>

        <a
          href={chunk.source_url}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1 text-[11px] font-medium text-sky-700 hover:text-sky-900 bg-sky-50 hover:bg-sky-100 px-2 py-0.5 rounded border border-sky-200 transition-colors flex-shrink-0"
        >
          <span>NHS Source</span>
          <ExternalLink className="w-3 h-3" />
        </a>
      </div>

      {/* Chunk ID & Scores Strip */}
      <div className="flex items-center flex-wrap gap-2 text-[11px] text-slate-500 mb-3 bg-slate-50/80 px-2.5 py-1 rounded-md border border-slate-100 font-mono">
        <span className="text-slate-600 font-medium">ID: {chunk.chunk_id}</span>
        <span className="text-slate-300">•</span>
        <span className="text-sky-700 font-semibold">Rerank: {chunk.rerank_score.toFixed(4)}</span>
        {chunk.raw_dense_score !== undefined && (
          <>
            <span className="text-slate-300">•</span>
            <span>Dense: {chunk.raw_dense_score.toFixed(4)}</span>
          </>
        )}
        {chunk.lexical_overlap !== undefined && (
          <>
            <span className="text-slate-300">•</span>
            <span>Overlap: {(chunk.lexical_overlap * 100).toFixed(0)}%</span>
          </>
        )}
      </div>

      {/* Chunk Text Body */}
      <div className="text-xs leading-relaxed text-slate-800 whitespace-pre-line bg-white/60 p-3 rounded-lg border border-slate-100 font-sans">
        {chunk.text}
      </div>

      {/* Provenance & Copyright Clause */}
      <div className="mt-2.5 pt-2 border-t border-slate-100 flex items-center justify-between text-[10px] text-slate-400">
        <div className="flex items-center gap-1">
          <CheckCircle2 className="w-3 h-3 text-emerald-600" />
          <span>OGL v3.0 Grounding Verified</span>
        </div>
        <span className="truncate max-w-[240px]">{chunk.provenance_clause}</span>
      </div>
    </div>
  );
};
