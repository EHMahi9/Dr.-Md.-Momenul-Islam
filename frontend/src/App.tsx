import React, { useState, useEffect, useRef } from 'react';
import { Header } from './components/Header';
import { ChatInput } from './components/ChatInput';
import { ChatMessageItem } from './components/ChatMessageItem';
import { Message, HealthResponse, ConversationContextState } from './types';
import { fetchHealth, sendChatMessage } from './services/api';
import { ShieldCheck, MessageSquare, AlertTriangle, RefreshCw, Loader2, RotateCcw, Globe, BookOpen } from 'lucide-react';

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
          title: 'Retrieval Service Connecting',
          detail: 'The clinical knowledge base service is initializing. If this persists, please ensure the backend is active.',
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
        title: 'Evidence Retrieval Notice',
        detail: err.message || 'Unable to retrieve evidence for this query. Please verify your connection or try again.',
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col min-h-screen bg-stone-50 text-stone-900 font-sans">
      <Header health={health} />

      {/* Main Content Area */}
      <main className="flex-1 max-w-4xl w-full mx-auto p-4 sm:p-6 flex flex-col justify-between">
        {error && (
          <div className="mb-4 bg-amber-50 border border-amber-200 text-amber-900 p-4 rounded-2xl flex items-start justify-between gap-3 text-xs shadow-2xs">
            <div className="flex items-start gap-2.5">
              <AlertTriangle className="w-4 h-4 text-amber-600 flex-shrink-0 mt-0.5" />
              <div>
                <p className="font-semibold text-amber-950 text-xs">{error.title}</p>
                <p className="mt-0.5 text-amber-800 leading-relaxed text-[11px]">{error.detail}</p>
              </div>
            </div>
            <button
              type="button"
              onClick={checkHealth}
              className="inline-flex items-center gap-1 bg-amber-100 hover:bg-amber-200 text-amber-900 px-2.5 py-1 rounded-lg text-xs font-semibold transition-colors flex-shrink-0 cursor-pointer"
            >
              <RefreshCw className="w-3 h-3" />
              <span>Retry</span>
            </button>
          </div>
        )}

        {messages.length === 0 ? (
          /* Calm Minimalist Landing View */
          <div className="my-auto py-12 px-4 text-center space-y-8 max-w-2xl mx-auto">
            {/* Primary Action Callout */}
            <div className="space-y-3">
              <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-teal-50 text-teal-700 mb-2 border border-teal-100 shadow-2xs">
                <MessageSquare className="w-7 h-7" />
              </div>
              <h2 className="text-2xl sm:text-3xl font-semibold text-stone-900 tracking-tight">
                Ask a health question
              </h2>
              <p className="text-sm text-stone-600 leading-relaxed max-w-lg mx-auto">
                Consult verified clinical evidence from official NHS guidance. Supports English, বাংলা (Native Bangla), and Banglish queries.
              </p>
            </div>

            {/* Subtle Clinical Features Pill Row */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2 text-left">
              <div className="bg-white p-3.5 rounded-xl border border-stone-200 shadow-2xs space-y-1">
                <div className="flex items-center gap-1.5 text-xs font-semibold text-stone-800">
                  <BookOpen className="w-4 h-4 text-teal-700" />
                  <span>Authoritative Grounding</span>
                </div>
                <p className="text-xs text-stone-500 leading-normal">
                  Strictly grounded in verified NHS clinical evidence passages under OGL v3.0.
                </p>
              </div>

              <div className="bg-white p-3.5 rounded-xl border border-stone-200 shadow-2xs space-y-1">
                <div className="flex items-center gap-1.5 text-xs font-semibold text-stone-800">
                  <Globe className="w-4 h-4 text-teal-700" />
                  <span>Multilingual Retrieval</span>
                </div>
                <p className="text-xs text-stone-500 leading-normal">
                  Understands colloquial Bangla, Banglish, and English clinical terminology.
                </p>
              </div>

              <div className="bg-white p-3.5 rounded-xl border border-stone-200 shadow-2xs space-y-1">
                <div className="flex items-center gap-1.5 text-xs font-semibold text-stone-800">
                  <ShieldCheck className="w-4 h-4 text-teal-700" />
                  <span>Zero Hallucination</span>
                </div>
                <p className="text-xs text-stone-500 leading-normal">
                  Direct passage retrieval with safety red-flag triage and transparent citations.
                </p>
              </div>
            </div>
          </div>
        ) : (
          /* Active Consultation View */
          <div className="flex-1 overflow-y-auto pb-4">
            <div className="flex items-center justify-between pb-3 mb-4 border-b border-stone-200">
              <div className="flex items-center gap-2 text-xs text-stone-500 font-medium">
                <span>Clinical Consultation</span>
                {currentContextState && currentContextState.clarification_turn_count > 0 && (
                  <span className="bg-teal-50 text-teal-800 text-[11px] font-semibold px-2.5 py-0.5 rounded-full border border-teal-200">
                    Turn {currentContextState.clarification_turn_count}/{currentContextState.max_clarification_turns}
                  </span>
                )}
              </div>
              <button
                type="button"
                onClick={handleResetConversation}
                className="inline-flex items-center gap-1.5 text-xs text-stone-600 hover:text-stone-900 bg-white hover:bg-stone-100 px-3 py-1.5 rounded-lg border border-stone-200 transition-colors cursor-pointer"
              >
                <RotateCcw className="w-3.5 h-3.5 text-stone-500" />
                <span>New Question</span>
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
              <div className="flex items-center gap-3 p-4 bg-white border border-stone-200 rounded-2xl max-w-sm mb-6 shadow-xs animate-pulse">
                <Loader2 className="w-5 h-5 text-teal-700 animate-spin" />
                <div>
                  <p className="text-xs font-semibold text-stone-800">Consulting clinical evidence...</p>
                  <p className="text-[11px] text-stone-500">Searching and reranking NHS knowledge base</p>
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
