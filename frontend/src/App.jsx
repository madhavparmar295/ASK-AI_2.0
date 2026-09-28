import { useState, useRef, useEffect } from 'react';
import { ChevronDown, ChevronUp, FileText, Sparkles } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import GeminiBackground from './components/background/GeminiBackground';
import Sidebar from './components/layout/Sidebar';
import MainContent from './components/layout/MainContent';
import ChatInput from './components/ui/ChatInput';
import AuthModal from './components/auth/AuthModal';
import HistoryDrawer from './components/history/HistoryDrawer';
import { AuthProvider, useAuth } from './context/AuthContext';
import { API_CONFIG, sendMessage, uploadFile } from './services/api';
import { getDemoResponse } from './services/demoService';
import logoImg from './assets/logo.png';
import {
  fetchChatHistory,
  saveChatSession,
  deleteChatSession,
} from './services/chatHistoryService';

function ChatApp() {
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [expandedSources, setExpandedSources] = useState({});
  const messagesEndRef = useRef(null);

  // Chat History & Session State
  const [sessions, setSessions] = useState([]);
  const [currentSessionId, setCurrentSessionId] = useState(null);
  const [isHistoryDrawerOpen, setIsHistoryDrawerOpen] = useState(false);

  const { user, isAuthenticated } = useAuth();

  // Auto-scroll to bottom of messages
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  // Load chat history when user logs in, or clear when user logs out
  useEffect(() => {
    if (!isAuthenticated || !user?.email) {
      setMessages([]);
      setSessions([]);
      setCurrentSessionId(null);
      setIsHistoryDrawerOpen(false);
      return;
    }

    let isCancelled = false;
    async function loadUserHistory() {
      try {
        const userSessions = await fetchChatHistory(user.email);
        if (!isCancelled) {
          setSessions(userSessions);
          if (userSessions.length > 0) {
            const latest = userSessions[0];
            setCurrentSessionId(latest.id);
            setMessages(latest.messages || []);
          }
        }
      } catch (err) {
        console.error('Error loading history:', err);
      }
    }

    loadUserHistory();
    return () => {
      isCancelled = true;
    };
  }, [isAuthenticated, user?.email]);

  const toggleSources = (messageId) => {
    setExpandedSources((prev) => ({
      ...prev,
      [messageId]: !prev[messageId],
    }));
  };

  // Start a fresh conversation
  const handleNewChat = () => {
    setMessages([]);
    setCurrentSessionId(null);
  };

  // Select an existing conversation from history
  const handleSelectSession = (session) => {
    setCurrentSessionId(session.id);
    setMessages(session.messages || []);
  };

  // Delete a session
  const handleDeleteSession = async (sessionId) => {
    if (!user?.email) return;
    await deleteChatSession(user.email, sessionId);
    setSessions((prev) => prev.filter((s) => s.id !== sessionId));
    if (currentSessionId === sessionId) {
      handleNewChat();
    }
  };

  // Handle sending messages
  const handleSendMessage = async (messageText) => {
    if (!messageText.trim() || isLoading) return;

    const userMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: messageText,
      timestamp: new Date().toISOString(),
    };

    const newMessages = [...messages, userMessage];
    setMessages(newMessages);
    setIsLoading(true);

    try {
      let response;
      if (API_CONFIG.DEMO_MODE) {
        response = await getDemoResponse(messageText);
      } else {
        const activeEmail = user?.email || API_CONFIG.DEFAULT_USER_EMAIL;
        const recentChatHistory = messages.slice(-6).map((m) => ({
          role: m.role === 'user' ? 'user' : 'assistant',
          content: m.content,
        }));
        response = await sendMessage(messageText, {
          userEmail: activeEmail,
          chatHistory: recentChatHistory,
        });
      }

      if (response.success) {
        const assistantMessage = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: response.data.message,
          sources: response.data.sources || [],
          timestamp: response.data.timestamp || new Date().toISOString(),
        };
        const finalMessages = [...newMessages, assistantMessage];
        setMessages(finalMessages);

        // Auto-save session to Django backend
        if (isAuthenticated && user?.email) {
          const syncRes = await saveChatSession(
            user.email,
            currentSessionId,
            finalMessages
          );
          if (syncRes && syncRes.session_id) {
            setCurrentSessionId(syncRes.session_id);
            fetchChatHistory(user.email).then(setSessions);
          }
        }
      }
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        isError: true,
        content: `⚠️ Failed to get response: ${error.message}. Please check if the backend service is reachable.`,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  // Handle document file upload
  const handleFileUpload = async (file) => {
    const uploadNotice = {
      id: Date.now().toString(),
      role: 'user',
      content: `📎 Uploading document: ${file.name}...`,
      timestamp: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, uploadNotice]);
    setIsLoading(true);

    try {
      const activeEmail = user?.email || API_CONFIG.DEFAULT_USER_EMAIL;
      const res = await uploadFile(file, activeEmail);
      const successNotice = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `✅ Successfully uploaded & indexed **${res.filename || file.name}**! You can now ask questions about its content.`,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, successNotice]);
    } catch (error) {
      console.error('Error uploading file:', error);
      const errorNotice = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        isError: true,
        content: `❌ Document upload failed: ${error.message}`,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errorNotice]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="relative w-screen h-screen overflow-hidden text-gray-100 flex">
      {/* Calm Gemini Dark Background */}
      <GeminiBackground />

      {/* Auth Modal */}
      <AuthModal />

      {/* History Drawer */}
      <HistoryDrawer
        isOpen={isHistoryDrawerOpen}
        onClose={() => setIsHistoryDrawerOpen(false)}
        sessions={sessions}
        currentSessionId={currentSessionId}
        onSelectSession={handleSelectSession}
        onNewChat={handleNewChat}
        onDeleteSession={handleDeleteSession}
      />

      {/* Sidebar Navigation: Desktop side bar + Mobile top header */}
      <Sidebar
        onOpenHistory={() => setIsHistoryDrawerOpen(true)}
        onNewChat={handleNewChat}
      />

      {/* Main Full-Width Content Area */}
      <div className="flex-1 md:pl-14 flex flex-col h-full w-full min-w-0 overflow-hidden">
        {messages.length === 0 ? (
          // Welcome View when no messages
          <div className="flex-1 overflow-y-auto flex flex-col w-full pt-16 md:pt-0">
            <MainContent
              onSend={handleSendMessage}
              onFileUpload={handleFileUpload}
              disabled={isLoading}
            />
          </div>
        ) : (
          // Active Chat View: Full-width scroll container, scrollbar at edge of window
          <div className="flex-1 flex flex-col h-full w-full min-w-0 overflow-hidden">
            {/* Messages Scroll Area - pt-20 on mobile ensures first message is never hidden under the fixed header */}
            <div className="flex-1 overflow-y-auto w-full px-3 md:px-12 lg:px-24 pt-20 pb-8 md:py-8">
              <div className="max-w-4xl lg:max-w-5xl mx-auto w-full space-y-6">
                {messages.map((msg) => (
                  <div
                    key={msg.id}
                    className={`flex gap-3.5 ${msg.role === 'user' ? 'justify-end' : 'justify-start'
                      }`}
                  >
                    {/* Ask AI Logo Avatar for Assistant */}
                    {msg.role === 'assistant' && (
                      <div className="flex-shrink-0 w-8 h-8 rounded-xl bg-purple-600/20 border border-purple-500/20 p-1.5 flex items-center justify-center shadow-md">
                        <img
                          src={logoImg}
                          alt="Ask AI"
                          className="w-full h-full object-contain"
                        />
                      </div>
                    )}

                    <div
                      className={`max-w-[85%] md:max-w-[80%] rounded-2xl px-5 py-4 shadow-md ${
                        msg.role === 'user'
                          ? 'bg-[#231d3d] border border-purple-500/25 text-purple-100 rounded-tr-sm'
                          : msg.isError
                          ? 'bg-red-500/10 border border-red-500/30 text-red-200 rounded-tl-sm'
                          : 'bg-[#151726]/90 border border-white/10 text-gray-100 rounded-tl-sm'
                      }`}
                    >
                      {/* Markdown Formatted Message */}
                      <div className="prose-chat text-sm md:text-base leading-relaxed break-words">
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>
                          {msg.content}
                        </ReactMarkdown>
                      </div>

                      <p className="text-[10px] text-[#80868b] mt-2 text-right">
                        {new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </p>
                    </div>
                  </div>
                ))}

                {/* Reasoning / Thinking Indicator */}
                {isLoading && (
                  <div className="flex items-center gap-2.5 text-sm text-purple-300 bg-[#151726]/80 px-4 py-2.5 rounded-2xl w-fit border border-purple-500/20 shadow-md">
                    <Sparkles className="w-4 h-4 text-purple-400 animate-spin" />
                    <span>Ask AI is reasoning across your documents...</span>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>
            </div>

            {/* Bottom Input Area - Full width with centered input pill */}
            <div className="w-full px-4 md:px-12 lg:px-24 pb-6 pt-2 bg-gradient-to-t from-[#0d0f18] via-[#0d0f18]/90 to-transparent flex-shrink-0">
              <div className="max-w-4xl lg:max-w-5xl mx-auto w-full">
                <ChatInput
                  onSend={handleSendMessage}
                  onFileUpload={handleFileUpload}
                  disabled={isLoading}
                />
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <ChatApp />
    </AuthProvider>
  );
}
