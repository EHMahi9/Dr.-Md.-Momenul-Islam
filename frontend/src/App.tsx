import React, { useState, useEffect, useRef } from 'react';
import { Header } from './components/Header';
import { ChatInput } from './components/ChatInput';
import { ChatMessageItem } from './components/ChatMessageItem';
import { Message, HealthResponse } from './types';
import { fetchHealth, sendChatMessage } from './services/api';
import { ShieldCheck, Info, MessageSquare, Database, AlertTriangle } from 'lucide-react';

export const App: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetchHealth()
      .then((data) => setHealth(data))
      .catch((err) => {
        console.warn('Backend health check failed:', err);
        setError('Backend is offline or unreachable. Please start the FastAPI backend on port 8000.');
      });
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const handleSendMessage = async (text: string) => {
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
      const response = await sendChatMessage(text);
      const assistantMsg: Message = {
        id: `assistant-${Date.now()}`,
        sender: 'assistant',
        text: response.synthetic_answer,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        evidence: response.evidence,
        generationEnabled: response.generation_enabled,
      };

      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err: any) {
      setError(err.message || 'An error occurred during evidence retrieval.');
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
          <div className="mb-4 bg-rose-50 border border-rose-200 text-rose-800 p-4 rounded-xl flex items-start gap-3 text-xs">
            <AlertTriangle className="w-4 h-4 text-rose-600 flex-shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold">Connection Error</p>
              <p className="mt-0.5">{error}</p>
            </div>
          </div>
        )}

        {messages.length === 0 ? (
          <div className="my-auto py-12 px-4 text-center space-y-6">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-sky-100 text-sky-700 shadow-inner">
              <MessageSquare className="w-8 h-8" />
            </div>

            <div className="max-w-xl mx-auto space-y-2">
              <h2 className="text-xl font-bold text-slate-900">
                Dr. Md. Momenul Islam Health Intelligence
              </h2>
              <p className="text-xs text-slate-600 leading-relaxed">
                Welcome to the research prototype. This system integrates the frozen{' '}
                <strong>Dual-Anchor Fusion Reranker</strong> to retrieve verified NHS evidence
                across English, Native Bangla (বাংলা), and Banglish queries.
              </p>
            </div>

            {/* Architecture Explainer Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 max-w-3xl mx-auto text-left pt-4">
              <div className="bg-white p-3.5 rounded-xl border border-slate-200 shadow-xs space-y-1">
                <div className="flex items-center gap-1.5 text-xs font-bold text-slate-800">
                  <Database className="w-3.5 h-3.5 text-sky-600" />
                  <span>Authoritative NHS Grounding</span>
                </div>
                <p className="text-[11px] text-slate-500 leading-normal">
                  Grounds strictly against 68 indexed NHS clinical passages with full provenance and OGL v3.0 licensing.
                </p>
              </div>

              <div className="bg-white p-3.5 rounded-xl border border-slate-200 shadow-xs space-y-1">
                <div className="flex items-center gap-1.5 text-xs font-bold text-slate-800">
                  <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
                  <span>Multilingual Normalization</span>
                </div>
                <p className="text-[11px] text-slate-500 leading-normal">
                  Deterministic Unicode-safe dictionary expansion for colloquial Bangla and Banglish medical terms.
                </p>
              </div>

              <div className="bg-white p-3.5 rounded-xl border border-slate-200 shadow-xs space-y-1">
                <div className="flex items-center gap-1.5 text-xs font-bold text-slate-800">
                  <Info className="w-3.5 h-3.5 text-amber-600" />
                  <span>Generation Disabled</span>
                </div>
                <p className="text-[11px] text-slate-500 leading-normal">
                  LLM free-form generation is locked off by protocol to inspect raw retrieval veracity safely.
                </p>
              </div>
            </div>
          </div>
        ) : (
          <div className="flex-1 overflow-y-auto pb-4">
            {messages.map((msg) => (
              <ChatMessageItem key={msg.id} message={msg} />
            ))}
            <div ref={messagesEndRef} />
          </div>
        )}
      </main>

      <ChatInput onSendMessage={handleSendMessage} isLoading={isLoading} />
    </div>
  );
};
export default App;
