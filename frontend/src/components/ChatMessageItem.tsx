import React, { useState } from 'react';
import { User, Activity, AlertCircle, ChevronDown, ChevronUp, Layers } from 'lucide-react';
import { Message } from '../types';
import { EvidenceCard } from './EvidenceCard';

interface ChatMessageItemProps {
  message: Message;
}

export const ChatMessageItem: React.FC<ChatMessageItemProps> = ({ message }) => {
  const isUser = message.sender === 'user';
  const [showEvidence, setShowEvidence] = useState(true);

  if (isUser) {
    return (
      <div className="flex gap-3 justify-end items-start mb-6">
        <div className="bg-sky-600 text-white rounded-2xl rounded-tr-xs px-4 py-3 max-w-[85%] sm:max-w-[70%] shadow-sm">
          <p className="text-sm leading-relaxed whitespace-pre-wrap">{message.text}</p>
          <div className="text-[10px] text-sky-200 mt-1 text-right">{message.timestamp}</div>
        </div>
        <div className="w-8 h-8 rounded-full bg-slate-200 text-slate-600 flex items-center justify-center flex-shrink-0 text-xs font-bold">
          <User className="w-4 h-4" />
        </div>
      </div>
    );
  }

  const evidence = message.evidence || [];

  return (
    <div className="flex gap-3 justify-start items-start mb-8">
      <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-sky-700 to-sky-500 text-white flex items-center justify-center flex-shrink-0 shadow-xs">
        <Activity className="w-4 h-4" />
      </div>

      <div className="flex-1 max-w-full sm:max-w-[90%] space-y-3">
        {/* Research Mode Synthetic Answer Notice Box */}
        <div className="bg-white border border-slate-200 rounded-2xl rounded-tl-xs p-4 shadow-xs">
          <div className="flex items-center justify-between pb-2 mb-2 border-b border-slate-100">
            <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-800">
              <span className="inline-block w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
              <span>Retrieved Clinical Evidence Context</span>
            </div>
            <span className="text-[11px] text-slate-400">{message.timestamp}</span>
          </div>

          <div className="bg-slate-50 border border-slate-200 rounded-lg p-3 text-xs text-slate-700 leading-relaxed font-mono">
            <div className="flex items-center gap-1.5 text-amber-800 font-semibold mb-1 text-[11px]">
              <AlertCircle className="w-3.5 h-3.5" />
              <span>Generation Layer Notice (Phase 6A)</span>
            </div>
            {message.text}
          </div>
        </div>

        {/* Evidence Breakdown Section */}
        {evidence.length > 0 && (
          <div className="space-y-2">
            <div className="flex items-center justify-between px-1">
              <button
                type="button"
                onClick={() => setShowEvidence(!showEvidence)}
                className="flex items-center gap-2 text-xs font-bold text-slate-700 hover:text-sky-700 transition-colors cursor-pointer"
              >
                <Layers className="w-4 h-4 text-sky-600" />
                <span>Top-{evidence.length} Grounding Evidence Passages</span>
                {showEvidence ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
              </button>

              <span className="text-[11px] text-slate-400 font-medium">
                Strategy: Dual-Anchor Reranking
              </span>
            </div>

            {showEvidence && (
              <div className="grid grid-cols-1 gap-3 pt-1">
                {evidence.map((chunk, idx) => (
                  <EvidenceCard key={chunk.chunk_id || idx} chunk={chunk} isTopRank={idx === 0} />
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
