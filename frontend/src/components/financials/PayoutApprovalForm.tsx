'use client';

import { useState } from 'react';
import { beginPayoutApproval, confirmPayoutApproval, money, type PayoutApproval } from '../../lib/api/payouts';
import { verifyReview, type Challenge } from '../../lib/api/security';

export function PayoutApprovalForm({ approval, onSaved, onCancel }: { approval: PayoutApproval; onSaved: (id?: string) => Promise<void>; onCancel: () => void }) {
  const [challenge, setChallenge] = useState<Challenge | null>(null);
  const [code, setCode] = useState('');
  const [busy, setBusy] = useState(false);
  const [uncertain, setUncertain] = useState(false);
  const [error, setError] = useState('');
  async function submit(event: React.FormEvent) {
    event.preventDefault(); if (busy || uncertain) return;
    setBusy(true); setError('');
    let transmitted = false;
    try {
      if (!challenge) { setChallenge(await beginPayoutApproval(approval)); return; }
      if (Date.parse(challenge.expires_at) <= Date.now()) throw new Error('انتهى إذن التحقق. اطلب إذنًا جديدًا لهذه البيانات.');
      const result = await verifyReview(challenge.id, code);
      setCode(''); setChallenge(null); transmitted = true;
      const saved = await confirmPayoutApproval(approval, result.proof);
      await onSaved(saved.resource.id);
    } catch (failure) {
      setError(failure instanceof Error ? failure.message : 'تعذّر تأكيد النتيجة.');
      setCode(''); setChallenge(null);
      if (transmitted) setUncertain(true);
    } finally { setBusy(false); }
  }
  return <form onSubmit={submit} className="space-y-3 rounded-xl border border-[var(--card-border)] p-4">
    <h3 className="font-bold">{approval.kind === 'create' ? 'مراجعة اعتماد التحويل' : approval.kind === 'retry' ? 'اعتماد محاولة جديدة بعد فشل مؤكد' : 'اعتماد جديد للمحاولة التي لم تُرسل'}</h3>
    <p>{approval.maskedBeneficiary}</p><p>{money({ amount_minor: Number(approval.details.amount_minor), currency: String(approval.details.currency), exponent: 2 })}</p>
    <p>راجع المستفيد والمبلغ. الاعتماد يتيح إرسال هذه المحاولة، وتظهر نتيجة التحويل بعد تأكيد المزود.</p>
    {challenge && <label className="block">رمز تطبيق التحقق<input className="block w-full rounded border p-2" required autoComplete="one-time-code" inputMode="numeric" pattern="[0-9]{6}" maxLength={6} value={code} onChange={event => setCode(event.target.value)} disabled={busy} /></label>}
    {error && <p role="alert">{error}</p>}
    {uncertain ? <><p>النتيجة غير محسومة. حدّث السجل الأصلي قبل أي متابعة.</p><button type="button" disabled={busy} className="rounded border px-4 py-2" onClick={() => { setBusy(true); void onSaved(approval.payoutId).catch(failure => setError(failure instanceof Error ? failure.message : 'تعذّر تحديث السجل.')).finally(() => setBusy(false)); }}>استعلام عن الحالة الحالية</button></> : <div className="flex flex-wrap gap-3"><button className="rounded border px-4 py-2" disabled={busy}>{busy ? 'جارٍ التحقق…' : challenge ? 'تأكيد الاعتماد' : 'التحقق من هذه البيانات'}</button><button type="button" className="rounded border px-4 py-2" onClick={onCancel} disabled={busy}>إلغاء المراجعة</button></div>}
  </form>;
}
