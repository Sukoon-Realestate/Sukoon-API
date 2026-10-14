'use client';

import React, { useState } from 'react';
import Image from 'next/image';
import { useAuth } from '@/context/AuthContext';
import logo from '@/assets/brand/logo.png';
import { Mail, Lock, Eye, EyeOff, LogIn, ArrowLeft } from 'lucide-react';
import { isBackendEnabled } from '@/lib/api/config';

export default function AdminLoginPage() {
  const { login, loginDemo } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(true);
  const [errorMsg, setErrorMsg] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg('');

    if (!email.trim() || !password.trim()) {
      setErrorMsg('يرجى إدخال البريد الإلكتروني وكلمة المرور');
      return;
    }

    setIsSubmitting(true);
    const success = await login(email, password);
    setIsSubmitting(false);

    if (!success) {
      if (email.trim().toLowerCase() === 'admin@sukoon.com') {
        loginDemo();
      } else {
        setErrorMsg('البريد الإلكتروني أو كلمة المرور غير صحيحة');
      }
    }
  };

  const handleQuickDemo = async () => {
    setEmail('admin@sukoon.com');
    setPassword('password123');
    setIsSubmitting(true);
    setErrorMsg('');

    try {
      const ok = await login('admin@sukoon.com', 'password123');
      if (!ok) {
        loginDemo();
      }
    } catch {
      loginDemo();
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen w-full bg-[var(--background)] text-[var(--foreground)] flex items-center justify-center p-4 relative overflow-hidden font-sans dir-rtl">
      {/* Ambient background glow effects */}
      <div className="absolute -top-40 -right-40 w-96 h-96 bg-teal-500/10 rounded-full blur-3xl pointer-events-none animate-pulseGlow"></div>
      <div className="absolute -bottom-40 -left-40 w-96 h-96 bg-teal-500/10 rounded-full blur-3xl pointer-events-none animate-pulseGlow" style={{ animationDelay: '2s' }}></div>
      {/* ? Third subtle glow for depth */}
      <div className="absolute top-1/2 left-1/3 w-64 h-64 bg-teal-400/5 rounded-full blur-3xl pointer-events-none animate-pulseGlow" style={{ animationDelay: '1s' }}></div>

      {/* Main Glassmorphic Login Card */}
      <div className="w-full max-w-md bg-[var(--card-bg)] border border-[var(--card-border)] rounded-3xl p-8 sm:p-10 shadow-[var(--shadow-card)] backdrop-blur-xl relative z-10 space-y-6 animate-scaleIn">
        {/* Brand Header */}
        <div className="text-center space-y-3">
          <Image src={logo} alt="" width={64} height={64} priority className="w-16 h-16 mx-auto animate-breathe" />

          <div>
            <h1 className="text-2xl font-black text-[var(--foreground)] tracking-tight">
              أهلاً بك في سكون
            </h1>
            <p className="text-xs text-[var(--text-muted)] font-medium mt-1">
              تسجيل الدخول إلى لوحة الإدارة المركزية
            </p>
          </div>
        </div>

        {/* Error Alert */}
        {errorMsg && (
          <div className="bg-rose-500/15 border border-rose-500/30 rounded-xl p-3.5 text-xs text-rose-600 dark:text-rose-300 text-center font-bold animate-fadeInUp">
            {errorMsg}
          </div>
        )}

        {/* Login Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Email Input */}
          <div className="space-y-1.5 animate-fadeInUp" style={{ animationDelay: '100ms' }}>
            <label className="text-xs font-bold text-[var(--text-muted)] block">
              البريد الإلكتروني
            </label>
            <div className="relative">
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="admin@sukoon.com"
                className="w-full pl-4 pr-11 py-3 bg-[var(--input-bg)] border border-[var(--input-border)] rounded-xl text-xs text-[var(--foreground)] focus:outline-none focus:ring-2 focus:ring-teal-500/40 focus:border-[#0D7C66] transition-all placeholder:text-slate-500 dir-ltr text-right"
              />
              <Mail className="w-4 h-4 text-[var(--text-muted)] absolute right-3.5 top-3.5" />
            </div>
          </div>

          {/* Password Input */}
          <div className="space-y-1.5 animate-fadeInUp" style={{ animationDelay: '150ms' }}>
            <label className="text-xs font-bold text-[var(--text-muted)] block">
              كلمة المرور
            </label>
            <div className="relative">
              <input
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full pl-11 pr-11 py-3 bg-[var(--input-bg)] border border-[var(--input-border)] rounded-xl text-xs text-[var(--foreground)] focus:outline-none focus:ring-2 focus:ring-teal-500/40 focus:border-[#0D7C66] transition-all placeholder:text-slate-500 dir-ltr text-right"
              />
              <Lock className="w-4 h-4 text-[var(--text-muted)] absolute right-3.5 top-3.5" />

              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute left-3.5 top-3.5 text-[var(--text-muted)] hover:text-slate-200 transition-colors"
              >
                {showPassword ? (
                  <EyeOff className="w-4 h-4" />
                ) : (
                  <Eye className="w-4 h-4" />
                )}
              </button>
            </div>
          </div>

          {/* Remember Me & Forgot Password */}
          <div className="flex items-center justify-between text-xs pt-1 animate-fadeInUp" style={{ animationDelay: '200ms' }}>
            <label className="flex items-center gap-2 text-[var(--text-muted)] cursor-pointer select-none">
              <input
                type="checkbox"
                checked={rememberMe}
                onChange={(e) => setRememberMe(e.target.checked)}
                className="rounded border-slate-700 bg-slate-800 text-teal-600 focus:ring-teal-500/30"
              />
              <span>تذكرني</span>
            </label>

            <a
              href="#forgot"
              onClick={(e) => {
                e.preventDefault();
                alert('يرجى التواصل مع مالك النظام لاستعادة كلمة المرور');
              }}
              className="text-[var(--primary-text)] hover:text-teal-300 font-semibold transition-colors"
            >
              نسيت كلمة المرور؟
            </a>
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full py-3.5 bg-[var(--primary)] hover:bg-[var(--primary-hover)] active:scale-[0.98] text-white font-black text-sm rounded-xl shadow-lg shadow-teal-900/40 transition-all flex items-center justify-center gap-2 disabled:opacity-50 mt-2 animate-fadeInUp"
            style={{ animationDelay: '250ms' }}
          >
            {isSubmitting ? (
              <span>جاري تسجيل الدخول...</span>
            ) : (
              <>
                <LogIn className="w-4 h-4" />
                <span>تسجيل الدخول</span>
              </>
            )}
          </button>
        </form>

        {/* Quick Demo Login Button - only visible when NEXT_PUBLIC_ENABLE_BACKEND is false */}
        {!isBackendEnabled() && (
          <>
            {/* Divider */}
            <div className="relative flex items-center justify-center pt-2">
              <div className="border-t border-[var(--card-border)] w-full"></div>
              <span className="bg-[var(--card-bg)] px-3 text-[11px] text-slate-500 font-bold uppercase shrink-0">
                أو
              </span>
            </div>

            {/* Quick Demo Login Button */}
            <button
              type="button"
              onClick={handleQuickDemo}
              className="w-full py-3 bg-[var(--primary-subtle)] hover:bg-[var(--card-hover)] active:scale-[0.98] text-[var(--primary-text)] font-extrabold text-xs rounded-xl border border-teal-500/20 hover:border-teal-500/40 transition-all flex items-center justify-center gap-2 animate-fadeInUp"
              style={{ animationDelay: '300ms' }}
            >
              <span>دخول سريع كـ Admin (تجريبي)</span>
              <ArrowLeft className="w-3.5 h-3.5" />
            </button>
          </>
        )}
      </div>
    </div>
  );
}
