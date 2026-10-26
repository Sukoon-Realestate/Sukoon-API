'use client';

import { useState } from 'react';
import { beginRefundApproval, confirmRefundApproval, type RefundApproval } from '../../lib/api/refunds';
import { money } from '../../lib/api/payouts';
import { verifyReview, type Challenge } from '../../lib/api/security';

export function RefundApprovalForm({ value, onSaved, onCancel }: { value: RefundApproval; onSaved: () => Promise<void>; onCancel: () => void }) {
  const [challenge, setChallenge] = useState<Challenge | null>(null);
  const [code, setCode] = useState('');
  const [busy, setBusy] = useState(false);
  const [unknown, setUnknown] = useState(false);
  const [error, setError] = useState('');
  async function submit(event: React.FormEvent) {
    event.preventDefault(); if (busy || unknown) return;
    setBusy(true); setError(''); let transmitted = false;
    try {
      if (!challenge) { setChallenge(await beginRefundApproval(value)); return; }
      if (Date.parse(challenge.expires_at) <= Date.now()) throw new Error('انتهى إذن التحقق. اطلب إذنًا جديدًا لهذه البيانات.');
      const result = await verifyReview(challenge.id, code);
      setCode(''); setChallenge(null); transmitted = true;
      await confirmRefundApproval(value, result.proof); await onSaved();
    } catch (failure) {
      setError(failure instanceof Error ? failure.message : 'تعذّر تأكيد النتيجة.'); setCode(''); setChallenge(null);
      if (transmitted) setUnknown(true);
    } finally { setBusy(false); }
  }
  return <form onSubmit={submit} className="space-y-3 rounded border p-4">
    <h3 className="font-bold">{value.kind === 'retry' ? 'مراجعة محاولة جديدة بعد فشل مؤكد' : value.kind === 'reauthorize' ? 'اعتماد جديد لاسترداد لم يُرسل' : 'التحقق من إذن إرسال الاسترداد'}</h3>
    {value.kind === 'retry' && <p className="break-all">المحاولة الفاشلة: {value.command.failed_instruction_id}. يُعاد التحقق من نتيجتها قبل اعتماد المحاولة الجديدة، ويظل تاريخها محفوظًا.</p>}
    <p>{money(value.review.resource.amount)}</p><p className="break-all">الدفعة الأصلية: {value.review.resource.payment_attempt_id}</p>
    <p>يُعاد المبلغ إلى وسيلة الدفع الأصلية بعد تأكيد المزود. لا تُنشأ دفعة تحصيل جديدة.</p>
    {challenge && <label className="block">رمز تطبيق التحقق<input className="block w-full rounded border p-2" required autoComplete="one-time-code" inputMode="numeric" pattern="[0-9]{6}" maxLength={6} value={code} onChange={event => setCode(event.target.value)} disabled={busy} /></label>}
    {error && <p role="alert">{error}</p>}
    {unknown ? <><p>النتيجة غير محسومة؛ تابع السجل الأصلي قبل إجراء آخر.</p><button type="button" disabled={busy} className="rounded border px-4 py-2" onClick={() => { setBusy(true); void onSaved().catch(failure => setError(failure instanceof Error ? failure.message : 'تعذّر التحديث.')).finally(() => setBusy(false)); }}>استعادة الحالة الحالية</button></> : <div className="flex flex-wrap gap-3"><button className="rounded border px-4 py-2" disabled={busy}>{busy ? 'جارٍ التحقق…' : challenge ? 'تأكيد الإذن' : 'التحقق من هذه البيانات'}</button><button type="button" className="rounded border px-4 py-2" disabled={busy} onClick={onCancel}>إلغاء المراجعة</button></div>}
  </form>;
}
