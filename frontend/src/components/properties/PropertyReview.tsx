'use client';

import { Header } from '@/components/layout/Header';

import { Suspense, useCallback, useEffect, useRef, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import { apiClient } from '../../lib/api/client';
import { exportProperty, fetchAdminProperties, fetchAdminPropertyDetail, moderateProperty, PropertyDecision, recoverPropertyReview } from '../../lib/api/properties';
import { PropertyDetail, PropertyItem } from '../../lib/api/types';

const labels: Record<PropertyDecision, string> = { approve: 'اعتماد العقار', reject: 'رفض مع إتاحة التصحيح', request_revision: 'طلب تعديل', block: 'حظر العقار', unblock: 'رفع الحظر وإعادة المراجعة' };
const control = 'rounded-lg border border-[var(--card-border)] px-4 py-2 disabled:opacity-50';

function ReviewDetail({ id, onChanged }: { id: string; onChanged: () => void }) {
  const [detail, setDetail] = useState<PropertyDetail | null>(null);
  const [reason, setReason] = useState('');
  const [note, setNote] = useState('');
  const [decision, setDecision] = useState<PropertyDecision>('approve');
  const [pending, setPending] = useState<string | null>(null);
  const [storageKey, setStorageKey] = useState('');
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [busy, setBusy] = useState(false);
  const submitting = useRef(false);
  const active = useRef(true);
  const loadAbort = useRef<AbortController | null>(null);
  const load = useCallback(() => {
    loadAbort.current?.abort();
    const controller = new AbortController(); loadAbort.current = controller;
    return Promise.all([fetchAdminPropertyDetail(id, controller.signal), apiClient<{id: string}>('/api/v1/admin/session/', {signal: controller.signal})]).then(([value, session]) => {
    if (!active.current || controller.signal.aborted) return;
    const key = `property-review:${session.id}:${id}`;
    setDetail(value); setStorageKey(key); setPending(sessionStorage.getItem(key));
      setError('');

    }).catch(failure => { if (!controller.signal.aborted) throw failure; });
  }, [id]);
  useEffect(() => {
    active.current = true;
    void load().catch(e => { if (active.current) setError(e.message); });
    return () => { active.current = false; loadAbort.current?.abort(); };
  }, [load]);
  const finish = () => { sessionStorage.removeItem(storageKey); setPending(null); };
  const submit = async () => {
    if (!detail || !storageKey || pending || submitting.current || !detail.actions[decision]?.enabled) return;
    if (decision !== 'approve' && !reason.trim()) { setError('اكتب سببًا واضحًا للمالك وخطوة التصحيح المطلوبة.'); return; }
    submitting.current = true; setBusy(true); setError(''); setNotice('');
    const key = crypto.randomUUID();
    try {
      sessionStorage.setItem(storageKey, key); setPending(key);
      const result = await moderateProperty(id, decision, {expected_version: detail.review_version, reason, internal_note: note}, key);
      if (result.property_id !== id || !result.decision_id || result.revision <= detail.review_revision) throw new Error('لم يُؤكد حفظ القرار. استعد نتيجته الأصلية.');
      if (!active.current) return;
      finish(); setReason(''); setNote(''); await load(); onChanged(); setNotice('حُفظ القرار وأُضيف إلى تاريخ العقار.');
    } catch (e) { if (active.current) setError(e instanceof Error ? e.message : 'تعذّر تأكيد النتيجة.'); }
    finally { submitting.current = false; if (active.current) setBusy(false); }
  };
  const recover = async () => {
    if (!pending || submitting.current) return;
    submitting.current = true; setBusy(true); setError('');
    try {
      let result = await recoverPropertyReview(id, pending);
      if (result.status === 'unknown') result = await recoverPropertyReview(id, pending, true);
      if (!active.current) return;
      if (result.status === 'confirmed' || result.status === 'absent_final') {
        finish(); await load(); onChanged();
        setNotice(result.status === 'confirmed' ? 'استُعيد القرار المحفوظ دون تكراره.' : 'لم يُنفذ القرار السابق. راجع النسخة الحالية قبل اتخاذ قرار جديد.');
      } else setNotice('النتيجة لا تزال قيد الاستعلام.');
    } catch (e) { if (active.current) setError(e instanceof Error ? e.message : 'تعذّر استرجاع القرار.'); }
    finally { submitting.current = false; if (active.current) setBusy(false); }
  };
  return <section className="min-w-0 space-y-4">
    {error && <p role="alert">{error}</p>}{notice && <p role="status">{notice}</p>}
    <button className={control} disabled={busy} onClick={() => void load().catch(e => setError(e.message))}>تحديث نسخة المراجعة</button>
    {pending && <div className="border rounded-xl p-4 space-y-2"><p>استعلم عن القرار السابق قبل تنفيذ أي قرار جديد.</p><button className={control} disabled={busy} onClick={() => void recover()}>استعادة نتيجة القرار</button></div>}
    {detail ? <>
      <article className="border rounded-xl p-4 space-y-3">
        <h2 className="text-xl font-bold">{detail.title}</h2><p>الإصدار {detail.review_revision} · {detail.moderation_blocked ? 'محظور' : detail.status}</p>
        <p className="whitespace-pre-wrap">{detail.description}</p><p>{detail.price} · {detail.price_period}</p><p>{detail.location} · {detail.area}</p><p>المالك: {detail.owner}</p>
        {detail.moderation_reason && <p>سبب آخر قرار: {detail.moderation_reason}</p>}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">{detail.images.map((src, index) => <a key={`${src}:${index}`} href={src} target="_blank" rel="noreferrer"><img className="w-full rounded-lg object-contain max-h-80" src={src} alt={`دليل العقار ${index + 1}`} /></a>)}</div>
        <details><summary className="cursor-pointer">بيانات النسخة والأدلة كاملة</summary><dl className="space-y-2 break-words">{Object.entries(detail.review_snapshot).map(([key, value]) => <div key={key}><dt className="font-semibold">{key}</dt><dd dir="auto" className="whitespace-pre-wrap">{typeof value === 'object' ? JSON.stringify(value, null, 2) : String(value ?? '—')}</dd></div>)}</dl></details>
        <button className={control} onClick={() => void exportProperty(id).catch(e => setError(e.message))}>تنزيل بيانات العقار</button>
      </article>
      <form className="border rounded-xl p-4 space-y-3" onSubmit={e => {e.preventDefault(); void submit();}}>
        <h2 className="font-bold">قرار المراجعة</h2>
        <label className="block">الإجراء<select aria-label="الإجراء" disabled={busy || !!pending} className="block w-full border rounded p-2" value={decision} onChange={e => setDecision(e.target.value as PropertyDecision)}>{Object.entries(labels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label>
        {!detail.actions[decision]?.enabled && <p>{detail.actions[decision]?.reason || 'راجع الصلاحية والحالة الحالية.'}</p>}
        <label className="block">السبب الظاهر للمالك<textarea className="block w-full border rounded p-3" maxLength={2000} value={reason} onChange={e => setReason(e.target.value)} required={decision !== 'approve'} /></label>
        <label className="block">ملاحظة داخلية للمراجعين<textarea className="block w-full border rounded p-3" maxLength={4000} value={note} onChange={e => setNote(e.target.value)} /></label>
        <p>سيُحفظ القرار على النسخة المعروضة. أي تعديل عليها يتطلب مراجعتها مجددًا.</p>
        <button className={control} disabled={busy || !!pending || !detail.actions[decision]?.enabled}>تأكيد {labels[decision]}</button>
      </form>
      <section className="space-y-3"><h2 className="font-bold">تاريخ القرارات</h2>{detail.review_history.length === 0 && <p>لا توجد قرارات محفوظة بعد.</p>}{detail.review_history.map(row => <article className="border rounded p-3" key={row.id}><p>{labels[row.action as PropertyDecision] || row.action} · الإصدار {row.revision} · {new Date(row.created_at).toLocaleString('ar')}</p><p className="whitespace-pre-wrap">{row.reason}</p>{row.internal_note && <p className="whitespace-pre-wrap">ملاحظة داخلية: {row.internal_note}</p>}</article>)}</section>
    </> : <p role="status">جارٍ تحميل نسخة العقار…</p>}
  </section>;
}

function ReviewQueueContent({ queryId }: { queryId: string }) {
  const [selected, setSelected] = useState(queryId);
  const [items, setItems] = useState<PropertyItem[]>([]);
  const [page, setPage] = useState(1);
  const [pages, setPages] = useState(1);
  const [filter, setFilter] = useState('under_review');
  const [revision, setRevision] = useState(0);
  const changed = useCallback(() => setRevision(value => value + 1), []);
  const [error, setError] = useState('');
  useEffect(() => {
    let current = true;
    void fetchAdminProperties({status: filter, page, page_size: 20}).then(result => {
      if (!current) return;
      setItems(result.results); setPages(Math.max(1, Math.ceil(result.count / 20))); setError('');
    }).catch(e => { if (current) setError(e.message); });
    return () => { current = false; };
  }, [filter, page, revision]);
  return <>
    <Header title="مراجعة العقارات" />
    <section dir="rtl" className="mx-auto w-full max-w-7xl space-y-5 p-4 sm:p-8">

    <div className="grid grid-cols-1 md:grid-cols-[minmax(180px,1fr)_3fr] gap-5">
      <aside className="space-y-3 min-w-0"><label>الحالة<select aria-label="الحالة" className="block w-full border rounded p-2" value={filter} onChange={e => {setFilter(e.target.value);setPage(1);}}><option value="under_review">قيد المراجعة</option><option value="needs_revision">يحتاج تصحيحًا</option><option value="blocked">محظور</option><option value="">كل العقارات</option></select></label>
        {error && <p role="alert">{error}</p>}{items.map(item => <button className={`${control} block w-full text-start break-words`} aria-pressed={selected === item.id} key={item.id} onClick={() => setSelected(item.id)}>{item.title}<span className="block">{item.status}</span></button>)}
        {!error && items.length === 0 && <p>لا توجد عقارات في هذه الصفحة.</p>}
        <div className="flex flex-wrap gap-2"><button className={control} disabled={page <= 1} onClick={() => setPage(p => p - 1)}>السابق</button><span>{page} / {pages}</span><button className={control} disabled={page >= pages} onClick={() => setPage(p => p + 1)}>التالي</button></div>
      </aside>
      {selected ? <ReviewDetail key={selected} id={selected} onChanged={changed} /> : <p>اختر عقارًا لعرض نسخته الحالية وأدلته.</p>}
    </div>
  </section></>;
}
function ReviewQueue() {
  const queryId = useSearchParams().get('id') || '';
  return <ReviewQueueContent key={queryId} queryId={queryId} />;
}
export default function PropertyReview() { return <Suspense fallback={<p>جارٍ تحميل المراجعة…</p>}><ReviewQueue /></Suspense>; }
