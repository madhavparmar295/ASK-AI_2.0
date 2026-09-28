import { X, Plus, MessageSquare, Trash2, Clock, Calendar } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

export default function HistoryDrawer({
  isOpen,
  onClose,
  sessions = [],
  currentSessionId,
  onSelectSession,
  onNewChat,
  onDeleteSession,
}) {
  const { isAuthenticated, openAuthModal } = useAuth();

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-40 flex">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/60 backdrop-blur-sm transition-opacity animate-fadeIn"
        onClick={onClose}
      />

      {/* Drawer Panel */}
      <div className="relative w-80 md:w-96 h-full glass-strong border-r border-white/10 bg-[#0c0919]/95 text-white z-50 flex flex-col shadow-2xl animate-slideRight">

        {/* Top Header */}
        <div className="p-4 border-b border-white/10 flex items-center justify-between flex-shrink-0">
          <div className="flex items-center gap-2">
            <Clock className="w-4 h-4 text-purple-400" />
            <h2 className="font-bold text-sm tracking-wide text-white">Chat History</h2>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-gray-400 hover:text-white hover:bg-white/10 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* New Chat Button */}
        <div className="p-3 border-b border-white/5 flex-shrink-0">
          <button
            onClick={() => {
              onNewChat();
              onClose();
            }}
            className="w-full py-2 px-3 rounded-xl bg-purple-600/20 hover:bg-purple-600/30 text-purple-300 border border-purple-500/30 text-xs font-semibold flex items-center justify-center gap-2 transition-all hover:scale-[1.02] active:scale-95"
          >
            <Plus className="w-4 h-4 text-purple-400" />
            <span>Start New Conversation</span>
          </button>
        </div>

        {/* Sessions List */}
        <div className="flex-1 overflow-y-auto p-3 space-y-2">
          {!isAuthenticated ? (
            <div className="text-center py-12 px-4">
              <MessageSquare className="w-8 h-8 text-gray-500 mx-auto mb-3 opacity-50" />
              <p className="text-xs text-gray-400 mb-3">
                Sign in to save and sync your conversations across all devices.
              </p>
              <button
                onClick={() => {
                  onClose();
                  openAuthModal('login');
                }}
                className="py-1.5 px-4 rounded-lg bg-purple-600 text-white text-xs font-medium hover:bg-purple-500 transition-colors shadow-md"
              >
                Sign In Now
              </button>
            </div>
          ) : sessions.length === 0 ? (
            <div className="text-center py-12 px-4 text-gray-500">
              <Clock className="w-8 h-8 mx-auto mb-3 opacity-30" />
              <p className="text-xs">No chat history yet.</p>
              <p className="text-[11px] text-gray-600 mt-1">Start chatting to automatically save your sessions!</p>
            </div>
          ) : (
            sessions.map((session) => {
              const isSelected = currentSessionId === session.id;
              const formattedDate = new Date(session.updated_at || session.created_at).toLocaleDateString([], {
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit',
              });

              return (
                <div
                  key={session.id}
                  className={`group relative flex items-start justify-between p-3 rounded-xl border transition-all cursor-pointer ${isSelected
                      ? 'bg-purple-600/25 border-purple-500/40 text-white shadow-sm'
                      : 'bg-white/5 border-white/5 text-gray-300 hover:bg-white/10 hover:text-white'
                    }`}
                  onClick={() => {
                    onSelectSession(session);
                    onClose();
                  }}
                >
                  <div className="flex-1 min-w-0 pr-2">
                    <p className="text-xs font-semibold truncate leading-tight mb-1">
                      {session.title || 'Conversation'}
                    </p>
                    <div className="flex items-center gap-1 text-[10px] text-gray-500">
                      <Calendar className="w-2.5 h-2.5" />
                      <span>{formattedDate}</span>
                      <span>•</span>
                      <span>{session.messages?.length || 0} msgs</span>
                    </div>
                  </div>

                  {/* Delete button */}
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onDeleteSession(session.id);
                    }}
                    className="opacity-0 group-hover:opacity-100 p-1 text-gray-500 hover:text-red-400 hover:bg-red-500/10 rounded transition-all"
                    title="Delete session"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              );
            })
          )}
        </div>

        {/* Footer */}
        <div className="p-3 border-t border-white/10 text-center flex-shrink-0">
          <p className="text-[10px] text-gray-500">
            Conversations are encrypted & synced with your account.
          </p>
        </div>
      </div>
    </div>
  );
}
