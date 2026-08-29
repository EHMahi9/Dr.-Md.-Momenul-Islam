import React, { useState } from 'react';
import {
  User,
  Activity,
  AlertCircle,
  ChevronDown,
  ChevronUp,
  Layers,
  CheckCircle,
  AlertTriangle,
  HelpCircle,
  XCircle
} from 'lucide-react';
import { Message, RetrievalOutcomeState } from '../types';
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
  const outcome = message.outcomeState || 'SUPPORTED_RETRIEVAL';
  const assessment = message.confidenceAssessment;

  const renderOutcomeBadge = (state: RetrievalOutcomeState) => {
    switch (state) {
      case 'SUPPORTED_RETRIEVAL':
        return (
          <div className="flex items-center gap-1.5 bg-emerald-50 text-emerald-800 border border-emerald-200 px-2.5 py-1 rounded-md text-xs font-semibold">
            <CheckCircle className="w-3.5 h-3.5 text-emerald-600" />
            <span>Evidence Found (High Confidence)</span>
          </div>
        );
      case 'LOW_CONFIDENCE_RETRIEVAL':
        return (
          <div className="flex items-center gap-1.5 bg-amber-50 text-amber-800 border border-amber-200 px-2.5 py-1 rounded-md text-xs font-semibold">
            <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
            <span>Evidence May Be Incomplete (Needs Caution)</span>
          </div>
        );
      case 'POSSIBLE_MISMATCH':
        return (
          <div className="flex items-center gap-1.5 bg-orange-50 text-orange-800 border border-orange-200 px-2.5 py-1 rounded-md text-xs font-semibold">
            <HelpCircle className="w-3.5 h-3.5 text-orange-600" />
            <span>Possible Topic Mismatch</span>
          </div>
        );
      case 'UNSUPPORTED_BY_ACTIVE_CORPUS':
        return (
          <div className="flex items-center gap-1.5 bg-rose-50 text-rose-800 border border-rose-200 px-2.5 py-1 rounded-md text-xs font-semibold">
            <XCircle className="w-3.5 h-3.5 text-rose-600" />
            <span>Unsupported by Current Active Knowledge Base</span>
          </div>
        );
      case 'NO_RELEVANT_EVIDENCE':
      default:
        return (
          <div className="flex items-center gap-1.5 bg-slate-100 text-slate-700 border border-slate-300 px-2.5 py-1 rounded-md text-xs font-semibold">
            <AlertCircle className="w-3.5 h-3.5 text-slate-500" />
            <span>No Supporting Evidence Found</span>
          </div>
        );
    }
  };

  return (
    <div className="flex gap-3 justify-start items-start mb-8">
      <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-sky-700 to-sky-500 text-white flex items-center justify-center flex-shrink-0 shadow-xs">
        <Activity className="w-4 h-4" />
      </div>

      <div className="flex-1 max-w-full sm:max-w-[90%] space-y-3">
        {/* Outcome & Confidence State Box */}
        <div className="bg-white border border-slate-200 rounded-2xl rounded-tl-xs p-4 shadow-xs space-y-3">
          <div className="flex items-center justify-between pb-2 border-b border-slate-100 flex-wrap gap-2">
            {renderOutcomeBadge(outcome)}
            <span className="text-[11px] text-slate-400">{message.timestamp}</span>
          </div>

          {/* Assessment Explanation Summary */}
          {assessment && (
            <p className="text-xs text-slate-700 leading-relaxed font-sans bg-slate-50 p-2.5 rounded-lg border border-slate-100">
              <strong>Assessment:</strong> {assessment.summary_reason}
            </p>
          )}

          {/* Generation Disabled Static Banner */}
          <div className="bg-amber-50/70 border border-amber-200 rounded-lg p-3 text-xs text-amber-900 leading-relaxed">
            <div className="flex items-center gap-1.5 font-bold mb-1 text-[11px] text-amber-800">
              <AlertCircle className="w-3.5 h-3.5" />
              <span>Research Mode Notice (LLM Generation Disabled)</span>
            </div>
            <p className="text-[11px] text-amber-900/90 font-mono">
              {message.text}
            </p>
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
                Strategy: Dual-Anchor Reranker (Frozen Strategy 5)
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
