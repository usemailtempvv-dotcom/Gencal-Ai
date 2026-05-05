import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';

export default function Login() {
  const { login, loginWithGoogle, loading } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState(null);
  const [isDark, setIsDark] = useState(true);

  const ADMIN_EMAIL = 'umerazizgujjar009@gmail.com';
  

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    if (!email || !password) {
      setError('Please fill in all fields');
      return;
    }
    const result = await login(email, password);
    if (!result.success) {
      setError(result.error);
    } else {
      // If admin email, navigate to admin dashboard
      if (String(email || '').toLowerCase().trim() === ADMIN_EMAIL) {
        window.location.href = '/admin/dashboard';
      } else {
        window.location.href = '/dashboard';
      }
    }
  };

  const handleGoogleLogin = async () => {
    setError(null);
    const result = await loginWithGoogle();
    if (!result.success) {
      setError(result.error);
    }
  };

  // Admin account creation helper removed from client for security

  return (
    <div className={`min-h-screen flex flex-col ${isDark ? 'bg-gradient-to-br from-slate-950 via-purple-950 to-slate-950 text-white' : 'bg-white text-slate-900'}`}>
      {/* Header */}
      <header className="bg-black/40 backdrop-blur-xl border-b border-purple-500/20 fixed top-0 w-full z-50 shadow-lg">
        <nav className="flex justify-between items-center px-8 h-20 max-w-7xl mx-auto w-full">
          <div className="flex items-center gap-3">
                <button
                  onClick={() => setIsDark((s) => !s)}
                  className="px-3 py-2 rounded-full bg-slate-800/30 text-sm text-slate-200 hover:bg-slate-800/50 transition-colors"
                >
                  {isDark ? 'Dark' : 'Light'}
                </button>
            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-purple-500 to-blue-600 flex items-center justify-center">
              <span className="text-white font-bold">G</span>
            </div>
            <span className="font-['Space_Grotesk'] text-xl font-black">GenCal AI</span>
          </div>
          <div className="flex items-center gap-4">
            <a href="/signup" className="px-5 py-2 rounded-lg border border-purple-500/30 text-purple-200 hover:bg-purple-500/10 transition-colors font-medium">
              Sign Up
            </a>
          </div>
        </nav>
      </header>

      {/* Main Content */}
      <main className="flex-grow flex pt-20">
        {/* Left Side: Form Section */}
        <section className="w-full lg:w-1/2 flex items-center justify-center p-6 lg:p-16">
          <div className="w-full max-w-md">
            {/* Form Card */}
            <div className="bg-gradient-to-b from-slate-900/80 to-purple-950/60 backdrop-blur-xl border border-purple-500/30 rounded-2xl p-10 shadow-2xl">
              <div className="mb-12">
                <h1 className="text-4xl font-['Space_Grotesk'] font-bold text-white mb-4">Welcome Back</h1>
                <p className="text-lg text-gray-300">Sign in to your GenCal AI account</p>
              </div>

              {error && (
                <div className="p-4 bg-red-500/20 border border-red-500/50 rounded-lg mb-8">
                  <p className="text-red-200 font-medium">{error}</p>
                </div>
              )}

              <form onSubmit={handleSubmit} className="space-y-8">
                <div>
                  <label className="block text-sm font-semibold text-gray-200 mb-3 uppercase tracking-wide">Email Address</label>
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="you@company.com"
                    className="w-full bg-slate-800/50 border border-purple-500/20 rounded-xl px-5 py-4 text-white placeholder:text-gray-500 focus:outline-none focus:border-purple-500 focus:ring-2 focus:ring-purple-500/30 transition-all text-base"
                  />
                </div>

                <div>
                  <div className="flex justify-between items-center mb-3">
                    <label className="block text-sm font-semibold text-gray-200 uppercase tracking-wide">Password</label>
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="text-xs text-purple-300 hover:text-purple-200 transition-colors flex items-center gap-1 font-medium"
                    >
                      <span className="material-symbols-outlined text-base">
                        {showPassword ? 'visibility_off' : 'visibility'}
                      </span>
                      {showPassword ? 'Hide' : 'Show'}
                    </button>
                  </div>
                  <input
                    type={showPassword ? 'text' : 'password'}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••"
                    className="w-full bg-slate-800/50 border border-purple-500/20 rounded-xl px-5 py-4 text-white placeholder:text-gray-500 focus:outline-none focus:border-purple-500 focus:ring-2 focus:ring-purple-500/30 transition-all text-base"
                  />
                </div>

                <div className="flex justify-end">
                  <a href="/" className="text-purple-300 hover:text-purple-200 transition-colors text-sm font-medium">
                    Forgot Password?
                  </a>
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full py-5 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-500 hover:to-blue-500 text-white font-bold rounded-xl shadow-lg hover:shadow-purple-500/50 transition-all duration-300 active:scale-95 disabled:opacity-50 flex justify-center items-center gap-2 text-lg"
                >
                  {loading ? 'Signing In...' : 'Sign In'}
                  <span className="material-symbols-outlined">arrow_forward</span>
                </button>
              </form>

              {/* Divider */}
              <div className="relative my-10">
                <div className="absolute inset-0 flex items-center">
                  <div className="w-full border-t border-purple-500/20"></div>
                </div>
                <div className="relative flex justify-center">
                  <span className="px-4 bg-gradient-to-b from-slate-900/80 to-purple-950/60 text-gray-400 text-sm font-medium uppercase tracking-wide">or</span>
                </div>
              </div>

              {/* Google Button */}
              <button
                onClick={handleGoogleLogin}
                disabled={loading}
                className="w-full py-4 bg-slate-800/50 border border-purple-500/20 text-white rounded-xl hover:bg-slate-700/50 transition-colors flex items-center justify-center gap-3 active:scale-95 disabled:opacity-50 font-medium text-base"
              >
                <svg className="w-6 h-6" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
                  <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
                  <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
                  <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
                </svg>
                Continue with Google
              </button>

              {/* Signup Link */}
              <p className="text-center text-gray-300 text-base mt-10">
                Don't have an account?{' '}
                <a href="/signup" className="text-purple-300 font-semibold hover:text-purple-200 transition-colors">
                  Create one
                </a>
              </p>
            </div>
          </div>
        </section>

        {/* Right Side: Visual Section */}
        <section className="hidden lg:flex w-1/2 relative overflow-hidden bg-gradient-to-br from-purple-900/30 via-slate-900 to-blue-900/30 items-center justify-center p-16">
          {/* Background Gradient Mesh */}
          <div className="absolute inset-0 z-0">
            <div className="absolute top-1/4 -right-40 w-96 h-96 bg-purple-600/20 blur-[120px] rounded-full"></div>
            <div className="absolute bottom-1/3 -left-32 w-80 h-80 bg-blue-600/20 blur-[100px] rounded-full"></div>
          </div>

          {/* Content */}
          <div className="relative z-10 max-w-lg">
            <div className="space-y-12">
              {/* Headline */}
              <div className="space-y-6">
                <div className="flex items-center gap-3">
                  <div className="h-1 w-12 bg-gradient-to-r from-purple-500 to-blue-500"></div>
                  <span className="text-purple-300 text-sm font-bold uppercase tracking-widest">Smart Campus Management</span>
                </div>
                <h2 className="text-5xl font-['Space_Grotesk'] font-bold text-white leading-tight">
                  Automate Your<br />Campus with AI
                </h2>
              </div>

              {/* Features */}
              <div className="space-y-6">
                <div className="flex items-start gap-4">
                  <div className="w-12 h-12 rounded-lg bg-purple-500/20 border border-purple-500/40 flex items-center justify-center flex-shrink-0 mt-1">
                    <span className="material-symbols-outlined text-purple-400 text-xl">check_circle</span>
                  </div>
                  <div>
                    <h3 className="text-xl font-bold text-white mb-2">Smart Scheduling</h3>
                    <p className="text-gray-300 leading-relaxed">AI-powered calendar management that learns your preferences and optimizes your time.</p>
                  </div>
                </div>

                <div className="flex items-start gap-4">
                  <div className="w-12 h-12 rounded-lg bg-blue-500/20 border border-blue-500/40 flex items-center justify-center flex-shrink-0 mt-1">
                    <span className="material-symbols-outlined text-blue-400 text-xl">bolt</span>
                  </div>
                  <div>
                    <h3 className="text-xl font-bold text-white mb-2">Instant Automation</h3>
                    <p className="text-gray-300 leading-relaxed">Automate repetitive tasks and free up time for what truly matters.</p>
                  </div>
                </div>

                <div className="flex items-start gap-4">
                  <div className="w-12 h-12 rounded-lg bg-cyan-500/20 border border-cyan-500/40 flex items-center justify-center flex-shrink-0 mt-1">
                    <span className="material-symbols-outlined text-cyan-400 text-xl">auto_awesome</span>
                  </div>
                  <div>
                    <h3 className="text-xl font-bold text-white mb-2">Intelligent Insights</h3>
                    <p className="text-gray-300 leading-relaxed">Get actionable insights to make better decisions about your schedule.</p>
                  </div>
                </div>
              </div>

              {/* Stats */}
              <div className="grid grid-cols-3 gap-4 pt-8 border-t border-purple-500/20">
                <div>
                  <div className="text-3xl font-bold text-purple-400">10K+</div>
                  <div className="text-gray-400 text-sm mt-1">Active Users</div>
                </div>
                <div>
                  <div className="text-3xl font-bold text-blue-400">99%</div>
                  <div className="text-gray-400 text-sm mt-1">Uptime</div>
                </div>
                <div>
                  <div className="text-3xl font-bold text-cyan-400">24/7</div>
                  <div className="text-gray-400 text-sm mt-1">Support</div>
                </div>
              </div>
            </div>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="bg-black/40 border-t border-purple-500/20 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-8 py-8 flex flex-col md:flex-row justify-between items-center gap-6">
          <div className="flex items-center gap-3">
            <span className="font-['Space_Grotesk'] font-bold text-white">GenCal AI</span>
            <span className="text-gray-500">|</span>
            <span className="text-gray-400 text-sm">© 2024 All rights reserved</span>
          </div>
          <div className="flex gap-8">
            <a href="/" className="text-gray-400 hover:text-white transition-colors text-sm">Privacy</a>
            <a href="/" className="text-gray-400 hover:text-white transition-colors text-sm">Terms</a>
            <a href="/" className="text-gray-400 hover:text-white transition-colors text-sm">Security</a>
          </div>
        </div>
      </footer>
    </div>
  );
}
