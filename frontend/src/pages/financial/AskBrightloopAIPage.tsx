import { useState } from 'react';
import { apiClient } from '../../api/client';
import { 
  Bot, 
  Send, 
  Sparkles, 
  ShieldCheck, 
  Cpu
} from 'lucide-react';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  provider?: string;
  groundedData?: any;
}

const PRESET_QUESTIONS = [
  "How much revenue is currently overdue?",
  "What is our Monthly Recurring Revenue (MRR)?",
  "Which customers have the highest outstanding balance?",
  "What is our payment collection success rate?",
  "Are there any critical revenue leakage risks?",
];

export function AskBrightloopAIPage() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'assistant',
      content: "Hello! I am your Brightloop Financial Intelligence Assistant. I am directly grounded in your live MySQL billing database and can answer queries about MRR, accounts receivable, overdue balances, discounts, and revenue leakage.",
      provider: "system",
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSend = async (queryText?: string) => {
    const textToSend = queryText || input;
    if (!textToSend.trim() || loading) return;

    const userMessage: Message = { role: 'user', content: textToSend };
    setMessages((prev) => [...prev, userMessage]);
    if (!queryText) setInput('');
    setLoading(true);

    try {
      const res = await apiClient.post('/ai-assistant/query', { query: textToSend });
      const assistantMessage: Message = {
        role: 'assistant',
        content: res.data.answer,
        provider: res.data.provider,
        groundedData: res.data.grounded_data,
      };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: "I encountered an error querying the financial analytics engine. Please ensure backend services are operational.",
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Header */}
      <div className="bg-slate-950/70 p-6 rounded-2xl border border-slate-800 shadow-xl flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="bg-indigo-600 p-2.5 rounded-xl shadow-lg shadow-indigo-600/30 text-white">
            <Bot className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-xl font-extrabold text-white">Ask Brightloop AI Assistant</h2>
            <p className="text-slate-400 text-xs">
              Natural language financial intelligence grounded in live database queries.
            </p>
          </div>
        </div>
        <span className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
          <ShieldCheck className="w-3.5 h-3.5" />
          <span>Strictly Grounded DB Queries</span>
        </span>
      </div>

      {/* Suggested Questions */}
      <div className="space-y-1.5">
        <span className="text-xs text-slate-400 font-semibold flex items-center space-x-1">
          <Sparkles className="w-3 h-3 text-indigo-400" />
          <span>Quick Analysis Prompts:</span>
        </span>
        <div className="flex flex-wrap gap-2">
          {PRESET_QUESTIONS.map((q, idx) => (
            <button
              key={idx}
              onClick={() => handleSend(q)}
              className="text-xs bg-slate-900/90 hover:bg-indigo-600/20 hover:text-indigo-300 text-slate-300 px-3 py-1.5 rounded-xl border border-slate-800 transition"
            >
              {q}
            </button>
          ))}
        </div>
      </div>

      {/* Chat Messages Container */}
      <div className="bg-slate-950/60 rounded-2xl border border-slate-800 p-6 min-h-[420px] max-h-[550px] overflow-y-auto space-y-4 shadow-xl">
        {messages.map((m, idx) => (
          <div
            key={idx}
            className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-xl rounded-2xl p-4 text-xs space-y-2 leading-relaxed ${
                m.role === 'user'
                  ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/20'
                  : 'bg-slate-900/90 text-slate-200 border border-slate-800 shadow-md'
              }`}
            >
              <div className="flex items-center space-x-2 border-b border-white/10 pb-1.5 font-semibold text-[11px]">
                {m.role === 'user' ? (
                  <span>You</span>
                ) : (
                  <span className="flex items-center space-x-1.5 text-indigo-400">
                    <Cpu className="w-3.5 h-3.5" />
                    <span>Brightloop Intelligence Engine</span>
                  </span>
                )}
                {m.provider && (
                  <span className="text-[10px] uppercase font-mono px-1.5 py-0.2 rounded bg-slate-800 text-slate-400 ml-auto">
                    {m.provider}
                  </span>
                )}
              </div>
              <p className="whitespace-pre-line">{m.content}</p>
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 text-xs text-slate-400 flex items-center space-x-2">
              <span className="w-2 h-2 rounded-full bg-indigo-500 animate-ping"></span>
              <span>Analyzing live database telemetry...</span>
            </div>
          </div>
        )}
      </div>

      {/* Chat Input Bar */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleSend();
        }}
        className="flex items-center space-x-3 bg-slate-950/80 p-2 rounded-2xl border border-slate-800 shadow-xl"
      >
        <input
          type="text"
          placeholder="Ask a financial question e.g. What is our current MRR?"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          className="flex-1 bg-transparent px-4 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none"
        />
        <button
          type="submit"
          disabled={loading || !input.trim()}
          className="px-4 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-semibold shadow-lg shadow-indigo-600/30 transition disabled:opacity-40 flex items-center space-x-1.5"
        >
          <span>Ask</span>
          <Send className="w-3.5 h-3.5" />
        </button>
      </form>
    </div>
  );
}
