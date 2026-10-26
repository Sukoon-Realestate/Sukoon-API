'use client';

import { useEffect, useState } from 'react';
import { Header } from '../layout/Header';
import { useAuth } from '../../context/AuthContext';
import { canOpenAdminPath } from '../../lib/admin-access';
import { money, type PayoutPage } from '../../lib/api/payouts';
import { fetchRefunds, fetchRefund, prepareRefund, respondRefund, reconcileRefund, refundStatus, type RefundReview, type RefundApproval } from '../../lib/api/refunds';
import { RefundApprovalForm } from './RefundApprovalForm';

const historyLabels: Record<string, string> = { requested: 'طُلب الاسترداد', approved: 'اعتُمد الطلب', rejected: 'رُفض الطلب', authorized: 'اعتُمد الإرسال', submitted: 'أُرسلت المحاولة', review: 'تحتاج إلى متابعة', reauthorized: 'سُجل اعتماد جديد للمحاولة غير المرسلة', succeeded: 'تأكد الاسترداد', failed: 'تأكد فشل المحاولة', retried: 'اعتُمدت محاولة جديدة بعد فشل مؤكد' };

export default function RefundsPage() {
  const { user } = useAuth();
  return <RefundsWorkspace key={user?.id || 'signed-out'} />;
}

function RefundsWorkspace() {
  const { user } = useAuth();
  const canRead = canOpenAdminPath(user?.allowedPaths, '/financials/refunds');
  const [page, setPage] = useState(1);
  const [rows, setRows] = useState<PayoutPage<RefundReview> | null>(null);
  const [review, setReview] = useState<RefundReview | null>(null);
  const [approval, setApproval] = useState<RefundApproval | null>(null);
  const [candidate, setCandidate] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [fresh, setFresh] = useState(false);
  useEffect(() => {
    if (!canRead) return;
    const controller = new AbortController();
    void fetchRefunds(page, controller.signal).then(value => { if (!controller.signal.aborted) setRows(value); }).catch(failure => { if (!controller.signal.aborted) setError(failure instanceof Error ? failure.message : 'تعذّر تحميل الاسترداد.'); });
    return () => controller.abort();
  }, [page, canRead]);
  async function perform(command: () => Promise<void>) {
    if (busy) return; setBusy(true); setError(''); setFresh(false);
    try { await command(); setFresh(true); }
    catch (failure) { setError(failure instanceof Error ? failure.message : 'تعذّر تأكيد النتيجة؛ حدّث السجل الأصلي.'); }
    finally { setBusy(false); }
  }
  async function reload(id?: string) {
    const [list, item] = await Promise.all([fetchRefunds(page), id ? fetchRefund(id) : Promise.resolve(null)]);
    setRows(list); setReview(item); setApproval(null); setCandidate(''); setFresh(true);
  }
  async function decision(action: 'approve' | 'reject') {
    if (!review) return;
    await respondRefund(review, action, crypto.randomUUID()); await reload(review.resource.id);
  }
  return <><Header title="الاسترداد" /><main dir="rtl" className="mx-auto max-w-5xl space-y-5 p-4 sm:p-8">
    {!canRead ? <p role="alert">تحتاج هذه المتابعة إلى صلاحية الاسترداد أو مطابقة العمليات.</p> : <>
      <p>راجع طلب الاسترداد ثم إذن إرساله. النتيجة النهائية تأتي من تأكيد المزود للمحاولة الأصلية.</p>
      {error && <p role="alert">{error}</p>}
      <button className="rounded border px-4 py-2" disabled={busy || !!approval} onClick={() => void perform(() => reload(review?.resource.id))}>تحديث السجلات</button>
      {approval && <RefundApprovalForm key={approval.command.request_key} value={approval} onSaved={() => reload(approval.review.resource.id)} onCancel={() => setApproval(null)} />}
      {review && <section aria-label="مراجعة الاسترداد" className="space-y-3 rounded-xl border border-[var(--card-border)] bg-[var(--card-bg)] p-4">
        <h2 className="font-bold">متابعة الاسترداد الأصلي</h2><p className="break-all">{review.resource.id}</p><p>{money(review.resource.amount)}</p>
        <p>{refundStatus[review.resource.status] || 'حالة تحتاج إلى تحديث'}</p>{review.instruction_status && <p>{refundStatus[review.instruction_status] || 'حالة المحاولة تحتاج إلى مراجعة'}</p>}
        <p>{review.resource.reason}</p><p className="break-all">الدفعة الأصلية: {review.resource.payment_attempt_id}</p>
        {review.provider_reference && <p className="break-all">مرجع المزود: {review.provider_reference}</p>}
        <ol>{review.resource.history.map((item, index) => <li key={`${item.occurred_at}:${index}`}>{historyLabels[item.action] || 'تحديث الحالة'} — {new Date(item.occurred_at).toLocaleString('ar')}</li>)}</ol>
        {!!review.resource.attempts?.length && <section aria-label="محاولات الاسترداد"><h3 className="font-bold">محاولات الاسترداد</h3><ol className="space-y-2">{review.resource.attempts.map(item => <li className="break-all rounded border p-2" key={item.id}><p>{item.current ? 'المحاولة الحالية' : 'محاولة سابقة'}: {refundStatus[item.status] || 'تحتاج إلى مراجعة'}</p><p>{item.id}</p>{item.retry_of && <p>تعيد محاولة: {item.retry_of}</p>}<p>{new Date(item.resolved_at || item.submitted_at || item.created_at).toLocaleString('ar')}</p></li>)}</ol></section>}
        {review.blocking_reasons.map(reason => <p key={reason}>{reason}</p>)}
        <div className="flex flex-wrap gap-3">{(['approve', 'reject'] as const).filter(action => review.allowed_actions.includes(action)).map(action => <button className="rounded border px-4 py-2" key={action} disabled={busy || !fresh || !!approval} onClick={() => void perform(() => decision(action))}>{action === 'approve' ? 'اعتماد الطلب' : 'رفض الطلب'}</button>)}
          {review.can_execute && <button className="rounded border px-4 py-2" disabled={busy || !fresh || !!approval || !review.allowed_actions.includes('execute')} onClick={() => setApproval(prepareRefund(review, 'execute'))}>مراجعة إذن الإرسال</button>}
          {review.can_reauthorize && <button className="rounded border px-4 py-2" disabled={busy || !fresh || !!approval || !review.allowed_actions.includes('reauthorize')} onClick={() => setApproval(prepareRefund(review, 'reauthorize'))}>مراجعة اعتماد جديد للمحاولة غير المرسلة</button>}
          {review.can_retry && <button className="rounded border px-4 py-2" disabled={busy || !fresh || !!approval || !review.allowed_actions.includes('retry')} onClick={() => setApproval(prepareRefund(review, 'retry'))}>مراجعة محاولة جديدة بعد الفشل المؤكد</button>}
        </div>
        {review.allowed_actions.includes('reconcile') && <form className="space-y-3" onSubmit={event => { event.preventDefault(); void perform(async () => { await reconcileRefund(review.resource.id, candidate || undefined); await reload(review.resource.id); }); }}>
          {!review.provider_reference && <label className="block">مرجع محاولة الاسترداد لدى المزود، إن توفر<input className="block w-full rounded border p-2" inputMode="numeric" pattern="[0-9]{1,18}" value={candidate} onChange={event => setCandidate(event.target.value)} disabled={busy} /><span className="block">إدخال المرجع يستعلم عنه؛ لا يثبت النجاح قبل تطابق نتيجة المزود.</span></label>}
          <button className="rounded border px-4 py-2" disabled={busy || !!approval}>استعلام عن نتيجة الاسترداد</button>
        </form>}
      </section>}
      <section className="space-y-3 rounded-xl border border-[var(--card-border)] bg-[var(--card-bg)] p-4"><h2 className="font-bold">طلبات الاسترداد</h2>
        {!rows ? <p role="status">جارٍ تحميل الطلبات…</p> : !rows.count ? <p>لا توجد طلبات استرداد.</p> : rows.results.map(row => <article key={row.resource.id} className="flex flex-wrap items-center justify-between gap-3 border-b py-3"><div><p>{money(row.resource.amount)}</p><p>{refundStatus[row.resource.status] || 'تحتاج إلى مراجعة'}</p></div><button className="rounded border px-4 py-2" disabled={busy || !!approval} onClick={() => void perform(async () => { setReview(await fetchRefund(row.resource.id)); setCandidate(''); })}>فتح الطلب</button></article>)}
        {rows && <div className="flex flex-wrap gap-3"><button disabled={page <= 1 || busy || !!approval} onClick={() => setPage(value => value - 1)}>السابق</button><span>{page} / {rows.total_pages}</span><button disabled={page >= rows.total_pages || busy || !!approval} onClick={() => setPage(value => value + 1)}>التالي</button></div>}
      </section>
    </>}
  </main></>;
}
