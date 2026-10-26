'use client';

import { useCallback, useEffect, useState } from 'react';
import { Header } from '../layout/Header';
import { useAuth } from '../../context/AuthContext';
import { canOpenAdminPath } from '../../lib/admin-access';
import { fetchPayableQueue, fetchPayoutQueue, fetchPayoutReview, preparePayout, prepareReauthorization, reconcilePayout, payoutStatus, money, type PayableRow, type PayoutRow, type PayoutReview, type PayoutPage, type PayoutApproval } from '../../lib/api/payouts';
import { PayoutApprovalForm } from './PayoutApprovalForm';

const historyLabels: Record<string, string> = { approved: 'اعتُمد التحويل', submitted: 'أُرسلت المحاولة', held: 'تحتاج إلى متابعة', reauthorized: 'سُجل اعتماد جديد', retry_approved: 'اعتُمدت محاولة جديدة بعد فشل مؤكد', paid: 'تأكد التحويل' };
const panel = 'space-y-3 rounded-xl border border-[var(--card-border)] bg-[var(--card-bg)] p-4';

export default function PayoutsPage() {
  const { user } = useAuth();
  return <PayoutsWorkspace key={user?.id || 'signed-out'} />;
}

function PayoutsWorkspace() {
  const { user } = useAuth();
  const canRead = canOpenAdminPath(user?.allowedPaths, '/financials/payouts');
  const [page, setPage] = useState(1);
  const [queue, setQueue] = useState<PayoutPage<PayoutRow> | null>(null);
  const [payables, setPayables] = useState<PayoutPage<PayableRow> | null>(null);
  const [payablePage, setPayablePage] = useState(1);
  const [review, setReview] = useState<PayoutReview | null>(null);
  const [approval, setApproval] = useState<PayoutApproval | null>(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [fresh, setFresh] = useState(false);
  const load = useCallback((signal?: AbortSignal) =>
    Promise.all([fetchPayoutQueue(page, signal), fetchPayableQueue(payablePage, signal)]), [page, payablePage]);
  useEffect(() => {
    if (!canRead) return;
    const controller = new AbortController();
    void load(controller.signal).then(([rows, balances]) => {
      if (!controller.signal.aborted) { setQueue(rows); setPayables(balances); setFresh(true); }
    }).catch(failure => { if (!controller.signal.aborted) setError(failure instanceof Error ? failure.message : 'تعذّر تحميل التحويلات.'); });
    return () => controller.abort();
  }, [canRead, load, user?.id]);
  async function perform(command: () => Promise<void>) {
    if (busy) return; setBusy(true); setError(''); setFresh(false);
    try { await command(); setFresh(true); }
    catch (failure) { setFresh(false); setError(failure instanceof Error ? failure.message : 'تعذّر تأكيد النتيجة. حدّث السجل الأصلي.'); }
    finally { setBusy(false); }
  }
  async function saved(id?: string) {
    const [rows, balances] = await load();
    setQueue(rows); setPayables(balances); setFresh(true);
    setReview(id ? await fetchPayoutReview(id) : null);
    setApproval(null);
  }
  return <><Header title="مستحقات الملاك والتحويلات" /><main dir="rtl" className="mx-auto max-w-5xl space-y-5 p-4 sm:p-8">
    {!canRead ? <p role="alert">هذه المتابعة تحتاج إلى صلاحية الصرف أو مطابقة العمليات.</p> : <>
      <p>الاستحقاق، واعتماد الصرف، وتأكيد التحويل حالات منفصلة. الاستعلام يتابع المحاولة الأصلية دون إرسالها مجددًا.</p>
      {error && <p role="alert">{error}</p>}
      <button className="rounded border px-4 py-2" disabled={busy || !!approval} onClick={() => void perform(() => saved(review?.resource.id))}>تحديث السجلات</button>
      {approval && <PayoutApprovalForm key={approval.command.request_key} approval={approval} onSaved={saved} onCancel={() => setApproval(null)} />}
      {review && <section className={panel} aria-label="مراجعة التحويل">
        <h2 className="font-bold">متابعة المحاولة الأصلية</h2><p className="break-all">{review.resource.id}</p>
        <p>{review.resource.masked_beneficiary} · {money(review.resource.amount)}</p>
        <p>{payoutStatus[review.instruction_status] || 'حالة غير معروفة تحتاج إلى تحديث'}</p><p>{review.resource.reason}</p>
        {review.provider_reference && <p className="break-all">مرجع المزود: {review.provider_reference}</p>}
        <ol>{review.resource.history.map((event, index) => <li key={`${event.occurred_at}:${index}`}>{historyLabels[event.action] || 'تحديث الحالة'} — {new Date(event.occurred_at).toLocaleString('ar')}</li>)}</ol>
        <details><summary>المحاولات السابقة والحالية</summary><ul>{review.attempts.map(attempt => <li key={attempt.id} className="break-all py-2">{attempt.current ? 'الحالية' : 'السابقة'}: {payoutStatus[attempt.status] || 'تحتاج إلى مراجعة'} — {attempt.provider_reference || 'لا يوجد مرجع مؤكد لدى المزود'} — {new Date(attempt.created_at).toLocaleString('ar')}</li>)}</ul></details>
        <div className="flex flex-wrap gap-3">{review.allowed_actions.includes('reconcile') && <button className="rounded border px-4 py-2" disabled={busy || !!approval} onClick={() => void perform(async () => { await reconcilePayout(review.resource.id); await saved(review.resource.id); })}>استعلام عن نتيجة المحاولة</button>}
        {review.can_reauthorize && <button className="rounded border px-4 py-2" disabled={busy || !fresh || !!approval || !review.allowed_actions.includes('reauthorize')} onClick={() => setApproval(prepareReauthorization(review))}>مراجعة اعتماد جديد للمحاولة غير المرسلة</button>}</div>
        {review.can_retry && <button className="rounded border px-4 py-2" disabled={busy || !fresh || !!approval || !review.allowed_actions.includes('retry')} onClick={() => setApproval(prepareReauthorization(review, true))}>مراجعة محاولة جديدة بعد الفشل المؤكد</button>}
        {review.reauthorize_reason && <p>{review.reauthorize_reason}</p>}
      </section>}
      <section className={panel}><h2 className="font-bold">سجل التحويلات</h2>
        {!queue ? <p role="status">جارٍ تحميل السجل…</p> : !queue.count ? <p>لا توجد تحويلات مرتبطة بالمزود حتى الآن.</p> : queue.results.map(row => <article key={row.resource.id} className="flex flex-wrap items-center justify-between gap-3 border-b py-3"><div><p>{row.resource.masked_beneficiary} · {money(row.resource.amount)}</p><p>{payoutStatus[row.instruction_status] || 'بانتظار المراجعة'}</p></div><button className="rounded border px-4 py-2" disabled={busy || !!approval} onClick={() => void perform(async () => setReview(await fetchPayoutReview(row.resource.id)))}>فتح المحاولة</button></article>)}
        {queue && <div className="flex flex-wrap items-center gap-3"><button disabled={page <= 1 || busy || !!approval} onClick={() => setPage(value => value - 1)}>السابق</button><span>{page} / {queue.total_pages}</span><button disabled={page >= queue.total_pages || busy || !!approval} onClick={() => setPage(value => value + 1)}>التالي</button></div>}
      </section>
      <section className={panel}><h2 className="font-bold">المستحقات التي لم تُرسل</h2>
        {!payables ? <p role="status">جارٍ تحميل المستحقات…</p> : !payables.count ? <p>لا توجد مستحقات متاحة للمراجعة.</p> : payables.results.map(row => <article key={row.id} className="space-y-2 border-b py-3"><p>{row.masked_beneficiary} · {money(row.amount)}</p><p className="break-all">الفاتورة: {row.invoice_id}</p><p>{payoutStatus[row.status] || 'تحتاج إلى مراجعة'}</p>{row.blocking_reasons.map(reason => <p key={reason}>{reason}</p>)}{!row.provider_ready && <p>تحتاج قناة الصرف والمستفيد إلى تجهيز ومراجعة قبل الإرسال.</p>}{row.can_prepare && <button className="rounded border px-4 py-2 disabled:opacity-50" disabled={!row.can_execute || !fresh || busy || !!approval} onClick={() => void perform(async () => setApproval(await preparePayout(row)))}>مراجعة اعتماد الصرف</button>}</article>)}
        {payables && <div className="flex flex-wrap items-center gap-3"><button disabled={payablePage <= 1 || busy || !!approval} onClick={() => setPayablePage(value => value - 1)}>السابق</button><span>{payablePage} / {payables.total_pages}</span><button disabled={payablePage >= payables.total_pages || busy || !!approval} onClick={() => setPayablePage(value => value + 1)}>التالي</button></div>}
      </section>
    </>}
  </main></>;
}
