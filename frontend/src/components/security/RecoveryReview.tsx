'use client';

import { useState } from 'react';
import { beginReview, verifyReview, decideRecovery, RecoveryRequest, RecoveryDecision, Challenge } from '../../lib/api/security';

export function RecoveryReview({ item, onSaved }: { item: RecoveryRequest; onSaved: () => Promise<void> }) {
  const [body, setBody] = useState<RecoveryDecision>({ expected_revision: item.revision, decision: item.status === 'approved' ? 'renew_enrollment' : 'approve', reason: '', verification_method: 'known_channel_video', verification_reference: '', identity_matched: false });
  const [challenge, setChallenge] = useState<Challenge | null>(null);
  const [code, setCode] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const change = (update: Partial<RecoveryDecision>) => { setBody(current => ({ ...current, ...update })); setChallenge(null); setCode(''); };
  async function submit(event: React.FormEvent) {
    event.preventDefault(); if (busy) return; setBusy(true); setError('');
    try {
      if (!challenge) {
        setChallenge(await beginReview(item, body));
      } else {
        if (Date.parse(challenge.expires_at) <= Date.now()) throw new Error('انتهى إذن التحقق. راجع البيانات واطلب رمزًا جديدًا.');
        const authorization = await verifyReview(challenge.id, code);
        setCode('');
        await decideRecovery(item.id, body, authorization.proof);
        setChallenge(null);
        await onSaved();
      }
    } catch (failure) {
      setError(failure instanceof Error ? failure.message : 'تعذّر تأكيد القرار. حدّث الطلب لمعرفة حالته الحالية.');
      setChallenge(null); setCode('');
    } finally { setBusy(false); }
  }
  return <form onSubmit={submit} className="space-y-3 rounded-xl border p-4">
    <h3 className="font-bold">{item.email}</h3>
    <p>{item.reason}</p>
    <p>مرجع الهوية: {item.identity_reference} · القناة المعروفة: {item.known_channel_reference}</p>
    <p>يجب إجراء مقابلة مستقلة ومطابقة سجل الهوية. البريد أو الجلسة المفتوحة لا يكفيان.</p>
    <label className="block">القرار<select className="block w-full border rounded p-2" value={body.decision} disabled={busy} onChange={e => change({ decision: e.target.value as RecoveryDecision['decision'] })}>
      {item.status === 'approved' ? <option value="renew_enrollment">تجديد إذن الربط بعد مراجعة مستقلة</option> : <><option value="approve">اعتماد الاستعادة</option><option value="request_information">طلب معلومات</option><option value="reject">رفض</option></>}
    </select></label>
    <label className="block">السبب<textarea className="block w-full border rounded p-2" required maxLength={1000} value={body.reason} disabled={busy} onChange={e => change({ reason: e.target.value })} /></label>
    <label className="block">وسيلة التحقق<select className="block w-full border rounded p-2" value={body.verification_method} disabled={busy} onChange={e => change({ verification_method: e.target.value as RecoveryDecision['verification_method'] })}><option value="known_channel_video">اتصال مرئي بالقناة المعروفة</option><option value="in_person">مقابلة مباشرة</option></select></label>
    <label className="block">مرجع التحقق الموثّق<input className="block w-full border rounded p-2" required={['approve', 'renew_enrollment'].includes(body.decision)} maxLength={200} value={body.verification_reference} disabled={busy} onChange={e => change({ verification_reference: e.target.value })} /></label>
    <label className="flex gap-2"><input type="checkbox" required={['approve', 'renew_enrollment'].includes(body.decision)} checked={body.identity_matched} disabled={busy} onChange={e => change({ identity_matched: e.target.checked })} />أؤكد مطابقة الهوية بمراجعة مستقلة موثّقة</label>
    {challenge && <label className="block">رمز تطبيق التحقق<input className="block w-full border rounded p-2" autoComplete="one-time-code" inputMode="numeric" maxLength={6} minLength={6} required value={code} onChange={e => setCode(e.target.value)} /></label>}
    {error && <p role="alert">{error}</p>}
    <button disabled={busy} className="border rounded px-4 py-2" type="submit">{busy ? 'جارٍ التحقق…' : challenge ? 'تأكيد القرار' : 'التحقق من القرار'}</button>
  </form>;
}
