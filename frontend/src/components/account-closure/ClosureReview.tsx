'use client';

import { Header } from '@/components/layout/Header';

import { Suspense, useCallback, useEffect, useRef, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import { apiClient } from '../../lib/api/client';
import { Challenge, verifyReview } from '../../lib/api/security';
import { canReviewClosure, ClosureDecision, ClosureRequest, closureChallenge, closureDecide, closureDetail, closureQueue, closureRecover } from '../../lib/api/account-closure';

const labels: Record<string, string> = {in_review: 'قيد المراجعة', awaiting_settlement: 'بانتظار تسوية الموانع', withdrawn: 'سُحب الطلب', rejected: 'رُفض الطلب', completed: 'اكتمل الحذف', requested: 'تقديم الطلب'};
const control = 'block w-full rounded-lg border p-3 disabled:opacity-50';

function Decision({ id, onSaved }: { id: string; onSaved: () => void }) {
  const [item, setItem] = useState<ClosureRequest | null>(null);
  const [body, setBody] = useState<ClosureDecision>({expected_revision: 0, decision: 'wait', reason: ''});
  const [challenge, setChallenge] = useState<Challenge | null>(null);
  const [code, setCode] = useState('');
  const [pending, setPending] = useState<string | null>(null);
  const [storageKey, setStorageKey] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const active = useRef(true);
  const running = useRef(false);
  const abort = useRef<AbortController | null>(null);
  const load = useCallback(() => {
    abort.current?.abort();
    const controller = new AbortController(); abort.current = controller;
    return Promise.all([closureDetail(id, controller.signal), apiClient<{id: string}>('/api/v1/admin/session/', {signal: controller.signal})]).then(([value, session]) => {
    if (!active.current || controller.signal.aborted) return;
    const key = `account-closure:${session.id}:${id}`;
    setItem(value); setBody({expected_revision: value.revision, decision: 'wait', reason: ''});
    setStorageKey(key); setPending(sessionStorage.getItem(key)); setChallenge(null); setCode('');
      setError('');

    }).catch(failure => { if (!controller.signal.aborted) throw failure; });
  }, [id]);
  useEffect(() => { active.current = true; void load().catch(e => {if (active.current) setError(e.message);}); return () => {active.current = false; abort.current?.abort();}; }, [load]);
  const change = (patch: Partial<ClosureDecision>) => {setBody(value => ({...value, ...patch})); setChallenge(null); setCode('');};
  async function recover() {
    if (!pending || running.current) return;
    running.current = true; setBusy(true); setError('');
    try {
      const result = await closureRecover(id, pending);
      if (!active.current) return;
      if (result.state !== 'confirmed' && result.state !== 'absent_final') throw new Error('النتيجة ما زالت معلقة.');
      sessionStorage.removeItem(storageKey); setPending(null); await load(); onSaved();
    } catch (e) { if (active.current) setError(e instanceof Error ? e.message : 'تعذر الاستعلام.'); }
    finally {running.current = false; if (active.current) setBusy(false);}
  }
  async function submit(event: React.FormEvent) {
    event.preventDefault(); if (!item?.active || pending || running.current || !storageKey) return;
    running.current = true; setBusy(true); setError('');
    try {
      if (!challenge) {
        const next = await closureChallenge(item, body); if (active.current) setChallenge(next);
      } else {
        if (Date.parse(challenge.expires_at) <= Date.now()) throw new Error('انتهى التحقق. راجع القرار وابدأ تحققًا جديدًا.');
        const proof = await verifyReview(challenge.id, code);
        if (!active.current) return;
        setCode(''); const key = crypto.randomUUID(); sessionStorage.setItem(storageKey, key); setPending(key);
        const saved = await closureDecide(id, body, proof.proof, key);
        if (!active.current) return;
        if (saved.id !== id || saved.revision <= item.revision) throw new Error('لم تؤكد استجابة الخادم حفظ القرار.');
        sessionStorage.removeItem(storageKey); setPending(null); await load(); onSaved();
      }
    } catch (e) {if (active.current) {setError(e instanceof Error ? e.message : 'تعذر تأكيد القرار.'); setChallenge(null); setCode('');}}
    finally {running.current = false; if (active.current) setBusy(false);}
  }
  return <section className="min-w-0 space-y-4 rounded-xl border p-4">
    {error && <p role="alert">{error}</p>}
    <button type="button" className="rounded border px-4 py-2" disabled={busy} onClick={() => void load().catch(e => setError(e.message))}>تحديث الحالة</button>
    {pending && <div role="status"><p>لم تتأكد نتيجة القرار السابق. استعلم قبل اتخاذ إجراء آخر.</p><button className="rounded border px-4 py-2" disabled={busy} onClick={() => void recover()}>استعادة نتيجة القرار</button></div>}
    {item && <>
      <h2 className="text-xl font-bold">{item.account_name}</h2><p>{labels[item.status]}</p><p>{item.reason}</p>
      {item.erasure_pending && <p role="status">أُزيلت بيانات الملف. حذف ملفات الوسائط غير المرتبطة بسجلات مطلوبة ما زال قيد التنفيذ.</p>}
      <h3 className="font-bold">الموانع الحالية</h3>
      {item.blockers.length ? <ul className="space-y-2">{item.blockers.map(b => <li key={b.code}>{b.label} ({b.count})</li>)}</ul> : <p>لا توجد موانع حالية. يعيد الخادم الفحص عند حسم الطلب.</p>}
      <p>إتمام الحذف يغلق الدخول ويحذف بيانات الملف غير اللازمة. تظل سجلات العقود والمال والتدقيق المطلوبة محفوظة بصلاحياتها.</p>
      {item.active && <form onSubmit={submit} className="space-y-4">
        <label className="block">القرار<select aria-label="القرار" className={control} disabled={busy || !!pending} value={body.decision} onChange={e => change({decision: e.target.value as ClosureDecision['decision']})}><option value="wait">انتظار تسوية الموانع</option><option value="reject">رفض بسبب</option><option value="complete" disabled={!!item.blockers.length}>إتمام الحذف</option></select></label>
        <label className="block">السبب الظاهر للمستخدم<textarea className={control} disabled={busy || !!pending} required maxLength={2000} value={body.reason} onChange={e => change({reason: e.target.value})} /></label>
        {challenge && <label className="block">رمز تطبيق التحقق<input className={control} autoComplete="one-time-code" inputMode="numeric" required minLength={6} maxLength={6} disabled={busy} value={code} onChange={e => setCode(e.target.value)} /></label>}
        <button className="rounded border px-4 py-2 disabled:opacity-50" disabled={busy || !!pending || (body.decision === 'complete' && !!item.blockers.length)}>{busy ? 'جارٍ التحقق…' : challenge ? 'تأكيد القرار' : 'التحقق من القرار'}</button>
      </form>}
      <details><summary>سجل الطلب</summary><ol className="space-y-3 py-3">{item.history.map(row => <li key={row.revision}><strong>{labels[row.action] || row.action}</strong><p>{row.reason}</p><time>{new Date(row.at).toLocaleString('ar-EG')}</time></li>)}</ol></details>
    </>}
  </section>;
}

function ClosureReviewContent() {
  const query = useSearchParams();
  const [rows, setRows] = useState<ClosureRequest[]>([]);
  const [page, setPage] = useState(1); const [pages, setPages] = useState(1);
  const [history, setHistory] = useState(false); const [selected, setSelected] = useState(query.get('request') || '');
  const [revision, setRevision] = useState(0); const [error, setError] = useState(''); const [loadedKey, setLoadedKey] = useState('');
  const queryKey = JSON.stringify([page, history, revision]);
  const busy = loadedKey !== queryKey;
  useEffect(() => {
    const controller = new AbortController();
    void (async () => {
      const session = await apiClient<{role: string}>('/api/v1/admin/session/', {signal: controller.signal});
      if (!canReviewClosure(session.role)) throw new Error('مراجعة حذف الحساب تحتاج صلاحيتها المستقلة.');
      const result = await closureQueue(page, history, controller.signal);
      if (!controller.signal.aborted) {setRows(result.results); setPages(result.total_pages); setError('');}
    })().catch(e => {if (!controller.signal.aborted) {setRows([]); setError(e.message);}}).finally(() => {if (!controller.signal.aborted) setLoadedKey(queryKey);});
    return () => controller.abort();
  }, [page, history, revision, queryKey]);
  return <>
    <Header title="مراجعة حذف الحساب" />
    <section dir="rtl" className="space-y-6 p-4 md:p-6">

    <p>طلب واحد لكل حساب، بمراجعة مستقلة وفحص الالتزامات قبل القرار النهائي.</p>
    <label className="flex gap-2"><input type="checkbox" checked={history} onChange={e => {setHistory(e.target.checked); setPage(1);}} />إظهار الطلبات السابقة</label>
    {!busy && error && <p role="alert">{error}</p>}{busy && <p role="status">جارٍ التحميل…</p>}
    <div className="grid gap-6 xl:grid-cols-2">
      <div className="min-w-0 space-y-3">{!busy && !error && !rows.length && <p>لا توجد طلبات في هذه القائمة.</p>}{!busy && rows.map(row => <button key={row.id} className="w-full rounded-xl border p-4 text-start" onClick={() => {setSelected(row.id); const url = new URL(window.location.href); url.searchParams.set("request", row.id); window.history.replaceState(null, "", url);}}><strong>{row.account_name}</strong><p>{labels[row.status]}</p><p>{row.blockers.length} نوع من الموانع الحالية</p></button>)}
        <div className="flex flex-wrap gap-3"><button disabled={busy || page <= 1} onClick={() => setPage(p => p - 1)}>السابق</button><span>{page} / {pages}</span><button disabled={busy || page >= pages} onClick={() => setPage(p => p + 1)}>التالي</button></div>
      </div>
      {selected && <Decision key={selected} id={selected} onSaved={() => setRevision(value => value + 1)} />}
    </div>
  </section></>;
}

export default function ClosureReview() { return <Suspense fallback={<p>جارٍ التحميل…</p>}><ClosureReviewContent /></Suspense>; }
