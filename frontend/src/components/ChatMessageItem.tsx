import React, { useState } from 'react';
import {
  User,
  Activity,
  AlertCircle,
  ChevronDown,
  ChevronUp,
  Layers,
  CheckCircle2,
  AlertTriangle,
  HelpCircle,
  XCircle,
  ShieldAlert,
  Sparkles,
  BookOpen,
  Info
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
  const isAbstention =
    policy === 'SUPPRESS_UNRELATED_CARDS_SHOW_ABSTENTION' ||
    message.outcomeState === 'NO_RELEVANT_EVIDENCE' ||
    message.outcomeState === 'UNSUPPORTED_BY_ACTIVE_CORPUS';

  // Default show evidence only when supported; collapse for abstention/unsupported queries
  const [showEvidence, setShowEvidence] = useState(!isAbstention);
  const [showDiagnostics, setShowDiagnostics] = useState(false);

  if (isUser) {
    return (
      <div className="flex gap-3 justify-end items-start mb-6">
        <div className="bg-teal-700 text-white rounded-2xl rounded-tr-xs px-4 py-3 max-w-[85%] sm:max-w-[70%] shadow-xs">
          <p className="text-sm leading-relaxed whitespace-pre-wrap">{message.text}</p>
          <div className="text-[10px] text-teal-200 mt-1 text-right">{message.timestamp}</div>
        </div>
        <div className="w-8 h-8 rounded-full bg-stone-200 text-stone-600 flex items-center justify-center flex-shrink-0 text-xs font-semibold">
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
          <div className="flex items-center gap-1.5 bg-emerald-50 text-emerald-800 border border-emerald-200 px-2.5 py-1 rounded-full text-xs font-medium">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
            <span>Strong Clinical Evidence Found</span>
          </div>
        );
      case 'LOW_CONFIDENCE_RETRIEVAL':
        return (
          <div className="flex items-center gap-1.5 bg-amber-50 text-amber-800 border border-amber-200 px-2.5 py-1 rounded-full text-xs font-medium">
            <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
            <span>Limited Evidence Coverage</span>
          </div>
        );
      case 'POSSIBLE_MISMATCH':
        return (
          <div className="flex items-center gap-1.5 bg-stone-100 text-stone-700 border border-stone-200 px-2.5 py-1 rounded-full text-xs font-medium">
            <HelpCircle className="w-3.5 h-3.5 text-stone-500" />
            <span>Possible Topic Mismatch</span>
          </div>
        );
      case 'UNSUPPORTED_BY_ACTIVE_CORPUS':
        return (
          <div className="flex items-center gap-1.5 bg-rose-50 text-rose-800 border border-rose-200 px-2.5 py-1 rounded-full text-xs font-medium">
            <XCircle className="w-3.5 h-3.5 text-rose-600" />
            <span>Topic Not in Active Knowledge Base</span>
          </div>
        );
      case 'NO_RELEVANT_EVIDENCE':
      default:
        return (
          <div className="flex items-center gap-1.5 bg-stone-100 text-stone-700 border border-stone-200 px-2.5 py-1 rounded-full text-xs font-medium">
            <AlertCircle className="w-3.5 h-3.5 text-stone-500" />
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
          <span className="bg-teal-50 text-teal-800 border border-teal-200 text-[11px] font-medium px-2.5 py-0.5 rounded-full">
            Clarification Needed ({turn}/{maxTurns})
          </span>
        );
      case 'EMERGENCY':
        return (
          <span className="bg-rose-100 text-rose-800 border border-rose-200 text-[11px] font-semibold px-2.5 py-0.5 rounded-full">
            Emergency Protocol
          </span>
        );
      case 'ABSTAIN':
        return (
          <span className="bg-stone-100 text-stone-700 border border-stone-200 text-[11px] font-medium px-2.5 py-0.5 rounded-full">
            Cautious Abstention
          </span>
        );
      case 'ANSWER':
      default:
        return null;
    }
  };

  const renderGenerationContent = () => {
    switch (genStatus) {
      case 'COMPLETED':
        return (
          <div className="bg-white border border-stone-200 rounded-xl p-4 text-sm text-stone-800 leading-relaxed space-y-2.5 shadow-2xs">
            <div className="flex items-center gap-1.5 font-semibold text-xs text-teal-800">
              <Sparkles className="w-4 h-4 text-teal-600" />
              <span>Grounded Evidence Summary</span>
            </div>
            <p className="text-sm leading-relaxed text-stone-800 whitespace-pre-wrap">
              {genResult?.answer || message.text}
            </p>
            {genResult?.citations && genResult.citations.length > 0 && (
              <div className="pt-2 border-t border-stone-100 flex items-center gap-1.5 flex-wrap">
                <span className="text-xs text-stone-500 font-medium">Citations:</span>
                {genResult.citations.map((c) => (
                  <CitationLink key={c.citation_index} citation={c} />
                ))}
              </div>
            )}
            <p className="text-xs text-stone-400 italic pt-1">
              {genResult?.disclaimer || 'Clinical Information Prototype — For evidence consultation only.'}
            </p>
          </div>
        );

      case 'REFUSED_SAFETY':
        return (
          <div className="bg-rose-50/80 border border-rose-200 rounded-xl p-4 text-xs text-rose-900 leading-relaxed space-y-1.5">
            <div className="flex items-center gap-1.5 font-semibold text-xs text-rose-800">
              <ShieldAlert className="w-4 h-4 text-rose-600" />
              <span>Safety Guardrail Triggered</span>
            </div>
            <p className="text-xs text-rose-800 leading-relaxed">
              {genResult?.refusal_reason || 'Direct synthesis refused for potential emergency or high-risk inquiry.'}
            </p>
          </div>
        );

      case 'REFUSED_INSUFFICIENT_EVIDENCE':
        return (
          <div className="bg-amber-50/80 border border-amber-200 rounded-xl p-4 text-xs text-amber-900 leading-relaxed space-y-1.5">
            <div className="flex items-center gap-1.5 font-semibold text-xs text-amber-800">
              <BookOpen className="w-4 h-4 text-amber-600" />
              <span>Insufficient Evidence for Grounded Answer</span>
            </div>
            <p className="text-xs text-amber-800 leading-relaxed">
              {genResult?.refusal_reason || 'The retrieved NHS evidence does not contain sufficient clinical detail for this query.'}
            </p>
          </div>
        );

      case 'FAILED':
        return (
          <div className="bg-rose-50/80 border border-rose-200 rounded-xl p-4 text-xs text-rose-900 leading-relaxed">
            <div className="flex items-center gap-1.5 font-semibold mb-1 text-xs text-rose-800">
              <AlertCircle className="w-4 h-4 text-rose-600" />
              <span>Generation Error</span>
            </div>
            <p className="text-xs text-rose-800">
              {genResult?.refusal_reason || 'Synthesis failed post-generation validation checks.'}
            </p>
          </div>
        );

      case 'DISABLED':
      default:
        return (
          <div className="bg-stone-50 border border-stone-200/80 rounded-xl p-3.5 text-xs text-stone-600 leading-relaxed">
            <div className="flex items-center gap-1.5 font-medium text-stone-700 mb-1">
              <ShieldAlert className="w-3.5 h-3.5 text-teal-700" />
              <span>Direct Evidence Grounding (Synthetic LLM Generation Disabled)</span>
            </div>
            <p className="text-[11px] text-stone-500 leading-normal">
              To eliminate AI hallucinations, answers are presented as verified NHS passages retrieved directly by dual-anchor semantic ranking.
            </p>
          </div>
        );
    }
  };

  return (
    <div className="flex gap-3 justify-start items-start mb-8">
      <div className="w-8 h-8 rounded-full bg-teal-700 text-white flex items-center justify-center flex-shrink-0 shadow-2xs">
        <Activity className="w-4 h-4" />
      </div>

      <div className="flex-1 max-w-full sm:max-w-[90%] space-y-3.5">
        {/* Urgent Emergency Alert Banner */}
        {qu?.is_emergency && qu.emergency_advice && (
          <div className="bg-red-600 text-white p-4 sm:p-5 rounded-2xl shadow-md space-y-2 border border-red-700 animate-pulse">
            <div className="flex items-center gap-2 font-bold text-sm sm:text-base">
              <ShieldAlert className="w-5 h-5 text-white flex-shrink-0" />
              <span>{qu.emergency_advice.alert_title_bn} / {qu.emergency_advice.alert_title_en}</span>
            </div>
            <p className="text-xs sm:text-sm leading-relaxed text-red-50">
              {qu.emergency_advice.action_advice_bn}
            </p>
            <p className="text-xs leading-relaxed text-red-100 italic">
              {qu.emergency_advice.action_advice_en}
            </p>
            <div className="pt-2 border-t border-red-500/60 flex items-center justify-between text-xs font-semibold">
              <span>জরুরি সেবা / Emergency Helpline:</span>
              <span className="bg-white text-red-700 px-2 py-0.5 rounded font-mono font-bold">
                {qu.emergency_advice.emergency_contact}
              </span>
            </div>
          </div>
        )}

        {/* Primary Response Container */}
        <div className="bg-white border border-stone-200 rounded-2xl rounded-tl-xs p-4 sm:p-5 shadow-xs space-y-3.5">
          {/* Header row: Status badges & timestamp */}
          <div className="flex items-center justify-between pb-3 border-b border-stone-100 flex-wrap gap-2">
            <div className="flex items-center gap-2 flex-wrap">
              {renderOutcomeBadge(outcome)}
              {renderActionBadge()}
            </div>
            <span className="text-xs text-stone-400">{message.timestamp}</span>
          </div>

          {/* Stated Context Summary */}
          {message.contextState &&
            (message.contextState.specific_location ||
              message.contextState.precipitating_event ||
              message.contextState.duration) && (
              <div className="flex items-center gap-1.5 flex-wrap text-xs text-stone-600 bg-stone-50 p-2.5 rounded-xl border border-stone-100">
                <span className="font-semibold text-stone-500 text-[11px] uppercase tracking-wider">Context:</span>
                {message.contextState.body_location && message.contextState.body_location !== 'body' && (
                  <span className="bg-white border border-stone-200 px-2 py-0.5 rounded-md text-stone-700 font-medium">
                    {message.contextState.body_location}
                  </span>
                )}
                {message.contextState.specific_location && (
                  <span className="bg-white border border-stone-200 px-2 py-0.5 rounded-md text-stone-700 font-medium">
                    {message.contextState.specific_location}
                  </span>
                )}
                {message.contextState.precipitating_event && (
                  <span className="bg-white border border-stone-200 px-2 py-0.5 rounded-md text-stone-700 font-medium">
                    {message.contextState.precipitating_event}
                  </span>
                )}
                {message.contextState.duration && (
                  <span className="bg-white border border-stone-200 px-2 py-0.5 rounded-md text-stone-700 font-medium">
                    {message.contextState.duration}
                  </span>
                )}
              </div>
            )}

          {/* Clinical Assessment Explanation */}
          {assessment && (
            <p className="text-xs sm:text-sm text-stone-700 leading-relaxed font-sans bg-stone-50/70 p-3 rounded-xl border border-stone-100">
              <strong className="text-stone-900 font-semibold">Clinical Assessment:</strong> {assessment.summary_reason}
            </p>
          )}

          {/* Symptom Clarification Card for Underspecified Queries */}
          {qu?.clarification_question && (
            <div className="bg-teal-50/70 border border-teal-200 rounded-xl p-4 text-xs text-teal-950 space-y-2.5">
              <div className="flex items-center gap-1.5 font-semibold text-xs text-teal-900">
                <HelpCircle className="w-4 h-4 text-teal-700" />
                <span>লক্ষণ স্পষ্টীকরণ &bull; Symptom Clarification</span>
              </div>
              <p className="text-xs sm:text-sm leading-relaxed text-teal-950 font-medium">
                {qu.clarification_question.question_text_bn}
              </p>
              <p className="text-xs text-teal-800/80 italic">
                {qu.clarification_question.question_text_en}
              </p>

              {qu.clarification_question.options.length > 0 && (
                <div className="pt-2 flex items-center gap-2 flex-wrap">
                  <span className="text-[11px] text-teal-800 font-medium">Select an option:</span>
                  {qu.clarification_question.options.map((opt, idx) => (
                    <button
                      key={idx}
                      type="button"
                      onClick={() => onSelectOption && onSelectOption(opt)}
                      className="bg-white hover:bg-teal-100 text-teal-900 border border-teal-300 px-3 py-1 rounded-full text-xs font-medium shadow-2xs transition-colors cursor-pointer"
                    >
                      {opt}
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Grounded Generation Content */}
          {renderGenerationContent()}
        </div>

        {/* Evidence Section */}
        {evidence.length > 0 && (
          <div className="space-y-2.5 pt-1">
            <div className="flex items-center justify-between px-1">
              <button
                type="button"
                onClick={() => setShowEvidence(!showEvidence)}
                className="flex items-center gap-2 text-xs sm:text-sm font-semibold text-stone-800 hover:text-teal-800 transition-colors cursor-pointer"
              >
                <Layers className="w-4 h-4 text-teal-700" />
                <span>
                  {isAbstention
                    ? `Retrieved Candidates (${evidence.length} Unrelated Passages)`
                    : `Grounded Clinical Evidence (${evidence.length} NHS Passages)`}
                </span>
                {showEvidence ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
              </button>

              <button
                type="button"
                onClick={() => setShowDiagnostics(!showDiagnostics)}
                className="text-[11px] text-stone-400 hover:text-teal-700 flex items-center gap-1 transition-colors cursor-pointer"
              >
                <Info className="w-3 h-3" />
                <span>Diagnostics</span>
              </button>
            </div>

            {/* Diagnostics details row */}
            {showDiagnostics && message.retrievalMetadata && (
              <div className="p-3 bg-stone-100 rounded-xl text-xs font-mono text-stone-600 border border-stone-200 space-y-1">
                <div className="flex justify-between">
                  <span>Strategy:</span>
                  <span>{message.retrievalMetadata.strategy_name}</span>
                </div>
                <div className="flex justify-between">
                  <span>Candidate:</span>
                  <span>{message.retrievalMetadata.active_candidate}</span>
                </div>
                <div className="flex justify-between">
                  <span>Corpus Chunks:</span>
                  <span>{message.retrievalMetadata.active_chunks_count}</span>
                </div>
              </div>
            )}

            {/* Abstention reminder */}
            {isAbstention && !showEvidence && (
              <div className="text-xs text-stone-500 italic px-1">
                Candidate passages collapsed by default to prevent misleading clinical guidance. Expand above to inspect raw retrieval candidates.
              </div>
            )}

            {/* Evidence Cards */}
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
export default ChatMessageItem;
