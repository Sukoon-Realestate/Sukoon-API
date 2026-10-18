'use client';

import { useState, type FormEvent } from 'react';
import Image from 'next/image';
import PublicLink from 'next/link';
import { Mail, LockKeyhole, Eye, EyeOff, ArrowLeft, Building2, ShieldCheck, ChartNoAxesCombined, ArrowUpLeft } from 'lucide-react';
import { useAuth } from '@/context/AuthContext';
import { ThemeToggle } from '@/components/ui/ThemeToggle';
import { isBackendEnabled } from '@/lib/api/config';
import logo from '@/assets/brand/logo.png';

export default function AdminLoginPage() {
  const { login, loginDemo } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  async function signIn(address: string, secret: string) {
    setError('');
    setSubmitting(true);
    try {
      const success = await login(address, secret);
      if (!success) setError('Login was not confirmed. Check credentials and administrative access.');
    } catch {
      setError('Login was not confirmed. Check the server connection.');
    } finally {
      setSubmitting(false);
    }
  }
  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!email.trim() || !password) { setError('أدخل البريد الإلكتروني وكلمة المرور للمتابعة.'); return; }
    void signIn(email, password);
  }

  return <div className="admin-login">
    <aside className="admin-login-story" aria-label="مساحة إدارة سكون">
      <PublicLink href="/ar" className="flex items-center gap-3 w-fit"><Image src={logo} alt="" width={42} height={42} priority /><strong className="text-2xl font-medium">سكون</strong></PublicLink>
      <div><h2>مساحة واحدة لإدارة كل التفاصيل.</h2><p>تابع أداء المنصة، وراجع الطلبات، وامنح الملاك والمستأجرين تجربة أفضل.</p><ul><li><Building2 size={20} strokeWidth={1.5} />إدارة العقارات والمراجعات</li><li><ShieldCheck size={20} strokeWidth={1.5} />متابعة المجتمع وتوثيق الهوية</li><li><ChartNoAxesCombined size={20} strokeWidth={1.5} />قراءة النمو وأداء الأعمال</li></ul></div>
      <PublicLink href="/ar" className="inline-flex items-center gap-2 text-sm text-[#c3d5bc] w-fit">زيارة موقع سكون<ArrowUpLeft size={16} /></PublicLink>
    </aside>
    <main className="admin-login-main"><div className="admin-login-form">
      <div className="mb-10 flex items-center justify-between"><span className="flex items-center gap-2 text-sm text-[var(--text-muted)]"><Image src={logo} alt="سكون" width={28} height={28} />لوحة الإدارة</span><ThemeToggle /></div>
      <h1>أهلاً بعودتك</h1><p className="mt-2 mb-8 text-sm leading-7 text-[var(--text-muted)]">سجّل الدخول لمتابعة العمل على منصة سكون.</p>
      {error && <div id="login-error" role="alert" className="admin-error mb-5">{error}</div>}
      <form onSubmit={handleSubmit} className="space-y-5">
        <div><label htmlFor="admin-email">البريد الإلكتروني</label><div className="relative"><Mail size={17} className="absolute right-3 top-4 text-[var(--text-muted)]" aria-hidden /><input id="admin-email" type="email" autoComplete="username" required value={email} onChange={(event) => setEmail(event.target.value)} placeholder="name@sukoon.com" className="admin-login-input" dir="ltr" aria-describedby={error ? 'login-error' : undefined} /></div></div>
        <div><label htmlFor="admin-password">كلمة المرور</label><div className="relative"><LockKeyhole size={17} className="absolute right-3 top-4 text-[var(--text-muted)]" aria-hidden /><input id="admin-password" type={showPassword ? 'text' : 'password'} autoComplete="current-password" required value={password} onChange={(event) => setPassword(event.target.value)} className="admin-login-input !pl-11" dir="ltr" aria-describedby={error ? 'login-error' : undefined} /><button type="button" className="admin-icon-button absolute left-1 top-1" onClick={() => setShowPassword((value) => !value)} aria-label={showPassword ? 'إخفاء كلمة المرور' : 'إظهار كلمة المرور'} aria-pressed={showPassword}>{showPassword ? <EyeOff size={17} /> : <Eye size={17} />}</button></div></div>
        <p className="text-xs leading-6 text-[var(--text-muted)]">إذا نسيت كلمة المرور، تواصل مع مسؤول المنصة لاستعادة الوصول.</p>
        <button type="submit" disabled={submitting} className="admin-button admin-button-primary w-full !min-h-12">{submitting ? 'جاري تسجيل الدخول…' : 'تسجيل الدخول'}<ArrowLeft size={17} aria-hidden /></button>
      </form>
      {!isBackendEnabled() && <div className="mt-7 border-t border-[var(--divider)] pt-5"><p className="text-xs text-[var(--text-muted)] mb-3">تستعرض نسخة تجريبية ببيانات توضيحية.</p><button type="button" disabled={submitting} onClick={loginDemo} className="admin-button admin-button-secondary w-full">استكشاف لوحة الإدارة التجريبية<ArrowLeft size={15} aria-hidden /></button></div>}
    </div></main>
  </div>;
}
