import React, { useState, useEffect, useRef } from 'react';
import { Header } from './components/Header';
import { ChatInput } from './components/ChatInput';
import { ChatMessageItem } from './components/ChatMessageItem';
import { Message, HealthResponse, ConversationContextState } from './types';
import { fetchHealth, sendChatMessage } from './services/api';
import { ShieldCheck, Info, MessageSquare, Database, AlertTriangle, RefreshCw, Loader2, RotateCcw } from 'lucide-react';

export const App: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [currentContextState, setCurrentContextState] = useState<ConversationContextState | null>(null);
  const [error, setError] = useState<{ title: string; detail: string } | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const checkHealth = () => {
    fetchHealth()
      .then((data) => {
        setHealth(data);
        setError(null);
      })
      .catch((err) => {
        console.warn('Backend health check failed:', err);
        setError({
          title: 'Backend Offline or Unreachable',
          detail: 'The FastAPI backend is currently unavailable at port 8000. Please ensure the server process is active.',
        });
      });
  };

  useEffect(() => {
    checkHealth();
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const handleResetConversation = () => {
    setMessages([]);
    setCurrentContextState(null);
    setError(null);
  };

  const handleSendMessage = async (text: string, preferredLang: string = 'auto') => {
    setError(null);
    const now = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    const userMsg: Message = {
      id: `user-${Date.now()}`,
      sender: 'user',
      text,
      timestamp: now,
    };

    setMessages((prev) => [...prev, userMsg]);
    setIsLoading(true);

    try {
      const response = await sendChatMessage(
        text,
        preferredLang,
        currentContextState,
        currentContextState?.session_id
      );

      setCurrentContextState(response.context_state || null);

      const assistantMsg: Message = {
        id: `assistant-${Date.now()}`,
        sender: 'assistant',
        text: response.synthetic_answer,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        outcomeState: response.outcome_state,
        confidenceAssessment: response.confidence_assessment,
        nextAction: response.next_action,
        clarificationState: response.clarification_state,
        contextState: response.context_state,
        evidence: response.evidence,
        generationEnabled: response.generation_enabled,
        retrievalMetadata: response.retrieval_metadata,
        generationResult: response.generation_result,
        queryUnderstanding: response.query_understanding,
        evidencePresentationPolicy: response.evidence_presentation_policy,
      };

      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err: any) {
      setError({
        title: 'Evidence Retrieval Error',
        detail: err.message || 'The retrieval service was unable to complete your query. Please try again.',
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col min-h-screen bg-slate-50">
      <Header health={health} />

      {/* Main Content Area */}
      <main className="flex-1 max-w-5xl w-full mx-auto p-4 sm:p-6 flex flex-col justify-between">
        {error && (
          <div className="mb-4 bg-rose-50 border border-rose-200 text-rose-800 p-4 rounded-xl flex items-start justify-between gap-3 text-xs shadow-xs">
            <div className="flex items-start gap-2.5">
              <AlertTriangle className="w-4 h-4 text-rose-600 flex-shrink-0 mt-0.5" />
              <div>
                <p className="font-bold text-rose-900">{error.title}</p>
                <p className="mt-0.5 text-rose-700 leading-relaxed">{error.detail}</p>
              </div>
            </div>
            <button
              type="button"
              onClick={checkHealth}
              className="inline-flex items-center gap-1 bg-rose-100 hover:bg-rose-200 text-rose-800 px-2.5 py-1 rounded-md text-[11px] font-semibold transition-colors flex-shrink-0 cursor-pointer"
            >
              <RefreshCw className="w-3 h-3" />
              <span>Retry</span>
            </button>
          </div>
        )}

        {messages.length === 0 ? (
          <div className="my-auto py-8 px-4 text-center space-y-6">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-sky-100 text-sky-700 shadow-inner">
              <MessageSquare className="w-8 h-8" />
            </div>

            <div className="max-w-xl mx-auto space-y-2">
              <h2 className="text-xl font-bold text-slate-900">
                Dr. Md. Momenul Islam Health Intelligence
              </h2>
              <p className="text-xs text-slate-600 leading-relaxed">
                Bangladesh-focused clinical evidence retrieval prototype. Retrieves authoritative NHS
                evidence passages across English, Native Bangla (বাংলা), and Banglish queries using the
                frozen <strong>Dual-Anchor Fusion Reranker</strong>.
              </p>
            </div>

            {/* Architecture Explainer Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 max-w-3xl mx-auto text-left pt-2">
              <div className="bg-white p-3.5 rounded-xl border border-slate-200 shadow-xs space-y-1">
                <div className="flex items-center gap-1.5 text-xs font-bold text-slate-800">
                  <Database className="w-3.5 h-3.5 text-sky-600" />
                  <span>Authoritative NHS Grounding</span>
                </div>
                <p className="text-[11px] text-slate-500 leading-normal">
                  Grounds strictly against 119 indexed NHS clinical passages across 14 conditions under OGL v3.0 licensing.
                </p>
              </div>

              <div className="bg-white p-3.5 rounded-xl border border-slate-200 shadow-xs space-y-1">
                <div className="flex items-center gap-1.5 text-xs font-bold text-slate-800">
                  <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
                  <span>Multilingual Normalization</span>
                </div>
                <p className="text-[11px] text-slate-500 leading-normal">
                  Deterministic Unicode-safe procedural expansion for colloquial Bangla and Banglish symptoms.
                </p>
              </div>

              <div className="bg-white p-3.5 rounded-xl border border-slate-200 shadow-xs space-y-1">
                <div className="flex items-center gap-1.5 text-xs font-bold text-slate-800">
                  <Info className="w-3.5 h-3.5 text-amber-600" />
                  <span>Generation Disabled</span>
                </div>
                <p className="text-[11px] text-slate-500 leading-normal">
                  LLM generation is locked off by protocol to inspect raw retrieved passages safely with zero hallucination.
                </p>
              </div>
            </div>
          </div>
        ) : (
          <div className="flex-1 overflow-y-auto pb-4">
            <div className="flex items-center justify-between pb-3 mb-3 border-b border-slate-200">
              <div className="flex items-center gap-2 text-xs text-slate-500 font-medium">
                <span>Multi-Turn Consultation Session</span>
                {currentContextState && currentContextState.clarification_turn_count > 0 && (
                  <span className="bg-sky-100 text-sky-800 text-[10px] font-bold px-2 py-0.5 rounded-full">
                    Turn {currentContextState.clarification_turn_count}/{currentContextState.max_clarification_turns}
                  </span>
                )}
              </div>
              <button
                type="button"
                onClick={handleResetConversation}
                className="inline-flex items-center gap-1.5 text-xs text-slate-600 hover:text-rose-700 bg-slate-100 hover:bg-rose-50 px-2.5 py-1 rounded-lg border border-slate-200 transition-colors cursor-pointer"
              >
                <RotateCcw className="w-3.5 h-3.5" />
                <span>New Query / Reset</span>
              </button>
            </div>

            {messages.map((msg) => (
              <ChatMessageItem
                key={msg.id}
                message={msg}
                onSelectOption={(opt) => handleSendMessage(opt)}
              />
            ))}

            {/* In-flight Loading Indicator */}
            {isLoading && (
              <div className="flex items-center gap-3 p-4 bg-white border border-slate-200 rounded-2xl max-w-sm mb-6 shadow-xs animate-pulse">
                <Loader2 className="w-5 h-5 text-sky-600 animate-spin" />
                <div>
                  <p className="text-xs font-semibold text-slate-800">Evaluating clinical knowledge base...</p>
                  <p className="text-[11px] text-slate-500">Bi-encoder search & Cross-encoder reranking</p>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        )}
      </main>

      <ChatInput onSendMessage={handleSendMessage} isLoading={isLoading} />
    </div>
  );
};
export default App;
