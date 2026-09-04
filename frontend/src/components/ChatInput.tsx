import React, { useState, KeyboardEvent } from 'react';
import { Send, Loader2, Globe } from 'lucide-react';

interface ChatInputProps {
  onSendMessage: (msg: string, preferredLang: string) => void;
  isLoading: boolean;
}

const QUICK_PROMPTS = [
  { label: 'Burns', text: 'How to treat a minor burn with cool running water?' },
  { label: 'জ্বর', text: 'বাচ্চার জ্বর হলে কোন তাপমাত্রায় ১১১ কল করব?' },
  { label: 'Bleeding', text: 'kete geche bleeding thamtase na ki prothom shongshep korbo?' },
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
    <div className="bg-white/95 backdrop-blur-md border-t border-stone-200 p-3 sm:p-4 sticky bottom-0 z-20">
      <div className="max-w-4xl mx-auto space-y-2.5">
        {/* Top bar: Quick prompt chips & Language Selector */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
          {/* Quick Prompts */}
          <div className="flex items-center gap-1.5 overflow-x-auto text-xs py-0.5 no-scrollbar">
            <span className="text-[11px] text-stone-400 font-medium whitespace-nowrap pl-1">
              Sample queries:
            </span>
            {QUICK_PROMPTS.map((prompt, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => setInput(prompt.text)}
                className="bg-stone-100 hover:bg-teal-50 hover:text-teal-900 text-stone-600 px-2.5 py-1 rounded-full text-xs font-normal border border-stone-200 hover:border-teal-200 transition-colors whitespace-nowrap flex items-center gap-1.5 cursor-pointer"
              >
                <span className="font-semibold text-[10px] text-teal-800 bg-teal-100/70 px-1 py-0.2 rounded">
                  {prompt.label}
                </span>
                <span className="truncate max-w-[200px]">{prompt.text}</span>
              </button>
            ))}
          </div>

          {/* Response Language Preference Selector */}
          <div className="flex items-center gap-1 self-start sm:self-auto bg-stone-100 p-0.5 rounded-lg border border-stone-200 text-xs">
            <div className="flex items-center gap-1 text-stone-500 font-medium px-1.5">
              <Globe className="w-3 h-3 text-stone-500" />
              <span className="text-[11px]">Output:</span>
            </div>
            <button
              type="button"
              onClick={() => setResponseLang('auto')}
              className={`px-2 py-0.5 rounded text-[11px] font-medium transition-all cursor-pointer ${
                responseLang === 'auto'
                  ? 'bg-white text-teal-900 shadow-2xs border border-stone-200 font-semibold'
                  : 'text-stone-600 hover:text-stone-900'
              }`}
            >
              Auto
            </button>
            <button
              type="button"
              onClick={() => setResponseLang('bn')}
              className={`px-2 py-0.5 rounded text-[11px] font-medium transition-all cursor-pointer ${
                responseLang === 'bn'
                  ? 'bg-white text-teal-900 shadow-2xs border border-stone-200 font-semibold'
                  : 'text-stone-600 hover:text-stone-900'
              }`}
            >
              বাংলা
            </button>
            <button
              type="button"
              onClick={() => setResponseLang('en')}
              className={`px-2 py-0.5 rounded text-[11px] font-medium transition-all cursor-pointer ${
                responseLang === 'en'
                  ? 'bg-white text-teal-900 shadow-2xs border border-stone-200 font-semibold'
                  : 'text-stone-600 hover:text-stone-900'
              }`}
            >
              English
            </button>
          </div>
        </div>

        {/* Input Text Form */}
        <form onSubmit={handleSubmit} className="flex gap-2 items-end">
          <div className="relative flex-1">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask a health question in English, বাংলা, or Banglish..."
              rows={2}
              disabled={isLoading}
              className="w-full resize-none bg-stone-50 focus:bg-white text-sm text-stone-900 border border-stone-300 rounded-2xl p-3 pr-16 focus:outline-none focus:ring-2 focus:ring-teal-600 focus:border-transparent transition-all placeholder:text-stone-400 disabled:opacity-50 font-sans"
            />
            <div className="absolute right-3 bottom-3 text-[10px] text-stone-400 hidden sm:block pointer-events-none">
              <kbd className="bg-stone-200/80 text-stone-600 px-1.5 py-0.5 rounded text-[10px] font-mono">↵ Send</kbd>
            </div>
          </div>

          <button
            type="submit"
            disabled={!input.trim() || isLoading}
            className="h-[52px] px-5 bg-teal-700 hover:bg-teal-800 disabled:bg-stone-200 text-white disabled:text-stone-400 font-medium rounded-2xl flex items-center justify-center gap-2 transition-all shadow-xs flex-shrink-0 cursor-pointer disabled:cursor-not-allowed"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin text-teal-200" />
                <span className="hidden sm:inline text-xs font-semibold">Consulting...</span>
              </>
            ) : (
              <>
                <Send className="w-4 h-4" />
                <span className="hidden sm:inline text-xs font-semibold">Search</span>
              </>
            )}
          </button>
        </form>
      </div>
    </div>
  );
};
export default ChatInput;
