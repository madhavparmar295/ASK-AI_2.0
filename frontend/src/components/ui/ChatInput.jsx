import { useState, useRef } from 'react';
import { Paperclip, Mic, Send } from 'lucide-react';

export default function ChatInput({ onSend, onFileUpload, disabled = false }) {
  const [message, setMessage] = useState('');
  const [isListening, setIsListening] = useState(false);
  const fileInputRef = useRef(null);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (message.trim() && !disabled) {
      onSend?.(message);
      setMessage('');
    }
  };

  const handleAttachment = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      onFileUpload?.(file);
      e.target.value = '';
    }
  };

  const handleVoiceInput = () => {
    setIsListening(!isListening);
  };

  return (
    <div className="w-full max-w-3xl mx-auto px-2 md:px-4">
      {/* Hidden file input */}
      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileChange}
        className="hidden"
        accept=".pdf,.docx,.doc,.txt,.csv,.xlsx,.xls"
      />

      <form onSubmit={handleSubmit} className="relative">
        {/* Floating Gemini-style Input Pill */}
        <div className="rounded-2xl p-2.5 md:p-3 flex items-center gap-2.5 bg-[#141726]/90 backdrop-blur-xl border border-white/10 shadow-2xl focus-within:border-purple-500/40 focus-within:shadow-[0_0_30px_rgba(139,92,246,0.15)] transition-all">
          {/* Attachment button */}
          <button
            type="button"
            onClick={handleAttachment}
            disabled={disabled}
            className="flex-shrink-0 w-8 h-8 rounded-xl bg-white/5 hover:bg-white/10 disabled:opacity-50 flex items-center justify-center transition-colors text-gray-400 hover:text-white"
            title="Attach document (.pdf, .docx, .txt, etc.)"
            aria-label="Attach file"
          >
            <Paperclip className="w-4 h-4" />
          </button>

          {/* Text input */}
          <input
            type="text"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder={disabled ? "Thinking..." : "Ask questions about your emails, documents, or data..."}
            disabled={disabled}
            className="flex-1 bg-transparent text-sm md:text-base text-white placeholder-gray-500 outline-none disabled:opacity-50"
          />

          {/* Mic button */}
          <button
            type="button"
            onClick={handleVoiceInput}
            disabled={disabled}
            className={`flex-shrink-0 w-8 h-8 rounded-xl flex items-center justify-center transition-all ${isListening
                ? 'bg-red-500/20 text-red-400 pulse-glow'
                : 'bg-white/5 hover:bg-white/10 text-gray-400 hover:text-white'
              } disabled:opacity-50`}
            aria-label="Voice input"
          >
            <Mic className="w-4 h-4" />
          </button>

          {/* Send button */}
          <button
            type="submit"
            disabled={!message.trim() || disabled}
            className="flex-shrink-0 w-8 h-8 rounded-xl bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 disabled:from-purple-900/30 disabled:to-indigo-900/30 disabled:cursor-not-allowed flex items-center justify-center transition-all hover:scale-105 active:scale-95 shadow-md shadow-purple-600/20"
            aria-label="Send message"
          >
            <Send className="w-3.5 h-3.5 text-white" />
          </button>
        </div>
      </form>

      {/* Footer disclaimer */}
      <p className="text-center text-[11px] text-gray-500 mt-2.5">
        Ask AI answers questions based on your indexed emails and uploaded files.
      </p>
    </div>
  );
}
