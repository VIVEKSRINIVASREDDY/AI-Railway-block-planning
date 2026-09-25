import { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import { MessageSquare, X, Send, Bot, User, Loader2, Mic, MicOff, Trash2, ChevronDown } from 'lucide-react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs) { return twMerge(clsx(inputs)); }

const API = import.meta.env.VITE_API_URL || (import.meta.env.MODE === 'development' ? 'http://127.0.0.1:8000/api' : '/api');

const QUICK_PROMPTS = [
  { label: '🔴 Top risks today',          text: 'Which track section has the highest risk level today and why?' },
  { label: '📊 Show cost savings',         text: 'What are the estimated cost savings from integrating multiple departments in the same block?' },
  { label: '⚙️ Why Block #1 prioritized', text: 'Why was the first block prioritized in the current schedule? Explain the AI logic.' },
  { label: '🚦 Safety briefing',           text: 'Generate a 5-point safety briefing for today\'s maintenance blocks.' },
  { label: '🏗️ Civil Engineering summary', text: 'Summarize all Civil Engineering maintenance blocks scheduled this week.' },
  { label: '⚡ Electrical OHE status',     text: 'What is the current status of all Electrical OHE maintenance blocks? Any issues?' },
];

export default function AiChatbot() {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([
    { role: 'ai', content: '👋 Hi! I\'m **RailBot**, your AI control room assistant.\n\nAsk me anything about the current block schedule, track risks, KPIs, or safety briefings. You can also use the quick prompts below or speak via the 🎙️ mic button!' }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [listening, setListening] = useState(false);
  const [showChips, setShowChips] = useState(true);
  const messagesEndRef = useRef(null);
  const recognitionRef = useRef(null);
  const inputRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    if (isOpen) scrollToBottom();
  }, [messages, isOpen]);

  // Setup speech recognition
  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      const rec = new SpeechRecognition();
      rec.continuous = false;
      rec.interimResults = true;
      rec.lang = 'en-IN';

      rec.onresult = (event) => {
        const transcript = Array.from(event.results)
          .map(r => r[0].transcript).join('');
        setInput(transcript);
      };

      rec.onend = () => { setListening(false); };
      rec.onerror = () => { setListening(false); };
      recognitionRef.current = rec;
    }
  }, []);

  const toggleListening = () => {
    if (!recognitionRef.current) {
      alert('Speech recognition is not supported in your browser. Try Chrome.');
      return;
    }
    if (listening) {
      recognitionRef.current.stop();
      setListening(false);
    } else {
      setInput('');
      recognitionRef.current.start();
      setListening(true);
    }
  };

  const sendMessage = async (text) => {
    const msgText = (text || input).trim();
    if (!msgText || loading) return;

    if (listening) {
      recognitionRef.current?.stop();
      setListening(false);
    }

    setInput('');
    setShowChips(false);
    setMessages(prev => [...prev, { role: 'user', content: msgText }]);
    setLoading(true);

    try {
      const res = await axios.post(`${API}/chat`, { message: msgText });
      // Simulate streaming reveal
      const fullText = res.data.response || 'No response received.';
      setMessages(prev => [...prev, { role: 'ai', content: '', _streaming: true }]);

      let i = 0;
      const chunkSize = 4;
      const interval = setInterval(() => {
        i += chunkSize;
        setMessages(prev => {
          const updated = [...prev];
          const last = updated[updated.length - 1];
          if (last._streaming) {
            updated[updated.length - 1] = { ...last, content: fullText.slice(0, i) };
          }
          return updated;
        });
        if (i >= fullText.length) {
          clearInterval(interval);
          setMessages(prev => {
            const updated = [...prev];
            const last = updated[updated.length - 1];
            if (last._streaming) {
              updated[updated.length - 1] = { role: 'ai', content: fullText };
            }
            return updated;
          });
        }
      }, 18);
    } catch (err) {
      setMessages(prev => [...prev, { role: 'ai', content: '⚠️ Error connecting to the AI backend.' }]);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    sendMessage(input);
  };

  const clearChat = () => {
    setMessages([{ role: 'ai', content: '🔄 Chat cleared. Ask me anything about the railway block schedule!' }]);
    setShowChips(true);
  };

  // Simple markdown-like bold rendering
  const renderContent = (text) => {
    return text.split(/(\*\*[^*]+\*\*)/g).map((part, i) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        return <strong key={i} className="font-semibold text-white">{part.slice(2,-2)}</strong>;
      }
      return <span key={i}>{part}</span>;
    });
  };

  return (
    <>
      {/* Floating Chat Button */}
      <button
        onClick={() => setIsOpen(true)}
        className={cn(
          "fixed bottom-6 right-6 p-4 rounded-full bg-gradient-to-br from-emerald-500 to-teal-600 text-white shadow-lg shadow-emerald-500/30 hover:scale-110 hover:shadow-emerald-500/50 transition-all z-50",
          isOpen && "scale-0 opacity-0 pointer-events-none"
        )}
      >
        <Bot className="w-6 h-6" />
        <span className="absolute -top-1 -right-1 w-3 h-3 bg-white rounded-full border-2 border-black animate-pulse"/>
      </button>

      {/* Chat Window */}
      <div
        className={cn(
          "fixed bottom-6 right-6 w-[380px] max-h-[85vh] flex flex-col bg-[#0a0a0a] border border-[#1e1e1e] rounded-2xl shadow-2xl shadow-black/60 z-50 transition-all origin-bottom-right overflow-hidden",
          isOpen ? "scale-100 opacity-100" : "scale-75 opacity-0 pointer-events-none"
        )}
        style={{ height: '560px' }}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-[#1a1a1a] bg-[#050505] shrink-0">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-indigo-600 to-purple-600 flex items-center justify-center shadow-lg shadow-indigo-500/20">
              <Bot className="w-4 h-4 text-white" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-white">RailBot AI</h3>
              <p className="text-[10px] text-slate-500 flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                Powered by Gemini · Live Context
              </p>
            </div>
          </div>
          <div className="flex items-center gap-1">
            <button
              onClick={() => setShowChips(c => !c)}
              title="Toggle quick prompts"
              className="p-1.5 text-slate-500 hover:text-white hover:bg-white/5 rounded-lg transition-colors"
            >
              <ChevronDown className={cn("w-3.5 h-3.5 transition-transform", showChips && "rotate-180")}/>
            </button>
            <button onClick={clearChat} className="p-1.5 text-slate-500 hover:text-red-400 hover:bg-red-500/5 rounded-lg transition-colors" title="Clear chat">
              <Trash2 className="w-3.5 h-3.5" />
            </button>
            <button onClick={() => setIsOpen(false)} className="p-1.5 text-slate-500 hover:text-white hover:bg-white/5 rounded-lg transition-colors">
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        {/* Quick Prompt Chips */}
        {showChips && (
          <div className="px-3 pt-2 pb-1.5 border-b border-[#111] shrink-0">
            <div className="text-[9px] text-slate-600 uppercase font-semibold tracking-wider mb-1.5">Quick Prompts</div>
            <div className="flex flex-wrap gap-1.5 max-h-[70px] overflow-y-auto">
              {QUICK_PROMPTS.map((p, i) => (
                <button
                  key={i}
                  onClick={() => { setInput(p.text); sendMessage(p.text); }}
                  disabled={loading}
                  className="px-2.5 py-1 rounded-full border border-[#2a2a2a] bg-[#111] text-[10px] text-slate-400 hover:text-white hover:border-indigo-500/50 hover:bg-indigo-500/5 transition-all disabled:opacity-40 whitespace-nowrap"
                >
                  {p.label}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4 custom-scrollbar">
          {messages.map((msg, i) => (
            <div key={i} className={cn("flex gap-2 max-w-[88%]", msg.role === 'user' ? "ml-auto flex-row-reverse" : "")}>
              <div className={cn(
                "w-7 h-7 rounded-full flex items-center justify-center shrink-0 mt-1",
                msg.role === 'user' ? "bg-indigo-600/30 text-indigo-300" : "bg-gradient-to-br from-indigo-600 to-purple-600 text-white"
              )}>
                {msg.role === 'user' ? <User className="w-3.5 h-3.5" /> : <Bot className="w-3.5 h-3.5" />}
              </div>
              <div className={cn(
                "px-3.5 py-2.5 text-sm rounded-2xl leading-relaxed",
                msg.role === 'user'
                  ? "bg-indigo-600/15 text-indigo-100 border border-indigo-500/20 rounded-tr-sm"
                  : "bg-[#111] border border-[#1e1e1e] text-slate-300 rounded-tl-sm"
              )}>
                {renderContent(msg.content)}
                {msg._streaming && <span className="inline-block w-1 h-3.5 bg-indigo-400 animate-pulse ml-0.5 rounded-sm"/>}
              </div>
            </div>
          ))}
          {loading && !messages[messages.length-1]?._streaming && (
            <div className="flex gap-2 max-w-[85%]">
              <div className="w-7 h-7 rounded-full flex items-center justify-center shrink-0 mt-1 bg-gradient-to-br from-indigo-600 to-purple-600 text-white">
                <Bot className="w-3.5 h-3.5" />
              </div>
              <div className="px-4 py-3 text-sm rounded-2xl bg-[#111] border border-[#1e1e1e] rounded-tl-sm flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 bg-slate-600 rounded-full animate-bounce [animation-delay:-0.3s]"/>
                <span className="w-1.5 h-1.5 bg-slate-600 rounded-full animate-bounce [animation-delay:-0.15s]"/>
                <span className="w-1.5 h-1.5 bg-slate-600 rounded-full animate-bounce"/>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Voice listening indicator */}
        {listening && (
          <div className="px-4 py-2 bg-red-500/5 border-t border-red-500/20 flex items-center gap-2 shrink-0">
            <div className="w-2 h-2 rounded-full bg-red-500 animate-pulse"/>
            <span className="text-xs text-red-400 font-medium">Listening... speak now</span>
            <span className="text-xs text-slate-500 ml-auto">Say your question</span>
          </div>
        )}

        {/* Input */}
        <div className="p-3 bg-[#050505] border-t border-[#1a1a1a] shrink-0">
          <form onSubmit={handleSubmit} className="relative flex items-center gap-2">
            <button
              type="button"
              onClick={toggleListening}
              className={cn(
                "shrink-0 w-8 h-8 rounded-xl flex items-center justify-center transition-all border",
                listening
                  ? "bg-red-500/20 border-red-500/50 text-red-400 animate-pulse"
                  : "bg-[#111] border-[#222] text-slate-500 hover:text-white hover:border-[#333]"
              )}
              title={listening ? "Stop listening" : "Voice input"}
            >
              {listening ? <MicOff className="w-3.5 h-3.5"/> : <Mic className="w-3.5 h-3.5"/>}
            </button>
            <input
              ref={inputRef}
              type="text"
              value={input}
              onChange={e => setInput(e.target.value)}
              placeholder={listening ? "Listening..." : "Ask about the schedule..."}
              className="flex-1 bg-[#111] border border-[#222] rounded-xl pl-3 pr-9 py-2 text-sm text-white placeholder-slate-600 focus:outline-none focus:border-indigo-500/40 transition-colors"
              disabled={loading}
            />
            <button
              type="submit"
              disabled={!input.trim() || loading}
              className="absolute right-2 p-1.5 text-indigo-400 hover:text-indigo-300 disabled:opacity-30 transition-colors"
            >
              {loading ? <Loader2 className="w-4 h-4 animate-spin"/> : <Send className="w-4 h-4"/>}
            </button>
          </form>
        </div>
      </div>
    </>
  );
}
