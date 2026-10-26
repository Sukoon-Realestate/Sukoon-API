'use client';

import { Header } from '@/components/layout/Header';

import React, { useState, useEffect, useRef } from 'react';
import { fetchPushCampaigns, previewCampaign, changeCampaign } from '../../lib/api/system';
import { isBackendEnabled } from '../../lib/api/config';
import { PushCampaign } from '../../lib/api/types';
import { ApiError } from '../../lib/api/client';

type Audience = 'all' | 'tenants' | 'landlords' | 'verified' | 'students' | 'companies';
type PreviewIntent = {request_key: string; title: string; body: string; audience: Audience};
const labels: Record<string, string> = {preview: 'بانتظار المراجعة', queued: 'في طابور الإرسال', complete: 'انتهت المعالجة', cancelled: 'أُلغي المتبقي', sending: 'جارٍ الإرسال', accepted_by_provider: 'قبله مزود الإشعارات', delivery_unknown: 'نتيجة التسليم غير مؤكدة', failed: 'تعذّر الإرسال', skipped: 'لم يعد مؤهلًا'};

function CampaignEditor({owner, canOperate}: {owner?: string; canOperate: boolean}) {
  const [audience, setAudience] = useState<Audience>('all');
  const [title, setTitle] = useState('');
  const [body, setBody] = useState('');
  const [campaigns, setCampaigns] = useState<PushCampaign[]>([]);
  const [selected, setSelected] = useState<PushCampaign | null>(null);
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [unknown, setUnknown] = useState(false);
  const [journalError, setJournalError] = useState(false);
  const intent = useRef<string | null>(null);
  const originalPreview = useRef<PreviewIntent | null>(null);
  const generation = useRef(0);
  const replace = (value: PushCampaign) => {
    setSelected(value);
    setCampaigns(previous => [value, ...previous.filter(item => item.id !== value.id)]);
  };

  useEffect(() => {
    const lifecycle = generation;
    const epoch = ++lifecycle.current;
    if (!owner || !canOperate) return;
    const restoreJournal = () => {
    const key = `sokoun-campaign-intent:${owner}`;
    try {
      const stored = sessionStorage.getItem(key);
      if (stored) {
        if (/^[a-f0-9-]{36}$/i.test(stored)) {
          intent.current = stored; // Recover previews written by the older UI.
        } else {
          const value = JSON.parse(stored);
          if (!value || typeof value.request_key !== 'string' || !/^[a-f0-9-]{36}$/i.test(value.request_key) || typeof value.title !== 'string' || typeof value.body !== 'string' || !['all', 'tenants', 'landlords', 'verified', 'students', 'companies'].includes(value.audience)) throw new Error('invalid journal');
          originalPreview.current = value as PreviewIntent;
          intent.current = value.request_key;
          setTitle(value.title); setBody(value.body); setAudience(value.audience);
        }
        setUnknown(true);
      }
    } catch { setJournalError(true); setError('تعذّر قراءة سجل العملية المحلي. راجع الحملات المسجلة قبل بدء إرسال جديد.'); }
    };
    void fetchPushCampaigns().then(items => {
      if (epoch !== generation.current) return;
      restoreJournal(); setLoading(false);
      setCampaigns(items);
      const original = items.find(item => item.request_key === intent.current);
      if (original) { setSelected(original); setTitle(original.title); setBody(original.body); setAudience(original.audience ?? 'all'); setUnknown(false); }
    }).catch(() => { if (epoch === generation.current) { restoreJournal(); setLoading(false); setError('تعذّر تحميل الحملات. أعد التحديث.'); } });
    return () => { lifecycle.current++; };
  }, [owner, canOperate]);

  async function refresh() {
    if (loading || busy) return;
    const epoch = generation.current;
    setBusy(true);
    try {
      const items = await fetchPushCampaigns();
      if (epoch !== generation.current) return;
      setCampaigns(items);
      const original = items.find(item => item.id === selected?.id || item.request_key === intent.current);
      if (original) { setSelected(original); setUnknown(false); setError(''); }
    } catch { if (epoch === generation.current) setError('تعذّر التحديث؛ احتفظ بالعملية الأصلية.'); }
    finally { if (epoch === generation.current) setBusy(false); }
  }

  async function preview() {
    if (!owner || loading || busy || journalError || !isBackendEnabled()) return;
    const epoch = generation.current;
    intent.current ??= crypto.randomUUID();
    const original = originalPreview.current ?? {title, body, audience, request_key: intent.current};
    try { sessionStorage.setItem(`sokoun-campaign-intent:${owner}`, JSON.stringify(original)); }
    catch { setJournalError(true); setError('تعذّر حفظ العملية قبل الإرسال. لم يتم إرسال الطلب.'); return; }
    originalPreview.current = original;
    setBusy(true); setError('');
    try {
      const value = await previewCampaign(original);
      if (epoch === generation.current) { replace(value); setUnknown(false); }
    } catch (failure) {
      if (epoch === generation.current) {
        if (failure instanceof ApiError && [400, 422].includes(failure.status)) {
          setUnknown(false); setError(failure.message);
          intent.current = null; originalPreview.current = null;
          try { sessionStorage.removeItem(`sokoun-campaign-intent:${owner}`); }
          catch { setJournalError(true); }
        } else { setUnknown(true); setError('النتيجة غير مؤكدة. حدّث القائمة لاستعادة المعاينة، أو أعد نفس الطلب.'); }
      }
    }
    finally { if (epoch === generation.current) setBusy(false); }
  }

  async function command(action: 'confirm' | 'cancel') {
    if (!selected || loading || busy || unknown || journalError || !isBackendEnabled()) return;
    const epoch = generation.current;
    setBusy(true); setError('');
    try {
      const result = await changeCampaign(selected, action);
      if (epoch === generation.current) { replace(result); setUnknown(false); }
    } catch { if (epoch === generation.current) { setUnknown(true); setError('تعذّر تأكيد نتيجة العملية. حدّث الحملة الأصلية قبل أي إجراء جديد.'); } }
    finally { if (epoch === generation.current) setBusy(false); }
  }

  function reset() {
    if (loading || busy || unknown || journalError) return;
    try { if (owner) sessionStorage.removeItem(`sokoun-campaign-intent:${owner}`); }
    catch { setJournalError(true); setError('تعذّر تحديث سجل العملية المحلي. لم تبدأ حملة جديدة.'); return; }
    intent.current = null; originalPreview.current = null; setSelected(null); setTitle(''); setBody(''); setError('');
  }

  function review(campaign: PushCampaign) {
    if (loading || busy || unknown || !owner) return;
    const original = {request_key: campaign.request_key!, title: campaign.title, body: campaign.body, audience: campaign.audience ?? 'all'} as PreviewIntent;
    try { sessionStorage.setItem(`sokoun-campaign-intent:${owner}`, JSON.stringify(original)); }
    catch { setJournalError(true); setError('تعذّر حفظ الحملة المحددة للاستعادة؛ المراجعة فقط متاحة.'); }
    intent.current = original.request_key; originalPreview.current = original;
    setSelected(campaign); setTitle(campaign.title); setBody(campaign.body); setAudience(original.audience);
  }

  if (!canOperate) return <p className="p-6">إدارة الحملات متاحة لمالك النظام المخوّل.</p>;

  const button = 'min-h-12 rounded-xl border border-[var(--card-border)] px-4 py-3 disabled:opacity-50';
  const field = 'w-full p-3 rounded-xl border border-[var(--card-border)] bg-[var(--input-bg)] text-[var(--foreground)]';
  return <>
    <Header title="حملات الإشعارات" />
    <section dir="rtl" className="flex-1 flex flex-col p-4 md:p-6 space-y-4">
    <p>راجع الجمهور والنص، ثم أكّد الإرسال وتابع النتيجة.</p>
    <div className="admin-page-body space-y-6">
      {loading && <p role="status">جارٍ تحميل الحملات واستعادة العملية السابقة…</p>}
      {error && <p role="alert">{error}</p>}
      {!isBackendEnabled() && <p role="status">المعاينة التجريبية لا ترسل إشعارات.</p>}
      <div className="grid gap-6 lg:grid-cols-2">
        <section aria-label="إنشاء ومراجعة حملة" className="rounded-2xl border border-[var(--card-border)] bg-[var(--card-bg)] p-6 space-y-4">
          <fieldset disabled={loading || busy || !!selected || unknown || journalError} className="space-y-4">
            <label className="block">الجمهور<select className={field} value={audience} onChange={event => setAudience(event.target.value as Audience)}>
              <option value="all">كل الموافقين على العروض</option><option value="tenants">المستأجرون</option><option value="landlords">الملاك</option><option value="verified">الحسابات الموثقة</option><option value="students">الطلاب</option><option value="companies">أعضاء الشركات النشطون</option>
            </select></label>
            <label className="block">عنوان الإشعار<input className={field} maxLength={180} value={title} onChange={event => setTitle(event.target.value)} /></label>
            <label className="block">نص الإشعار<textarea className={field} maxLength={2000} rows={5} value={body} onChange={event => setBody(event.target.value)} /></label>
          </fieldset>
          {!selected && <button className={button} disabled={loading || busy || journalError || !title.trim() || !body.trim() || !isBackendEnabled()} onClick={preview}>{busy ? 'جارٍ التحميل…' : unknown ? 'إعادة طلب المعاينة الأصلية' : 'معاينة الجمهور'}</button>}
          {selected && <div className="space-y-3" aria-live="polite">
            <p>{labels[selected.state ?? ''] ?? 'الحالة غير متاحة'} · {selected.recipientCount} مستلم</p>
            <p>{selected.receiptCount ?? 0} إيصال مساحة · {selected.pushAccountCount ?? 0} حساب مؤهل لتنبيه Push واحد.</p><ul>{Object.entries(selected.workspaceCounts ?? {}).map(([space, count]) => <li key={space}>{({individual: "الأفراد", owner: "الملاك", student: "الطلاب", company: "الشركات", account: "الحساب"} as Record<string,string>)[space] || space}: {count}</li>)}</ul><p>تُراجع الأهلية والتفضيلات مرة أخرى قبل الإرسال. تبقى إيصالات التطبيق مستقلة عن Push؛ قبول المزود لا يثبت القراءة.</p>
            {selected.state === 'preview' && <button className={button} disabled={loading || busy || unknown || journalError || !selected.can_confirm} onClick={() => command('confirm')}>تأكيد وإضافة للطابور</button>}
            {selected.state === 'preview' && !selected.can_confirm && <p>الإرسال غير مفعّل في هذه البيئة.</p>}
            {['preview', 'queued'].includes(selected.state ?? '') && <button className={button} disabled={loading || busy || unknown || journalError} onClick={() => command('cancel')}>إلغاء ما لم يبدأ إرساله</button>}
          </div>}
          <div className="flex flex-wrap gap-2"><button className={button} disabled={loading || busy} onClick={refresh}>تحديث واستعادة الحالة</button><button className={button} disabled={loading || busy || unknown || journalError} onClick={reset}>حملة جديدة</button></div>
        </section>
        <section aria-label="سجل الحملات" className="rounded-2xl border border-[var(--card-border)] bg-[var(--card-bg)] p-6 space-y-4">
          <h2>سجل الحملات</h2>
          {!campaigns.length && <p>لا توجد حملات مسجلة.</p>}
          {campaigns.map(campaign => <article key={campaign.id} className="border-b border-[var(--divider)] pb-4 space-y-2">
            <h3>{campaign.title}</h3><p className="whitespace-pre-wrap break-words">{campaign.body}</p>
            <p>{labels[campaign.state ?? ''] ?? 'غير متاح'} · {campaign.recipientCount} مستلم</p>
            <ul>{Object.entries(campaign.deliveryCounts ?? {}).map(([state, count]) => <li key={state}>{labels[state] ?? state}: {count}</li>)}</ul>
            <button className={button} disabled={loading || busy || unknown} onClick={() => review(campaign)}>مراجعة الحملة</button>
          </article>)}
        </section>
      </div>
    </div>
  </section></>;
}

export default function PushCampaigns(props: {owner?: string; canOperate: boolean}) {
  return <CampaignEditor key={`${props.owner || ""}:${props.canOperate}`} {...props} />;
}
