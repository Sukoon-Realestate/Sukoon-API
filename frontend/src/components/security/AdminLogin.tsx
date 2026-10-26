'use client';

import { useState, type FormEvent } from 'react';
import Image from 'next/image';
import PublicLink from 'next/link';
import { Eye, EyeOff } from 'lucide-react';
import { useAuth } from '@/context/AuthContext';
import { ThemeToggle } from '@/components/ui/ThemeToggle';
import logo from '@/assets/brand/logo.png';
import { isBackendEnabled } from '../../lib/api/config';
import { StaffAccessSetup } from './StaffAccessSetup';

export default function AdminLogin({ publicSiteHref }: { publicSiteHref?: string }) {
  const { login, loginDemo } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [visible, setVisible] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  async function submit(event: FormEvent) {
    event.preventDefault();
    if (busy) return;
    setBusy(true); setError('');
    try {
      if (!await login(email, password)) setError('لم يتأكد تسجيل الدخول. راجع بيانات الدخول وصلاحية حساب الإدارة ثم أعد المحاولة.');
    } catch { setError('تعذر تأكيد تسجيل الدخول. تحقق من الاتصال ثم أعد المحاولة.'); }
    finally { setBusy(false); }
  }
  return <main dir="rtl" className="flex min-h-dvh w-full items-center justify-center bg-[var(--background)] p-4 text-[var(--foreground)]">
    <div className="w-full max-w-md space-y-6 rounded-2xl border border-[var(--card-border)] bg-[var(--card-bg)] p-5 sm:p-8">
      <div className="flex items-center justify-between gap-3"><span className="flex items-center gap-3"><Image src={logo} alt="سكون" width={36} height={36} />لوحة الإدارة</span><ThemeToggle /></div>
      <h1 className="text-2xl font-bold">أهلًا بعودتك</h1><p>سجّل الدخول لمتابعة العمل على منصة سكون.</p>
      {error && <p id="login-error" role="alert">{error}</p>}
      <form onSubmit={submit} className="space-y-5">
        <label className="block space-y-2" htmlFor="admin-email"><span>البريد الإلكتروني</span>
          <input id="admin-email" className="min-h-12 w-full rounded-lg border border-[var(--input-border)] bg-[var(--input-bg)] px-3" dir="ltr" type="email" autoComplete="username" required disabled={busy} value={email} onChange={event => setEmail(event.target.value)} aria-describedby={error ? 'login-error' : undefined} />
        </label>
        <label className="block space-y-2" htmlFor="admin-password"><span>كلمة المرور</span>
          <span className="flex rounded-lg border border-[var(--input-border)] bg-[var(--input-bg)]">
            <input id="admin-password" className="min-h-12 min-w-0 w-full bg-transparent px-3" dir="ltr" type={visible ? 'text' : 'password'} autoComplete="current-password" required disabled={busy} value={password} onChange={event => setPassword(event.target.value)} aria-describedby={error ? 'login-error' : undefined} />
            <button type="button" className="min-h-12 min-w-12 shrink-0" aria-label={visible ? 'إخفاء كلمة المرور' : 'إظهار كلمة المرور'} aria-pressed={visible} onClick={() => setVisible(value => !value)}>{visible ? <EyeOff className="mx-auto" size={20} /> : <Eye className="mx-auto" size={20} />}</button>
          </span>
        </label>
        <button type="submit" disabled={busy} className="min-h-12 w-full rounded-lg bg-teal-700 px-4 py-3 text-white disabled:opacity-50">{busy ? 'جارٍ تسجيل الدخول…' : 'تسجيل الدخول'}</button>
      </form>
      {isBackendEnabled() && <StaffAccessSetup />}
      {!isBackendEnabled() && <div className="space-y-3 border-t pt-4"><p>نسخة تجريبية ببيانات توضيحية.</p><button type="button" disabled={busy} onClick={loginDemo} className="min-h-12 rounded border px-4 py-3">استكشاف لوحة الإدارة التجريبية</button></div>}
      {publicSiteHref && <PublicLink href={publicSiteHref} className="inline-block min-h-12 py-3 underline">زيارة موقع سكون</PublicLink>}
    </div>
  </main>;
}
