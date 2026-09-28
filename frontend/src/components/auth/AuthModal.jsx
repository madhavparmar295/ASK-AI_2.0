import { useState } from 'react';
import { X, Lock, Mail, User, KeyRound, Loader2, ArrowRight, CheckCircle2 } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

export default function AuthModal() {
  const {
    isAuthModalOpen,
    closeAuthModal,
    authModalTab,
    setAuthModalTab,
    pendingEmail,
    login,
    register,
    verifyOtp,
  } = useAuth();

  // Form states
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [otpCode, setOtpCode] = useState('');

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [successMsg, setSuccessMsg] = useState('');

  if (!isAuthModalOpen) return null;

  const handleLoginSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await login(email, password);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleRegisterSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await register(name, email, password);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleOtpSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await verifyOtp(pendingEmail || email, otpCode);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-md animate-fadeIn">
      {/* Modal Card */}
      <div className="relative w-full max-w-md p-6 overflow-hidden rounded-2xl glass-strong border border-white/10 shadow-2xl bg-[#0f0c1b]/90 text-white">

        {/* Glow orb */}
        <div className="absolute -top-20 -right-20 w-48 h-48 bg-purple-600/30 rounded-full blur-3xl pointer-events-none"></div>
        <div className="absolute -bottom-20 -left-20 w-48 h-48 bg-blue-600/20 rounded-full blur-3xl pointer-events-none"></div>

        {/* Close Button */}
        <button
          onClick={closeAuthModal}
          className="absolute top-4 right-4 p-1.5 rounded-lg text-gray-400 hover:text-white hover:bg-white/10 transition-colors"
          aria-label="Close"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Header */}
        <div className="text-center mb-6">
          <h2 className="text-2xl font-bold text-white tracking-wide">
            {authModalTab === 'otp' ? 'Verify Your Account' : authModalTab === 'login' ? 'Welcome Back' : 'Create an Account'}
          </h2>
          <p className="text-sm text-gray-400 mt-1">
            {authModalTab === 'otp'
              ? `Enter the code sent to ${pendingEmail || email}`
              : authModalTab === 'login'
                ? 'Sign in to access your indexed emails & documents'
                : 'Sign up to start intelligent Q&A with Ask AI'}
          </p>
        </div>

        {/* Tabs for Login / Register */}
        {authModalTab !== 'otp' && (
          <div className="flex p-1 mb-6 rounded-xl bg-white/5 border border-white/10">
            <button
              onClick={() => { setAuthModalTab('login'); setError(''); }}
              className={`flex-1 py-2 text-sm font-medium rounded-lg transition-all ${authModalTab === 'login'
                  ? 'bg-purple-600 text-white shadow-md'
                  : 'text-gray-400 hover:text-white'
                }`}
            >
              Sign In
            </button>
            <button
              onClick={() => { setAuthModalTab('register'); setError(''); }}
              className={`flex-1 py-2 text-sm font-medium rounded-lg transition-all ${authModalTab === 'register'
                  ? 'bg-purple-600 text-white shadow-md'
                  : 'text-gray-400 hover:text-white'
                }`}
            >
              Create Account
            </button>
          </div>
        )}

        {/* Error Message */}
        {error && (
          <div className="p-3 mb-4 text-xs text-red-300 rounded-lg bg-red-500/10 border border-red-500/20">
            {error}
          </div>
        )}

        {/* Success Message */}
        {successMsg && (
          <div className="p-3 mb-4 text-xs text-green-300 rounded-lg bg-green-500/10 border border-green-500/20 flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-green-400 flex-shrink-0" />
            <span>{successMsg}</span>
          </div>
        )}

        {/* Login Form */}
        {authModalTab === 'login' && (
          <form onSubmit={handleLoginSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-gray-300 mb-1.5">Email Address</label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="name@example.com"
                  className="w-full pl-9 pr-3 py-2.5 rounded-xl bg-white/5 border border-white/10 text-sm text-white placeholder-gray-500 outline-none focus:border-purple-500 transition-colors"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-gray-300 mb-1.5">Password</label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full pl-9 pr-3 py-2.5 rounded-xl bg-white/5 border border-white/10 text-sm text-white placeholder-gray-500 outline-none focus:border-purple-500 transition-colors"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 px-4 rounded-xl bg-purple-600 hover:bg-purple-500 active:scale-95 disabled:opacity-50 text-sm font-semibold text-white shadow-lg shadow-purple-600/30 flex items-center justify-center gap-2 transition-all mt-6"
            >
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Sign In'}
            </button>
          </form>
        )}

        {/* Register Form */}
        {authModalTab === 'register' && (
          <form onSubmit={handleRegisterSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-gray-300 mb-1.5">Your Name</label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input
                  type="text"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Parth Suryawanshi"
                  className="w-full pl-9 pr-3 py-2.5 rounded-xl bg-white/5 border border-white/10 text-sm text-white placeholder-gray-500 outline-none focus:border-purple-500 transition-colors"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-gray-300 mb-1.5">Email Address</label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="name@example.com"
                  className="w-full pl-9 pr-3 py-2.5 rounded-xl bg-white/5 border border-white/10 text-sm text-white placeholder-gray-500 outline-none focus:border-purple-500 transition-colors"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-gray-300 mb-1.5">Password</label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full pl-9 pr-3 py-2.5 rounded-xl bg-white/5 border border-white/10 text-sm text-white placeholder-gray-500 outline-none focus:border-purple-500 transition-colors"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 px-4 rounded-xl bg-purple-600 hover:bg-purple-500 active:scale-95 disabled:opacity-50 text-sm font-semibold text-white shadow-lg shadow-purple-600/30 flex items-center justify-center gap-2 transition-all mt-6"
            >
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Continue to Verification'}
            </button>
          </form>
        )}

        {/* OTP Form */}
        {authModalTab === 'otp' && (
          <form onSubmit={handleOtpSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-gray-300 mb-1.5">6-Digit Verification Code</label>
              <div className="relative">
                <KeyRound className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input
                  type="text"
                  maxLength={6}
                  required
                  value={otpCode}
                  onChange={(e) => setOtpCode(e.target.value)}
                  placeholder="123456"
                  className="w-full pl-9 pr-3 py-3 tracking-widest text-center text-lg font-mono rounded-xl bg-white/5 border border-white/10 text-white placeholder-gray-600 outline-none focus:border-purple-500 transition-colors"
                />
              </div>
              <p className="text-[11px] text-gray-400 mt-2.5 text-center">
                Didn't receive the email? Check your spam folder or verify your address.
              </p>
            </div>

            <button
              type="submit"
              disabled={loading || otpCode.length < 6}
              className="w-full py-2.5 px-4 rounded-xl bg-purple-600 hover:bg-purple-500 active:scale-95 disabled:opacity-50 text-sm font-semibold text-white shadow-lg shadow-purple-600/30 flex items-center justify-center gap-2 transition-all mt-6"
            >
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Verify & Log In'}
            </button>

            <button
              type="button"
              onClick={() => { setAuthModalTab('login'); setError(''); }}
              className="w-full text-xs text-gray-400 hover:text-white text-center transition-colors"
            >
              ← Back to Sign In
            </button>
          </form>
        )}

      </div>
    </div>
  );
}
