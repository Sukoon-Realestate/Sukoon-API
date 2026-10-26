'use client';

import { Header } from '@/components/layout/Header';

import { useCallback, useEffect, useRef, useState } from 'react';
import { apiClient } from '../../lib/api/client';
import { commandSupport, downloadSupportAttachment, fetchSupportDetail, fetchSupportTeam, recoverSupport, SupportAction, SupportCommand, SupportDetail as Ticket } from '../../lib/api/support';

type Pending = { key: string; action: SupportAction };
const names: Record<SupportAction, string> = { reply: 'إرسال الرد', resolve: 'حل الاستفسار العام', claim: 'استلام التذكرة', assign: 'إعادة الإسناد', escalate: 'تصعيد للمشرفين', note: 'حفظ ملاحظة داخلية' };
const control = 'rounded-lg border border-[var(--card-border)] px-4 py-2 disabled:opacity-50';

export default function SupportDetail({ id }: { id: string }) {
  const [ticket, setTicket] = useState<Ticket | null>(null);
  const [team, setTeam] = useState<{id: string; name: string}[]>([]);
  const [reply, setReply] = useState('');
  const [reason, setReason] = useState('');
  const [assignee, setAssignee] = useState('');
  const [pending, setPending] = useState<Pending | null>(null);
  const [storageKey, setStorageKey] = useState('');
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [busy, setBusy] = useState(false);
  const live = useRef(true);
  const load = useCallback((signal?: AbortSignal) => Promise.all([
      fetchSupportDetail(id, signal), fetchSupportTeam(signal), apiClient<{id: string}>('/api/v1/admin/session/', { signal }),
    ]).then(([value, members, session]) => {
    if (!live.current || signal?.aborted) return;
    const key = `support-operation:${session.id}:${id}`;
    setTicket(value); setTeam(members.results); setStorageKey(key);
    const saved = sessionStorage.getItem(key);
    if (saved) {
      try {
        const item = JSON.parse(saved) as Pending;
        if (item.key && item.action in names) setPending(item);
      } catch { setError('تعذّرت قراءة هوية العملية السابقة. راجع التذكرة قبل متابعة الإجراءات.'); }
    } else setPending(null);
  }), [id]);
  useEffect(() => {
    live.current = true;
    const controller = new AbortController();
    void load(controller.signal).catch(e => { if (!controller.signal.aborted) setError(e.message); });
    return () => { live.current = false; controller.abort(); };
  }, [load]);
  const clearPending = () => { sessionStorage.removeItem(storageKey); setPending(null); };
  const send = async (action: SupportAction) => {
    if (!ticket || !storageKey || busy || pending || !ticket.actions[action]) return;
    const body: SupportCommand = { action, expected_revision: ticket.revision, reason: reason.trim() || names[action] };
    if (action === 'reply' || action === 'resolve') body.body = reply.trim();
    if (action === 'resolve') body.acknowledge_resolution = true;
    if (action === 'assign') body.assignee_id = assignee;
    if (['escalate', 'assign', 'note'].includes(action) && !reason.trim()) { setError('اكتب السبب أو الملاحظة قبل الحفظ.'); return; }
    if (['reply', 'resolve'].includes(action) && !reply.trim()) { setError('اكتب ردًا يوضح النتيجة للمستخدم.'); return; }
    if (action === 'assign' && !assignee) { setError('اختر المسؤول التالي.'); return; }
    const original = { key: crypto.randomUUID(), action };
    setBusy(true); setError(''); setNotice('');
    try {
      // Persist only the receipt identity. Private replies and notes stay in memory.
      sessionStorage.setItem(storageKey, JSON.stringify(original)); setPending(original);
      const receipt = await commandSupport(id, body, original.key);
      if (receipt.ticket_id !== id || receipt.revision <= ticket.revision) throw new Error('لم يُؤكد حفظ العملية. استعد نتيجتها الأصلية.');
      if (!live.current) return;
      clearPending(); setReply(''); setReason(''); await load(); setNotice('حُفظ التغيير.');
    } catch (e) { if (live.current) setError(e instanceof Error ? e.message : 'تعذّر تأكيد النتيجة.'); }
    finally { if (live.current) setBusy(false); }
  };
  const recover = async () => {
    if (!pending || busy) return;
    setBusy(true); setError('');
    try {
      let result = await recoverSupport(id, pending.key, pending.action);
      if (result.status === 'unknown') result = await recoverSupport(id, pending.key, pending.action, true);
      if (!live.current) return;
      if (result.status === 'confirmed' || result.status === 'absent_final') {
        clearPending(); await load();
        setNotice(result.status === 'confirmed' ? 'استُعيد إيصال العملية المحفوظة.' : 'أكد السيرفر عدم تنفيذ العملية وأغلق هويتها السابقة. يمكنك مراجعة البيانات والمتابعة.');
      } else setNotice('ما زالت النتيجة قيد الاستعلام.');
    } catch (e) { if (live.current) setError(e instanceof Error ? e.message : 'تعذّر استرجاع النتيجة.'); }
    finally { if (live.current) setBusy(false); }
  };
  return <>
    <Header title={ticket ? `تذكرة ${ticket.reference}` : 'تفاصيل تذكرة الدعم'} />
    <section dir="rtl" className="mx-auto w-full max-w-5xl space-y-5 p-4 sm:p-8">

    {error && <p role="alert">{error}</p>}{notice && <p role="status">{notice}</p>}
    <button className={control} disabled={busy} onClick={() => void load().catch(e => setError(e.message))}>تحديث التذكرة</button>
    {pending && <section className="space-y-2 border rounded-xl p-4"><p>للعملية السابقة نتيجة غير مؤكدة. استعلم عنها قبل إجراء جديد.</p><button className={control} disabled={busy} onClick={() => void recover()}>استعادة نتيجة العملية الأصلية</button></section>}
    {!ticket ? <p role="status">جارٍ تحميل التذكرة…</p> : <>
      <section className="space-y-2 rounded-xl border p-4"><h2 className="font-bold">{ticket.subject}</h2><p>{ticket.user} · {ticket.workspace}</p><p>{ticket.status} · {ticket.escalated ? 'في متابعة المشرفين' : 'متابعة الدعم'}</p><p>المسؤول: {ticket.assignedTo || 'لم تُسند بعد'}</p>
        {ticket.actions.claim && <button className={control} disabled={busy || !!pending} onClick={() => void send('claim')}>{names.claim}</button>}
      </section>
      <section className="space-y-3 rounded-xl border p-4"><h2 className="text-lg font-bold">المحادثة مع المستخدم</h2>
        {ticket.messages.map(message => <article key={message.id} className="rounded-lg border p-3 break-words"><p>{message.sender === 'user' ? 'المستخدم' : 'الدعم'} · {new Date(message.created_at).toLocaleString('ar')}</p><p className="whitespace-pre-wrap">{message.body}</p>{message.attachments.map(file => <p key={file.id}>{file.url ? <button className="underline" onClick={() => void downloadSupportAttachment(file.url, file.name).catch(e => setError(e.message))}>{file.name}</button> : file.name}</p>)}</article>)}
        {ticket.actions.reply && <><label className="block">الرد للمستخدم<textarea className="w-full border rounded p-3" maxLength={4000} value={reply} onChange={e => setReply(e.target.value)} /></label><button className={control} disabled={busy || !!pending} onClick={() => void send('reply')}>{names.reply}</button></>}
        {ticket.actions.resolve && <div><p>حل الاستفسار العام لا يغيّر عقدًا أو فاتورة أو حالة حيازة.</p><button className={control} disabled={busy || !!pending} onClick={() => void send('resolve')}>{names.resolve}</button></div>}
        {!ticket.actions.reply && <p>الرد متاح للمسؤول المخوّل ما دامت التذكرة مفتوحة. راجع الإسناد والحالة الحالية.</p>}
      </section>
      <section className="space-y-3 rounded-xl border p-4"><h2 className="text-lg font-bold">ملاحظات الفريق الداخلية</h2><p>هذه الملاحظات منفصلة عن المحادثة ولا تُعرض للمستخدم.</p>{ticket.internal_notes.map(note => <article key={note.id} className="border rounded p-3 break-words"><p>{note.actor} · {new Date(note.created_at).toLocaleString('ar')}</p><p className="whitespace-pre-wrap">{note.body}</p></article>)}
        {ticket.actions.note && <><label className="block">الملاحظة أو سبب الإجراء<textarea className="w-full border rounded p-3" maxLength={1000} value={reason} onChange={e => setReason(e.target.value)} /></label><button className={control} disabled={busy || !!pending} onClick={() => void send('note')}>{names.note}</button></>}
        {ticket.actions.assign && <div className="flex flex-wrap gap-2"><select aria-label="المسؤول التالي" className={control} value={assignee} onChange={e => setAssignee(e.target.value)}><option value="">اختر المسؤول التالي</option>{team.map(member => <option key={member.id} value={member.id}>{member.name}</option>)}</select><button className={control} disabled={busy || !!pending} onClick={() => void send('assign')}>{names.assign}</button></div>}
        {ticket.actions.escalate && <button className={control} disabled={busy || !!pending} onClick={() => void send('escalate')}>{names.escalate}</button>}
      </section>
      <section className="space-y-2 rounded-xl border p-4"><h2 className="text-lg font-bold">سجل المتابعة والإسناد</h2>{ticket.transitions.map(row => <p key={row.id} className="break-words">{new Date(row.created_at).toLocaleString('ar')} · {row.actor} · {names[row.action as SupportAction] || row.action} · {row.reason}{row.assignee ? ` · ${row.assignee}` : ''}</p>)}</section>
    </>}
  </section></>;
}
