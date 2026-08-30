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
  XCircle,
  ShieldAlert,
  Sparkles,
  BookOpen
} from 'lucide-react';
import { Message, RetrievalOutcomeState } from '../types';
import { EvidenceCard } from './EvidenceCard';
import { CitationLink } from './CitationLink';

interface ChatMessageItemProps {
  message: Message;
  onSelectOption?: (text: string) => void;
}

export const ChatMessageItem: React.FC<ChatMessageItemProps> = ({ message, onSelectOption }) => {
  const isUser = message.sender === 'user';
  const policy = message.evidencePresentationPolicy || 'SHOW_GROUNDING_CARDS';
  const isAbstention = policy === 'SUPPRESS_UNRELATED_CARDS_SHOW_ABSTENTION' || 
    message.outcomeState === 'NO_RELEVANT_EVIDENCE' || 
    message.outcomeState === 'UNSUPPORTED_BY_ACTIVE_CORPUS';
  
  // Default show evidence only when supported; collapse for abstention/unsupported queries
  const [showEvidence, setShowEvidence] = useState(!isAbstention);

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
  const genResult = message.generationResult;
  const genStatus = genResult?.generation_status || (message.generationEnabled ? 'COMPLETED' : 'DISABLED');
  const qu = message.queryUnderstanding;

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

  const renderActionBadge = () => {
    const act = message.nextAction || 'ANSWER';
    const turn = message.contextState?.clarification_turn_count || 0;
    const maxTurns = message.contextState?.max_clarification_turns || 3;

    switch (act) {
      case 'CLARIFY':
        return (
          <span className="bg-sky-100 text-sky-800 border border-sky-300 text-[10px] font-bold px-2 py-0.5 rounded-full uppercase tracking-wider">
            Clarification (Turn {turn}/{maxTurns})
          </span>
        );
      case 'EMERGENCY':
        return (
          <span className="bg-rose-100 text-rose-800 border border-rose-300 text-[10px] font-bold px-2 py-0.5 rounded-full uppercase tracking-wider">
            Emergency Override
          </span>
        );
      case 'ABSTAIN':
        return (
          <span className="bg-slate-100 text-slate-700 border border-slate-300 text-[10px] font-bold px-2 py-0.5 rounded-full uppercase tracking-wider">
            Abstention
          </span>
        );
      case 'ANSWER':
      default:
        return (
          <span className="bg-emerald-100 text-emerald-800 border border-emerald-300 text-[10px] font-bold px-2 py-0.5 rounded-full uppercase tracking-wider">
            Grounded Answer
          </span>
        );
    }
  };

  const renderGenerationContent = () => {
    switch (genStatus) {
      case 'COMPLETED':
        return (
          <div className="bg-slate-50 border border-slate-200 rounded-lg p-3.5 text-xs text-slate-800 leading-relaxed space-y-2">
            <div className="flex items-center gap-1.5 font-bold text-[11px] text-sky-800">
              <Sparkles className="w-3.5 h-3.5 text-sky-600" />
              <span>Grounded Evidence Summary</span>
            </div>
            <p className="text-xs leading-relaxed text-slate-800 font-sans whitespace-pre-wrap">
              {genResult?.answer || message.text}
            </p>
            {genResult?.citations && genResult.citations.length > 0 && (
              <div className="pt-2 border-t border-slate-200/60 flex items-center gap-1.5 flex-wrap">
                <span className="text-[10px] text-slate-500 font-medium">Citations:</span>
                {genResult.citations.map((c) => (
                  <CitationLink key={c.citation_index} citation={c} />
                ))}
              </div>
            )}
            <p className="text-[10px] text-slate-400 italic pt-1">
              {genResult?.disclaimer || "Research Prototype — Not for Medical Decision-Making."}
            </p>
          </div>
        );

      case 'REFUSED_SAFETY':
        return (
          <div className="bg-rose-50 border border-rose-200 rounded-lg p-3 text-xs text-rose-900 leading-relaxed space-y-1">
            <div className="flex items-center gap-1.5 font-bold text-[11px] text-rose-800">
              <ShieldAlert className="w-3.5 h-3.5 text-rose-600" />
              <span>Safety Guardrail Triggered</span>
            </div>
            <p className="text-[11px] text-rose-800 leading-relaxed">
              {genResult?.refusal_reason || "Direct synthesis refused for potential emergency or high-risk inquiry."}
            </p>
          </div>
        );

      case 'REFUSED_INSUFFICIENT_EVIDENCE':
        return (
          <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 text-xs text-amber-900 leading-relaxed space-y-1">
            <div className="flex items-center gap-1.5 font-bold text-[11px] text-amber-800">
              <BookOpen className="w-3.5 h-3.5 text-amber-600" />
              <span>Insufficient Evidence for Grounded Answer</span>
            </div>
            <p className="text-[11px] text-amber-800 leading-relaxed">
              {genResult?.refusal_reason || "The retrieved NHS evidence does not contain sufficient details to synthesize an answer."}
            </p>
          </div>
        );

      case 'FAILED':
        return (
          <div className="bg-rose-50 border border-rose-200 rounded-lg p-3 text-xs text-rose-900 leading-relaxed">
            <div className="flex items-center gap-1.5 font-bold mb-1 text-[11px] text-rose-800">
              <AlertCircle className="w-3.5 h-3.5 text-rose-600" />
              <span>Generation Error</span>
            </div>
            <p className="text-[11px] text-rose-800">
              {genResult?.refusal_reason || "Synthesis failed post-generation validation checks."}
            </p>
          </div>
        );

      case 'DISABLED':
      default:
        return (
          <div className="bg-amber-50/70 border border-amber-200 rounded-lg p-3 text-xs text-amber-900 leading-relaxed">
            <div className="flex items-center gap-1.5 font-bold mb-1 text-[11px] text-amber-800">
              <AlertCircle className="w-3.5 h-3.5 text-amber-600" />
              <span>Research Mode Notice (LLM Generation Disabled)</span>
            </div>
            <p className="text-[11px] text-amber-900/90 font-mono">
              {message.text}
            </p>
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
        {/* Track B: Red-Flag Emergency Override Banner */}
        {qu?.is_emergency && qu.emergency_advice && (
          <div className="bg-red-600 text-white p-4 rounded-2xl shadow-md space-y-2 border-2 border-red-700 animate-pulse">
            <div className="flex items-center gap-2 font-bold text-sm">
              <ShieldAlert className="w-5 h-5 text-white" />
              <span>{qu.emergency_advice.alert_title_bn} / {qu.emergency_advice.alert_title_en}</span>
            </div>
            <p className="text-xs leading-relaxed text-red-50">
              {qu.emergency_advice.action_advice_bn}
            </p>
            <p className="text-[11px] leading-relaxed text-red-100 italic">
              {qu.emergency_advice.action_advice_en}
            </p>
            <div className="pt-2 border-t border-red-500/60 flex items-center justify-between text-xs font-bold">
              <span>Emergency Services: {qu.emergency_advice.emergency_contact}</span>
            </div>
          </div>
        )}

        {/* Outcome & Confidence State Box */}
        <div className="bg-white border border-slate-200 rounded-2xl rounded-tl-xs p-4 shadow-xs space-y-3">
          <div className="flex items-center justify-between pb-2 border-b border-slate-100 flex-wrap gap-2">
            <div className="flex items-center gap-2 flex-wrap">
              {renderOutcomeBadge(outcome)}
              {renderActionBadge()}
            </div>
            <span className="text-[11px] text-slate-400">{message.timestamp}</span>
          </div>

          {/* Context State Summary Chips */}
          {message.contextState && (message.contextState.specific_location || message.contextState.precipitating_event || message.contextState.duration) && (
            <div className="flex items-center gap-1.5 flex-wrap text-[11px] text-slate-600 bg-slate-50 p-2 rounded-lg border border-slate-100">
              <span className="font-semibold text-slate-500 text-[10px] uppercase">Stated Context:</span>
              {message.contextState.body_location && message.contextState.body_location !== 'body' && (
                <span className="bg-white border border-slate-200 px-2 py-0.5 rounded text-slate-700 font-medium">
                  Site: {message.contextState.body_location}
                </span>
              )}
              {message.contextState.specific_location && (
                <span className="bg-white border border-slate-200 px-2 py-0.5 rounded text-slate-700 font-medium">
                  Location: {message.contextState.specific_location}
                </span>
              )}
              {message.contextState.precipitating_event && (
                <span className="bg-white border border-slate-200 px-2 py-0.5 rounded text-slate-700 font-medium">
                  Event: {message.contextState.precipitating_event}
                </span>
              )}
              {message.contextState.duration && (
                <span className="bg-white border border-slate-200 px-2 py-0.5 rounded text-slate-700 font-medium">
                  Duration: {message.contextState.duration}
                </span>
              )}
            </div>
          )}

          {/* Assessment Explanation Summary */}
          {assessment && (
            <p className="text-xs text-slate-700 leading-relaxed font-sans bg-slate-50 p-2.5 rounded-lg border border-slate-100">
              <strong>Assessment:</strong> {assessment.summary_reason}
            </p>
          )}

          {/* Track B: Conversational Clarification Box for Underspecified / Ambiguous Queries */}
          {qu?.clarification_question && (
            <div className="bg-sky-50 border border-sky-200 rounded-xl p-3.5 text-xs text-sky-900 space-y-2.5">
              <div className="flex items-center gap-1.5 font-bold text-[12px] text-sky-800">
                <HelpCircle className="w-4 h-4 text-sky-600" />
                <span>লক্ষণ স্পষ্টীকরণ (Symptom Clarification)</span>
              </div>
              <p className="text-xs leading-relaxed text-sky-950 font-medium">
                {qu.clarification_question.question_text_bn}
              </p>
              <p className="text-[11px] text-sky-800/80 italic">
                {qu.clarification_question.question_text_en}
              </p>

              {qu.clarification_question.options.length > 0 && (
                <div className="pt-2 flex items-center gap-2 flex-wrap">
                  <span className="text-[10px] text-sky-700 font-bold uppercase tracking-wider">Quick Select:</span>
                  {qu.clarification_question.options.map((opt, idx) => (
                    <button
                      key={idx}
                      type="button"
                      onClick={() => onSelectOption && onSelectOption(opt)}
                      className="bg-white hover:bg-sky-100 text-sky-800 border border-sky-300 px-2.5 py-1 rounded-full text-xs font-semibold shadow-2xs transition-colors cursor-pointer"
                    >
                      {opt}
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Generation Content (State-Aware) */}
          {renderGenerationContent()}
        </div>

        {/* Track B: Deterministic Evidence Presentation Policy */}
        {evidence.length > 0 && (
          <div className="space-y-2">
            <div className="flex items-center justify-between px-1">
              <button
                type="button"
                onClick={() => setShowEvidence(!showEvidence)}
                className={`flex items-center gap-2 text-xs font-bold transition-colors cursor-pointer ${
                  isAbstention ? 'text-slate-500 hover:text-slate-800' : 'text-slate-700 hover:text-sky-700'
                }`}
              >
                <Layers className={`w-4 h-4 ${isAbstention ? 'text-slate-400' : 'text-sky-600'}`} />
                <span>
                  {isAbstention
                    ? `Technical / Diagnostic Details (${evidence.length} Unrelated Raw Candidates)`
                    : `Top-${evidence.length} Grounding Evidence Passages`}
                </span>
                {showEvidence ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
              </button>

              <span className="text-[11px] text-slate-400 font-medium">
                Candidate B (Promoted Dual-Anchor Reranker)
              </span>
            </div>

            {/* If abstention and evidence collapsed, show concise reassuring note */}
            {isAbstention && !showEvidence && (
              <div className="text-[11px] text-slate-500 italic px-1">
                Note: Unrelated candidate passages are hidden by default to prevent misleading evidence presentation. Expand above for technical inspection.
              </div>
            )}

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
