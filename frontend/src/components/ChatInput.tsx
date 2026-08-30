import React, { useState, KeyboardEvent } from 'react';
import { Send, Loader2, Languages, Globe } from 'lucide-react';

interface ChatInputProps {
  onSendMessage: (msg: string, preferredLang: string) => void;
  isLoading: boolean;
}

const QUICK_PROMPTS = [
  { label: 'English', text: 'How to treat a minor burn with cool running water?' },
  { label: 'বাংলা', text: 'বাচ্চার জ্বর হলে কোন তাপমাত্রায় ১১১ কল করব?' },
  { label: 'Banglish', text: 'kete geche bleeding thamtase na ki prothom shongshep korbo?' },
  { label: 'Nosebleed', text: 'nak die rokt porce koto minute chepe rakhbo?' }
];

export const ChatInput: React.FC<ChatInputProps> = ({ onSendMessage, isLoading }) => {
  const [input, setInput] = useState('');
  const [responseLang, setResponseLang] = useState<'auto' | 'bn' | 'en'>('auto');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;
    onSendMessage(input.trim(), responseLang);
    setInput('');
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <div className="bg-white border-t border-slate-200 p-4 shadow-lg sticky bottom-0">
      <div className="max-w-5xl mx-auto space-y-3">
        {/* Top Controls: Language Preference & Quick Prompts */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2.5 pb-1">
          {/* Quick Prompts */}
          <div className="flex items-center gap-2 overflow-x-auto text-xs no-scrollbar">
            <div className="flex items-center gap-1 text-slate-400 font-medium whitespace-nowrap pl-1">
              <Languages className="w-3.5 h-3.5 text-sky-600" />
              <span>Try sample:</span>
            </div>
            {QUICK_PROMPTS.map((prompt, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => setInput(prompt.text)}
                className="bg-slate-100 hover:bg-sky-50 hover:text-sky-800 text-slate-600 px-2.5 py-1 rounded-full text-xs font-normal border border-slate-200 transition-colors whitespace-nowrap flex items-center gap-1.5"
              >
                <span className="font-semibold text-[10px] text-sky-700 bg-sky-100/80 px-1 py-0.2 rounded">
                  {prompt.label}
                </span>
                <span>{prompt.text}</span>
              </button>
            ))}
          </div>

          {/* Part H: Response Language Selector */}
          <div className="flex items-center gap-1.5 self-start sm:self-auto bg-slate-100 p-1 rounded-lg border border-slate-200 text-xs">
            <div className="flex items-center gap-1 text-slate-500 font-medium px-1.5">
              <Globe className="w-3.5 h-3.5 text-slate-600" />
              <span className="text-[11px]">Response:</span>
            </div>
            <button
              type="button"
              onClick={() => setResponseLang('auto')}
              className={`px-2 py-0.5 rounded text-[11px] font-semibold transition-all cursor-pointer ${
                responseLang === 'auto'
                  ? 'bg-white text-sky-800 shadow-xs border border-slate-200'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Auto
            </button>
            <button
              type="button"
              onClick={() => setResponseLang('bn')}
              className={`px-2 py-0.5 rounded text-[11px] font-semibold transition-all cursor-pointer ${
                responseLang === 'bn'
                  ? 'bg-white text-emerald-800 shadow-xs border border-slate-200'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              বাংলা
            </button>
            <button
              type="button"
              onClick={() => setResponseLang('en')}
              className={`px-2 py-0.5 rounded text-[11px] font-semibold transition-all cursor-pointer ${
                responseLang === 'en'
                  ? 'bg-white text-sky-800 shadow-xs border border-slate-200'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              English
            </button>
          </div>
        </div>

        {/* Text Input Box */}
        <form onSubmit={handleSubmit} className="flex gap-2.5 items-end">
          <div className="relative flex-1">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask any health question in English, বাংলা (Native Bangla), or Banglish..."
              rows={2}
              disabled={isLoading}
              className="w-full resize-none bg-slate-50 focus:bg-white text-sm text-slate-900 border border-slate-300 rounded-xl p-3 pr-10 focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-transparent transition-all placeholder:text-slate-400 disabled:opacity-50"
            />
            <div className="absolute right-3 bottom-3 text-[11px] text-slate-400 hidden sm:block pointer-events-none">
              Press <kbd className="bg-slate-200 text-slate-600 px-1 py-0.5 rounded text-[10px] font-mono">Enter ↵</kbd>
            </div>
          </div>

          <button
            type="submit"
            disabled={!input.trim() || isLoading}
            className="h-[52px] px-5 bg-sky-600 hover:bg-sky-700 disabled:bg-slate-200 text-white disabled:text-slate-400 font-medium rounded-xl flex items-center justify-center gap-2 transition-all shadow-sm flex-shrink-0 cursor-pointer disabled:cursor-not-allowed"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span className="hidden sm:inline text-xs">Retrieving...</span>
              </>
            ) : (
              <>
                <Send className="w-4 h-4" />
                <span className="hidden sm:inline text-xs font-semibold">Retrieve</span>
              </>
            )}
          </button>
        </form>
      </div>
    </div>
  );
};
