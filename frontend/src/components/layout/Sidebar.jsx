import { useState } from 'react';
import {
  MessageSquare,
  Search,
  Lightbulb,
  Clock,
  Puzzle,
  Settings,
  User,
  LogOut,
  LogIn,
  CheckCircle,
  Plus,
} from 'lucide-react';
import logoImg from '../../assets/logo.png';
import { useAuth } from '../../context/AuthContext';

export default function Sidebar({ onOpenHistory, onNewChat }) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [activeIcon, setActiveIcon] = useState('chat');
  const [isProfileMenuOpen, setIsProfileMenuOpen] = useState(false);
  const { user, isAuthenticated, openAuthModal, logout } = useAuth();

  const navItems = [
    { id: 'chat', icon: MessageSquare, label: 'New Chat' },
    { id: 'history', icon: Clock, label: 'History' },
    { id: 'search', icon: Search, label: 'Search' },
    { id: 'ideas', icon: Lightbulb, label: 'Ideas' },
    { id: 'plugins', icon: Puzzle, label: 'Plugins' },
    { id: 'settings', icon: Settings, label: 'Settings' },
  ];

  const handleNavClick = (id) => {
    setActiveIcon(id);
    if (id === 'history') {
      onOpenHistory?.();
    } else if (id === 'chat') {
      onNewChat?.();
    }
  };

  const handleProfileClick = () => {
    if (!isAuthenticated) {
      openAuthModal('login');
    } else {
      setIsProfileMenuOpen(!isProfileMenuOpen);
    }
  };

  return (
    <>
      {/* 1. Desktop Sidebar - Matches the midnight navy and purple aura (#0d0f18 / #141624) */}
      <aside
        className="hidden md:flex fixed left-0 top-0 h-full bg-[#0d0f18]/85 backdrop-blur-2xl border-r border-white/5 z-30 transition-all duration-250 ease-out will-change-transform hover:w-44 w-14 flex-col group shadow-2xl"
        style={{ contain: 'layout style paint' }}
        onMouseEnter={() => setIsExpanded(true)}
        onMouseLeave={() => {
          setIsExpanded(false);
          setIsProfileMenuOpen(false);
        }}
      >
        {/* Logo Header */}
        <div className="flex items-center justify-center h-14 border-b border-white/5 transition-all duration-250 group-hover:h-16 flex-shrink-0">
          <div className="relative w-8 h-8 flex items-center justify-center transition-all duration-250 group-hover:w-10 group-hover:h-10">
            <img
              src={logoImg}
              alt="Ask AI Logo"
              className="relative w-7 h-7 object-contain drop-shadow-[0_0_8px_rgba(168,85,247,0.35)]"
            />
          </div>
        </div>

        {/* Navigation Items */}
        <nav className="flex-1 py-3 flex flex-col gap-1 px-2 overflow-y-auto">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeIcon === item.id;

            return (
              <button
                key={item.id}
                onClick={() => handleNavClick(item.id)}
                className={`
                  relative flex items-center gap-3 px-2.5 py-2.5 rounded-xl transition-all duration-200 text-left
                  ${
                    isActive
                      ? 'bg-purple-600/15 text-purple-300 border border-purple-500/30 shadow-[0_0_15px_rgba(168,85,247,0.15)]'
                      : 'text-gray-400 hover:text-purple-200 hover:bg-white/5 border border-transparent'
                  }
                `}
                aria-label={item.label}
              >
                <Icon className="relative w-4 h-4 flex-shrink-0" />

                {/* Label (fade-in on sidebar hover expansion) */}
                <span className="relative whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity duration-250 text-xs font-medium tracking-wide">
                  {item.label}
                </span>

                {/* Active Indicator Pip */}
                {isActive && (
                  <div className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-4 bg-purple-400 rounded-r-full shadow-[0_0_8px_rgba(192,132,252,0.8)]" />
                )}
              </button>
            );
          })}
        </nav>

        {/* Profile Card / Login Button at Bottom */}
        <div className="mt-auto border-t border-white/5 p-2 relative flex-shrink-0">
          {/* Profile Menu Popover */}
          {isAuthenticated && isProfileMenuOpen && (
            <div className="absolute bottom-16 left-2 right-2 p-3 rounded-2xl border border-white/10 shadow-2xl bg-[#141624]/95 backdrop-blur-2xl text-gray-100 z-40 animate-fadeIn text-xs">
              <div className="mb-2 pb-2 border-b border-white/10">
                <p className="font-semibold text-white truncate">{user?.name || 'User'}</p>
                <p className="text-gray-400 truncate text-[11px]">{user?.email}</p>
                <div className="mt-1 flex items-center gap-1 text-[10px] text-green-400 font-medium">
                  <CheckCircle className="w-3 h-3" />
                  <span>Verified Account</span>
                </div>
              </div>
              <button
                onClick={() => {
                  logout();
                  setIsProfileMenuOpen(false);
                }}
                className="w-full flex items-center gap-2 px-2 py-1.5 rounded-lg text-red-400 hover:bg-red-500/10 transition-colors font-medium"
              >
                <LogOut className="w-3.5 h-3.5" />
                <span>Log Out</span>
              </button>
            </div>
          )}

          <button
            onClick={handleProfileClick}
            className="w-full flex items-center gap-2.5 px-1 py-1 rounded-xl hover:bg-white/5 transition-colors text-left"
            title={isAuthenticated ? user?.name : 'Sign In'}
          >
            {/* User Avatar with purple gradient */}
            <div
              className={`relative w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 shadow-sm ${
                isAuthenticated
                  ? 'bg-gradient-to-br from-purple-500 to-indigo-600 text-white'
                  : 'bg-purple-500/15 text-purple-300 border border-purple-500/25'
              }`}
            >
              {isAuthenticated ? (
                <span className="text-xs font-semibold uppercase">
                  {(user?.name || user?.email || 'U')[0]}
                </span>
              ) : (
                <User className="w-4 h-4" />
              )}
            </div>

            {/* User info (hidden when collapsed) */}
            <div className="flex-1 text-left opacity-0 group-hover:opacity-100 transition-opacity duration-250 overflow-hidden">
              <p className="text-xs font-medium text-white truncate">
                {isAuthenticated ? user?.name || 'Account' : 'Sign In'}
              </p>
              <p className="text-[10px] text-gray-400 truncate">
                {isAuthenticated ? user?.email : 'Click to log in'}
              </p>
            </div>

            {!isAuthenticated && (
              <LogIn className="w-3.5 h-3.5 text-gray-400 opacity-0 group-hover:opacity-100 transition-opacity duration-250 flex-shrink-0" />
            )}
          </button>
        </div>
      </aside>

      {/* 2. Mobile Top Navigation Bar: pinned to top of phone screen (md:hidden) */}
      <header className="md:hidden fixed top-0 left-0 right-0 h-14 bg-[#0d0f18]/95 backdrop-blur-xl border-b border-white/5 flex items-center justify-between px-3 z-40">
        {/* Brand & Logo */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => onNewChat?.()}
            className="flex items-center gap-2 p-1 rounded-lg active:scale-95 transition-transform"
          >
            <img src={logoImg} alt="Ask AI" className="w-7 h-7 object-contain drop-shadow-[0_0_6px_rgba(168,85,247,0.4)]" />
            <span className="text-sm font-semibold text-white tracking-wide">Ask AI</span>
          </button>
        </div>

        {/* Mobile Action Controls */}
        <div className="flex items-center gap-1.5">
          {/* New Chat Button */}
          <button
            onClick={() => onNewChat?.()}
            className="p-1.5 rounded-lg text-purple-300 hover:text-white bg-purple-600/15 border border-purple-500/30 flex items-center gap-1 active:scale-95 transition-all text-xs"
            title="Start New Chat"
          >
            <Plus className="w-4 h-4 text-purple-400" />
            <span className="text-[11px] font-medium hidden xs:inline">New</span>
          </button>

          {/* History Drawer Trigger */}
          <button
            onClick={() => onOpenHistory?.()}
            className="p-1.5 rounded-lg text-gray-300 hover:text-white bg-white/5 border border-white/10 active:scale-95 transition-all"
            title="Chat History"
          >
            <Clock className="w-4 h-4 text-purple-400" />
          </button>

          {/* User Profile / Login */}
          <div className="relative">
            <button
              onClick={handleProfileClick}
              className="w-7 h-7 rounded-full bg-gradient-to-br from-purple-500 to-indigo-600 text-white flex items-center justify-center active:scale-95 transition-all shadow-sm"
              title={isAuthenticated ? user?.name : 'Sign In'}
            >
              {isAuthenticated ? (
                <span className="text-[11px] font-semibold uppercase">
                  {(user?.name || user?.email || 'U')[0]}
                </span>
              ) : (
                <User className="w-3.5 h-3.5 text-white" />
              )}
            </button>

            {/* Mobile Profile Dropdown Popover */}
            {isAuthenticated && isProfileMenuOpen && (
              <>
                <div
                  className="fixed inset-0 z-40 bg-black/20"
                  onClick={() => setIsProfileMenuOpen(false)}
                />
                <div className="absolute top-9 right-0 w-60 p-3 rounded-2xl border border-white/10 shadow-2xl bg-[#141624]/95 backdrop-blur-2xl text-gray-100 z-50 animate-fadeIn text-xs">
                  <div className="mb-2 pb-2 border-b border-white/10">
                    <p className="font-semibold text-white truncate">{user?.name || 'User'}</p>
                    <p className="text-gray-400 truncate text-[11px]">{user?.email}</p>
                    <div className="mt-1 flex items-center gap-1 text-[10px] text-green-400 font-medium">
                      <CheckCircle className="w-3 h-3" />
                      <span>Verified Account</span>
                    </div>
                  </div>
                  <button
                    onClick={() => {
                      logout();
                      setIsProfileMenuOpen(false);
                    }}
                    className="w-full flex items-center gap-2 px-2 py-1.5 rounded-lg text-red-400 hover:bg-red-500/10 transition-colors font-medium"
                  >
                    <LogOut className="w-3.5 h-3.5" />
                    <span>Log Out</span>
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      </header>
    </>
  );
}
