'use client';

import { useCallback, useEffect, useState, useRef } from 'react';
import { Header } from '../layout/Header';
import { reviewList, reviewDetail, decideTour, TourReview, ReviewPage } from '../../lib/api/tour-review';
import { TourPreviewButton } from './TourPreviewButton';
import { ApiError } from '../../lib/api/client';

const label: Record<string, string> = { pending: 'بانتظار المراجعة', approved: 'معتمد', rejected: 'مرفوض', ready: 'جاهز', panorama_360: 'جولة بانورامية', model_3d: 'جولة ثلاثية الأبعاد' };
export default function TourReviewPage() {
  const [state, setState] = useState('pending');
  const [page, setPage] = useState(1);
  const [result, setResult] = useState<ReviewPage | null>(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [selected, setSelected] = useState<TourReview | null>(null);
  const load = useCallback(async (signal?: AbortSignal) => {
    setLoading(true); setError('');
    try { const value = await reviewList(state, page, signal); if (!signal?.aborted) setResult(value); }
    catch (failure) { if (!signal?.aborted) setError(failure instanceof Error ? failure.message : 'تعذّر تحميل المراجعات.'); }
    finally { if (!signal?.aborted) setLoading(false); }
  }, [state, page]);
  useEffect(() => { const controller = new AbortController(); void load(controller.signal); return () => controller.abort(); }, [load]);
  return <><Header title="مراجعة الجولات" /><main dir="rtl" className="mx-auto max-w-5xl space-y-5 p-4 sm:p-8">
    <p>راجع الإصدار والمخرجات ونطاق الغرف قبل القرار. اعتماد الجولة لا يغيّر حالة مراجعة إعلان العقار.</p>
    <div className="flex flex-wrap gap-3"><label>الحالة <select value={state} disabled={loading} onChange={e => { setState(e.target.value); setPage(1); setSelected(null); }} className="rounded border p-2">{['pending', 'approved', 'rejected', 'all'].map(value => <option key={value} value={value}>{label[value] || 'كل المراجعات'}</option>)}</select></label><button className="rounded border px-4 py-2" disabled={loading} onClick={() => void load()}>تحديث القائمة</button></div>
    {error && <p role="alert">{error}</p>}{loading && <p role="status">جارٍ التحميل…</p>}
    {result && <><p>عدد الإصدارات: {result.count}</p><ul className="space-y-3">{result.items.map(item => <li key={item.id} className="rounded-xl border p-4"><button className="text-start underline" onClick={() => setSelected(item)}>{item.title || 'جولة عقار'} · {label[item.kind] || item.kind} · {label[item.review_state] || item.review_state}</button><p>الإصدار {item.draft_version}</p></li>)}</ul>{result.items.length === 0 && <p>لا توجد إصدارات في هذه القائمة.</p>}<div className="flex gap-3"><button disabled={loading || page === 1} onClick={() => { setPage(page - 1); setSelected(null); }}>السابق</button><span>صفحة {page}</span><button disabled={loading || !result.has_next} onClick={() => { setPage(page + 1); setSelected(null); }}>التالي</button></div></>}
    {selected && <ReviewEditor key={selected.id} initial={selected} onSaved={() => load()} />}
  </main></>;
}

function ReviewEditor({ initial, onSaved }: { initial: TourReview; onSaved: () => Promise<void> }) {
  const [item, setItem] = useState(initial);
  const [reason, setReason] = useState('');
  const [decision, setDecision] = useState('approved');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [uncertain, setUncertain] = useState(false);
  const intent = useRef<{ body: string; key: string } | null>(null);
  async function refresh() {
    setBusy(true); setError('');
    try { const value = await reviewDetail(item.id); setItem(value); if (value.review_state !== 'pending') setUncertain(false); }
    catch (failure) { setError(failure instanceof Error ? failure.message : 'تعذّر تحديث الإصدار.'); }
    finally { setBusy(false); }
  }
  async function submit(event: React.FormEvent) {
    event.preventDefault(); if (busy || !item.can_review) return;
    const body = JSON.stringify({ id: item.id, hash: item.source_hash, decision, reason });
    if (!intent.current || intent.current.body !== body) intent.current = { body, key: crypto.randomUUID() };
    setBusy(true); setError(''); setUncertain(true);
    try {
      await decideTour(item, decision, reason, intent.current.key);
      setItem(await reviewDetail(item.id)); setUncertain(false); await onSaved();
    } catch (failure) {
      if (failure instanceof ApiError && failure.status < 500 && ![408, 429].includes(failure.status)) setUncertain(false);
      setError(failure instanceof Error ? failure.message : 'تعذّر تأكيد القرار. حدّث الإصدار أو استعد نتيجة القرار نفسه.');
    }
    finally { setBusy(false); }
  }
  return <section className="space-y-4 rounded-xl border p-4"><h2 className="text-xl font-bold">{item.title}</h2>
    <p>حالة الإصدار: {label[item.review_state] || item.review_state} · المعالجة: {label[item.processing_state] || item.processing_state}</p>
    <button type="button" disabled={busy} className="rounded border px-4 py-2" onClick={() => void refresh()}>تحديث الإصدار وسجل القرار</button>
    {item.variants.map(variant => <section className="rounded border p-3" key={variant.id}><p>نطاق المعاينة: {variant.context === 'overview' ? 'المساحات العامة المسموحة' : variant.context}</p><TourPreviewButton item={item} context={variant.context} /></section>)}
    <details><summary>تقرير المعالجة</summary><pre dir="ltr" className="overflow-auto whitespace-pre-wrap">{JSON.stringify(item.report, null, 2)}</pre></details>
    {!item.can_review && <p>{item.review_blocker}</p>}
    <form onSubmit={submit} className="space-y-3"><label className="block">القرار<select className="block w-full rounded border p-2" disabled={busy || uncertain || !item.can_review} value={decision} onChange={e => setDecision(e.target.value)}><option value="approved">اعتماد المخرجات بعد فحصها</option><option value="rejected">رفض مع سبب التصحيح</option></select></label><label className="block">توثيق المراجعة أو سبب الرفض<textarea required maxLength={4000} className="block w-full rounded border p-2" value={reason} disabled={busy || uncertain || !item.can_review} onChange={e => setReason(e.target.value)} /></label>
    {error && <p role="alert">{error}</p>}<button className="rounded border px-4 py-2" disabled={busy || !item.can_review}>{uncertain ? 'استعادة نتيجة القرار نفسه' : 'حفظ القرار لهذا الإصدار'}</button></form>
    <ol className="space-y-2">{item.history.map((event, index) => <li key={`${event.created_at}:${index}`}>{label[event.decision] || event.decision} — {event.reason} — {new Date(event.created_at).toLocaleString('ar')}</li>)}</ol>
  </section>;
}
