'use client';

import { useState } from 'react';
import { apiClient } from '../../lib/api/client';

/** Ordinary email/password access does not establish staff identity or TOTP. */
export function StaffAccessSetup() {
  const [email, setEmail] = useState('');
  const [code, setCode] = useState('');
  const [mode, setMode] = useState('password');
  const [sent, setSent] = useState(false);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  async function submit(event: React.FormEvent) {
    event.preventDefault(); if (busy) return;
    setBusy(true); setError(''); setMessage('');
    try {
      if (mode === 'password') {
        await apiClient('/api/v1/auth/users/reset_password/', { method: 'POST', anonymous: true, body: { email: email.trim() } });
        setMessage('إذا كان الحساب موجودًا ومتاحًا فستصلك تعليمات تعيين كلمة المرور. أكملها من البريد ثم سجّل الدخول هنا.');
      } else if (!sent) {
        await apiClient('/api/v1/auth/resend-otp/', { method: 'POST', anonymous: true, body: { email: email.trim() } });
        setSent(true); setMessage('قُبل طلب إرسال رمز إثبات البريد. أدخل الرمز الذي يصلك.');
      } else {
        await apiClient('/api/v1/auth/verify-email/', { method: 'POST', anonymous: true, body: { email: email.trim(), otp: code } });
        setCode(''); setSent(false); setMessage('تم إثبات البريد. تابع تعيين كلمة المرور عند الحاجة ثم سجّل الدخول. توثيق هوية الموظف وعامل التحقق خطوتان مستقلتان.');
      }
    } catch (failure) { setError(failure instanceof Error ? failure.message : 'تعذّر تأكيد الطلب. راجع الاتصال وحاول مجددًا.'); }
    finally { setBusy(false); }
  }
  return <details className="space-y-3 border-t pt-4"><summary>تجهيز الدخول لأول مرة أو استعادة كلمة المرور</summary>
    <p>بعد تسجيل حساب الموظف بواسطة مالك النظام، يتولى الموظف إثبات بريده وتعيين كلمة مروره. بعد الدخول، افتح أمان الحساب لإكمال الربط الأول بعد المراجعة المستقلة للهوية.</p>
    <form onSubmit={submit} className="space-y-3">
      <label className="block">الخطوة<select className="block w-full rounded border p-2" value={mode} disabled={busy} onChange={e => { setMode(e.target.value); setSent(false); setCode(''); setMessage(''); setError(''); }}><option value="email">إثبات البريد الإلكتروني</option><option value="password">تعيين أو استعادة كلمة المرور</option></select></label>
      <label className="block">البريد الإلكتروني<input dir="ltr" type="email" required autoComplete="username" className="block w-full rounded border p-2" value={email} disabled={busy} onChange={e => { setEmail(e.target.value); setSent(false); setCode(''); }} /></label>
      {mode === 'email' && sent && <label className="block">رمز إثبات البريد<input dir="ltr" required inputMode="numeric" autoComplete="one-time-code" minLength={6} maxLength={6} value={code} className="block w-full rounded border p-2" onChange={e => setCode(e.target.value)} /></label>}
      {error && <p role="alert">{error}</p>}{message && <p role="status">{message}</p>}
      <button disabled={busy} className="min-h-12 rounded border px-4 py-2">{busy ? 'جارٍ التحقق…' : mode === 'password' ? 'طلب رابط تعيين كلمة المرور' : sent ? 'تأكيد البريد' : 'طلب رمز إثبات البريد'}</button>
      {sent && <button type="button" disabled={busy} className="min-h-12 px-3 underline" onClick={() => { setSent(false); setCode(''); }}>العودة لطلب رمز جديد</button>}
    </form>
  </details>;
}
