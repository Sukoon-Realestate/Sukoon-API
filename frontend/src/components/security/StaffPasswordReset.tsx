'use client';

import { useState } from 'react';
import { apiClient, ApiError } from '../../lib/api/client';
import { isBackendEnabled } from '../../lib/api/config';
import { BASE_PATH } from '../../lib/basePath';

export default function StaffPasswordReset({ uid, token }: { uid: string; token: string }) {
  const [password, setPassword] = useState('');
  const [confirmation, setConfirmation] = useState('');
  const [busy, setBusy] = useState(false);
  const [complete, setComplete] = useState(false);
  const [error, setError] = useState('');
  const [unknown, setUnknown] = useState(false);
  async function submit(event: React.FormEvent) {
    event.preventDefault();
    if (busy || complete || !isBackendEnabled()) return;
    if (password !== confirmation) { setError('كلمتا المرور غير متطابقتين.'); return; }
    setBusy(true); setError(''); setUnknown(false);
    try {
      await apiClient('/api/v1/auth/users/reset_password_confirm/', {
        method: 'POST', anonymous: true,
        body: { uid, token, new_password: password, re_new_password: confirmation },
      });
      setPassword(''); setConfirmation(''); setComplete(true);
      // The reset revokes server sessions; discard the local administrative copy.
      for (const key of ['sukoon_access_token', 'sukoon_admin_auth', 'sukoon_user', 'sukoon_admin_mode']) localStorage.removeItem(key);
      window.dispatchEvent(new Event('auth:unauthorized'));
      window.history.replaceState(null, '', `${BASE_PATH}/password-reset/completed/receipt`);
    } catch (failure) {
      setUnknown(!(failure instanceof ApiError) || failure.status >= 500);
      setError(failure instanceof Error ? failure.message : 'تعذّر تأكيد تغيير كلمة المرور.');
    } finally { setBusy(false); }
  }
  return <main dir="rtl" className="m-auto w-full max-w-lg space-y-4 p-6">
    <h1 className="text-2xl font-semibold">تعيين كلمة مرور حساب الموظف</h1>
    {!isBackendEnabled() ? <p role="alert">ربط الخادم غير مفعّل في هذه النسخة. لا يمكن تأكيد تغيير كلمة المرور.</p>
      : complete ? <p role="status">تم تعيين كلمة المرور وإبطال الجلسات السابقة. سجّل الدخول لإكمال توثيق الهوية وربط عامل التحقق إن لزم.</p>
      : <form onSubmit={submit} className="space-y-4">
        <p>هذا الرابط يغيّر كلمة المرور فقط. مراجعة هوية الموظف وربط TOTP واستعادته تبقى إجراءات مستقلة.</p>
        <label className="block">كلمة المرور الجديدة<input type="password" dir="ltr" required autoComplete="new-password" disabled={busy} value={password} onChange={e => setPassword(e.target.value)} className="block w-full rounded border p-3" /></label>
        <label className="block">تأكيد كلمة المرور<input type="password" dir="ltr" required autoComplete="new-password" disabled={busy} value={confirmation} onChange={e => setConfirmation(e.target.value)} className="block w-full rounded border p-3" /></label>
        {error && <p role="alert">{error}</p>}
        {unknown && <p>قد يكون التغيير حُفظ قبل انقطاع الاتصال. جرّب الدخول بكلمة المرور التي اخترتها؛ إذا تعذّر ذلك اطلب رابطًا جديدًا من شاشة الدخول.</p>}
        <button disabled={busy} className="min-h-12 rounded border px-4 py-2">{busy ? 'جارٍ الحفظ…' : 'حفظ كلمة المرور'}</button>
        <p>إذا انتهى الرابط أو استُخدم، اطلب رابطًا جديدًا من شاشة الدخول.</p>
      </form>}
    <a className="inline-block min-h-12 py-3 underline" href={`${BASE_PATH}/login`}>العودة لتسجيل الدخول</a>
  </main>;
}
