'use client';

import { useEffect, useRef, useState } from 'react';
import { PolicyStatus } from './PolicyStatus';
import { PolicyMedia } from './PolicyMedia';
import { Header } from '@/components/layout/Header';
import { ApiError } from '@/lib/api/client';
import { fetchPolicyCases, fetchPolicyCase, reviewPolicyCase, type PolicyCase, type PolicyAction, type PolicyCommand } from '@/lib/api/chatPolicy';

const labels: Record<string, string> = { warning: 'تنبيه', review: 'مراجعة دون إيقاف', pending_review: 'إيقاف مؤقت للمراجعة', permanent: 'إيقاف بقرار الإدارة', released: 'تم رفع الإيقاف', dismissed: 'أُغلق دون مخالفة' };
const actions: Record<PolicyAction, string> = { dismiss: 'رفض البلاغ', release: 'رفع الإيقاف', keep_restricted: 'استمرار الإيقاف للمراجعة', ban: 'إيقاف دائم بقرار الإدارة' };

export default function ChatPolicyPage() {
  const [items, setItems] = useState<PolicyCase[]>([]);
  const [selected, setSelected] = useState<PolicyCase | null>(null);
  const [page, setPage] = useState(1);
  const [more, setMore] = useState(false);
  const [listLoading, setListLoading] = useState(true);
  const [refresh, setRefresh] = useState(0);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [notes, setNotes] = useState('');
  const [action, setAction] = useState<PolicyAction>('dismiss');
  const [confirmed, setConfirmed] = useState(false);
  const [pending, setPending] = useState<PolicyCommand | null>(null);
  const generation = useRef(0);
  useEffect(() => {
    const current = ++generation.current;
    setListLoading(true); setError('');
    fetchPolicyCases(page).then(value => { if (current === generation.current) { setItems(value.results); setMore(Boolean(value.next)); } }).catch(() => { if (current === generation.current) setError('تعذر تحميل المراجعات. تحقق من الاتصال وصلاحية المراجع.'); }).finally(() => { if (current === generation.current) setListLoading(false); });
    return () => { generation.current++; };
  }, [page, refresh]);
  async function open(id: string) {
    if (busy || (pending && selected?.id !== id)) return;
    setBusy(true); setError('');
    try { setSelected(await fetchPolicyCase(id)); if (!pending) { setNotes(''); setConfirmed(false); } }
    catch { setError('تعذر تحميل تفاصيل الحالة.'); }
    finally { setBusy(false); }
  }
  async function decide() {
    if (!selected || busy || (!pending && (notes.trim().length < 10 || !confirmed))) return;
    const command = pending ?? { client_id: crypto.randomUUID(), expected_revision: selected.revision, action, notes: notes.trim() };
    setPending(command); setBusy(true); setError('');
    try {
      const result = await reviewPolicyCase(selected.id, command);
      setSelected(result); setItems(old => old.map(item => item.id === result.id ? result : item));
      setPending(null); setConfirmed(false); setNotes('');
    } catch (failure) {
      if (failure instanceof ApiError && [400, 403, 404, 409, 422].includes(failure.status)) {
        setPending(null); setSelected(null); setConfirmed(false);
        setError('تغيّرت الحالة. حدّثها وراجع القرار قبل إعادة الإرسال.');
      } else setError('النتيجة غير مؤكدة. حدّث الحالة أو أعد نفس العملية؛ لا تصدر قرارًا جديدًا قبل التحقق.');
    } finally { setBusy(false); }
  }
  return <div className="flex-1" dir="rtl">
    <Header title="مراجعة محادثات التأجير" subtitle="تحقق من السياق والفاعل والاعتراض قبل اتخاذ القرار" />
    <PolicyStatus />
    <main className="p-4 md:p-8 grid gap-6 lg:grid-cols-2">
      {error && <p role="alert" className="lg:col-span-2 text-red-600">{error}</p>}
      <section aria-label="قائمة المراجعات" className="space-y-3">
        {listLoading && <p role="status">جارٍ تحميل المراجعات…</p>}
        {!listLoading && !error && items.length === 0 && <p>لا توجد حالات لعرضها.</p>}
        <button className="min-h-12 underline" disabled={busy || listLoading} onClick={() => setRefresh(value => value + 1)}>تحديث قائمة المراجعات</button>
        {items.map(item => <button disabled={busy || listLoading || (Boolean(pending) && selected?.id !== item.id)} key={item.id} onClick={() => void open(item.id)} className="w-full border rounded-xl p-4 text-start min-h-12">
          <strong>{labels[item.state] ?? item.state}</strong>
          <p>{new Date(item.created_at).toLocaleString('ar-EG')}</p>
          {item.appeal_submitted && <p>يوجد اعتراض</p>}
          {item.review_overdue && <p className="text-red-600">تجاوزت ٤٨ ساعة — أولوية للمراجعة</p>}
        </button>)}
        <div className="flex gap-4"><button className="min-h-12" disabled={busy || listLoading || Boolean(pending) || page === 1} onClick={() => setPage(page - 1)}>السابق</button><button className="min-h-12" disabled={busy || listLoading || Boolean(pending) || !more} onClick={() => setPage(page + 1)}>التالي</button></div>
      </section>
      {selected && <section aria-label="الأدلة والقرار" className="space-y-4 border rounded-xl p-4 break-words">
        <h2 className="font-bold">{labels[selected.state] ?? selected.state}</h2>
        <p>الفاعل: <bdi>{selected.subject_id}</bdi></p>
        <p>رقم الهاتف وحده أو تنسيق زيارة ليس مخالفة. رفض طلب الطرف الآخر لا يبرر إيقاف الرافض.</p>
        {selected.evidence?.messages?.map(message => <article className="border rounded-lg p-3" key={message.message_id}>
          <p className="whitespace-pre-wrap" dir="auto">{message.text}</p>
          {message.media.map(media => <div key={media.source}><p dir="auto" className="whitespace-pre-wrap">{media.uncertain ? 'استخراج غير مؤكد: ' : 'نص مستخرج: '}{media.text}</p><PolicyMedia caseId={selected.id} mediaId={media.source} kind={media.kind} /></div>)}
        </article>)}
        {selected.evidence?.verdict?.evidence.map((e, i) => <blockquote key={i} className="border-s-4 ps-3" dir="auto">{e.quote}</blockquote>)}
        {selected.appeal && <div><h3 className="font-bold">اعتراض المستخدم</h3><p dir="auto" className="whitespace-pre-wrap">{selected.appeal.text}</p></div>}
        {selected.actions?.map(item => <p key={item.revision}>{actions[item.action as PolicyAction]} — {item.notes}</p>)}
        <button className="min-h-12 underline" disabled={busy} onClick={() => void open(selected.id)}>تحديث الحالة والأدلة</button>
        <label className="block">القرار<select className="block border rounded p-3 w-full" disabled={busy || Boolean(pending)} value={action} onChange={e => { setAction(e.target.value as PolicyAction); setConfirmed(false); }}>{Object.entries(actions).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label>
        <label className="block">سبب القرار<textarea className="block border rounded p-3 w-full" rows={4} minLength={10} maxLength={3000} value={notes} disabled={busy || Boolean(pending)} onChange={e => setNotes(e.target.value)} /></label>
        <label className="flex gap-3 items-center min-h-12"><input type="checkbox" checked={confirmed} disabled={busy || Boolean(pending)} onChange={e => setConfirmed(e.target.checked)} />راجعت الأدلة والاعتراض وأؤكد هذا القرار</label>
        <button className="min-h-12 border rounded px-6" disabled={busy || (!pending && (!confirmed || notes.trim().length < 10))} onClick={() => void decide()}>{busy ? 'جارٍ الحفظ…' : pending ? 'إعادة نفس العملية' : 'تسجيل القرار'}</button>
        <p>رفع الإيقاف يزيل أثر هذه الحالة فقط. تظل أي قيود أخرى فعالة، وتظل الالتزامات القائمة متاحة.</p>
      </section>}
    </main>
  </div>;
}
