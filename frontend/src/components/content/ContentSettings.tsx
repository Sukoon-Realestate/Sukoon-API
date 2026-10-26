'use client';

import { Header } from '@/components/layout/Header';
import React, { useEffect, useRef, useState } from 'react';
import { apiClient, ApiError } from '../../lib/api/client';
import { isBackendEnabled } from '../../lib/api/config';
import { ContentItem, ContentSchema, ContentValues, ContentIntent, ContentPage, contentSchema, contentList, contentDetail, contentTitle, saveContent, recoverContent } from '../../lib/api/content';
import ContentFields from './ContentFields';
import AdminLink from '@/components/ui/AdminLink';

function formValues(schema: ContentSchema, item: ContentItem | null): ContentValues {
  const values: ContentValues = {};
  for (const field of schema.fields) {
    let value = item?.values[field.name] ?? (field.type === 'boolean' ? true : field.type === 'integer' && !field.nullable ? 0 : '');
    if (field.type === 'datetime' && typeof value === 'string' && value) {
      const date = new Date(value);
      if (!Number.isNaN(date.getTime())) value = new Date(date.getTime() - date.getTimezoneOffset() * 60000).toISOString().slice(0, 16);
    }
    values[field.name] = value;
  }
  return values;
}
const button = 'rounded-lg border px-4 py-3 disabled:opacity-50';

export default function ContentSettings() {
  const [schemas, setSchemas] = useState<ContentSchema[]>([]);
  const [kind, setKind] = useState('pages');
  const [page, setPage] = useState<ContentPage | null>(null);
  const [item, setItem] = useState<ContentItem | null>(null);
  const [values, setValues] = useState<ContentValues>({});
  const [reason, setReason] = useState('');
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);
  const [pending, setPending] = useState<ContentIntent | null>(null);
  const [journal, setJournal] = useState('');
  const [storageFailed, setStorageFailed] = useState(false);
  const [canEdit, setCanEdit] = useState(false);
  const [blockingReason, setBlockingReason] = useState('');
  const active = useRef(false);
  const running = useRef(false);
  const generation = useRef(0);
  const abort = useRef<AbortController | null>(null);
  const schema = schemas.find(value => value.kind === kind);
  const dirty = !!schema && page !== null && !loading && (reason.trim() !== '' || JSON.stringify(values) !== JSON.stringify(formValues(schema, item)));
  const mayLeaveForm = () => !dirty || pending !== null || window.confirm('توجد تعديلات لم تُحفظ. هل تريد تركها والانتقال؟');

  useEffect(() => {
    const warn = (event: BeforeUnloadEvent) => {
      if (dirty && !pending) { event.preventDefault(); event.returnValue = ''; }
    };
    window.addEventListener('beforeunload', warn);
    return () => window.removeEventListener('beforeunload', warn);
  }, [dirty, pending]);

  useEffect(() => {
    active.current = true;
    const controller = new AbortController();
    async function init() {
      if (!isBackendEnabled()) throw new Error('إدارة المحتوى تتطلب اتصالًا فعليًا بالخادم.');
      const [session, response] = await Promise.all([apiClient<{id: string; role: string}>('/api/v1/admin/session/', {signal: controller.signal}), contentSchema(controller.signal)]);
      if (!active.current || controller.signal.aborted) return;
      if (session.role !== 'system_owner') throw new Error('هذه الصفحة تتطلب صلاحية مالك النظام الحالية.');
      const key = `sokoun-content-intent:${session.id}`;
      setSchemas(response.catalogs); setJournal(key);
      setCanEdit(response.can_edit === true); setBlockingReason(response.blocking_reason);
      let initialKind = response.catalogs[0].kind;
      try {
        const saved = sessionStorage.getItem(key);
        if (saved) {
          const intent: ContentIntent = JSON.parse(saved);
          if (!/^[a-f0-9-]{36}$/i.test(intent.key) || !response.catalogs.some(c => c.kind === intent.kind) || !(intent.identity === null || typeof intent.identity === 'string')) throw new Error('invalid journal');
          setPending(intent); setKind(intent.kind);
          initialKind = intent.kind;
        }
      } catch { setStorageFailed(true); throw new Error('تعذرت قراءة سجل الحفظ المحلي. راجع المحتوى المسجل قبل إجراء تعديل جديد.'); }
      await load(response.catalogs.find(value => value.kind === initialKind)!);
    }
    void init().catch(e => { if (active.current && !controller.signal.aborted) setError(e.message); }).finally(() => {if (active.current && !controller.signal.aborted) setLoading(false);});
    return () => { active.current = false; controller.abort(); abort.current?.abort(); };
  }, []);

  async function load(target: ContentSchema, pageNumber = 1, identity?: string | null) {
    const epoch = ++generation.current;
    abort.current?.abort(); const controller = new AbortController(); abort.current = controller;
    setLoading(true); setError('');
    try {
      const result = await contentList(target.kind, pageNumber, controller.signal);
      const id = identity === undefined ? result.results[0]?.id : identity;
      const selected = id ? await contentDetail(target.kind, id, controller.signal) : null;
      if (!active.current || controller.signal.aborted || epoch !== generation.current) return;
      setKind(target.kind); setPage(result); setItem(selected); setValues(formValues(target, selected)); setReason('');
    } catch (e) {if (active.current && !controller.signal.aborted && epoch === generation.current) setError(e instanceof Error ? e.message : 'تعذر تحميل المحتوى.');}
    finally {if (active.current && !controller.signal.aborted && epoch === generation.current) setLoading(false);}
  }

  async function save(event: React.FormEvent) {
    event.preventDefault();
    if (!schema || pending || running.current || loading || storageFailed || !journal || !canEdit || !item && schema.allow_create === false) return;
    running.current = true; setBusy(true); setError(''); setNotice('');
    let attempted = false;
    try {
      const intent: ContentIntent = {key: crypto.randomUUID(), kind, identity: item?.id ?? null};
      sessionStorage.setItem(journal, JSON.stringify(intent)); setPending(intent);
      const payload = {...values};
      for (const field of schema.fields) {
        if (field.type === 'datetime') payload[field.name] = values[field.name] ? new Date(String(values[field.name])).toISOString() : null;
        if (['date', 'decimal'].includes(field.type) && values[field.name] === '') payload[field.name] = null;
        if (field.type === 'integer' && field.nullable && values[field.name] === '') payload[field.name] = null;
      }
      attempted = true;
      const result = await saveContent(intent, item?.revision ?? 0, payload, reason);
      if (!active.current) return;
      const versionConfirmed = schema.revision_type === 'opaque'
        ? typeof result.revision === 'string' && !!result.revision && result.revision !== item?.revision
        : typeof result.revision === 'number' && result.revision === Number(item?.revision ?? 0) + 1;
      if (!result.id || (item && result.id !== item.id) || !versionConfirmed) throw new Error('لم تؤكد الاستجابة إصدار المحتوى المحفوظ.');
      sessionStorage.removeItem(journal); setPending(null); setNotice('تم حفظ المحتوى وإصداره.');
      await load(schema, page?.page ?? 1, result.id);
    } catch (e) {
      if (active.current) {
        if (e instanceof ApiError && e.status < 500) { sessionStorage.removeItem(journal); setPending(null); }
        if (!attempted) setStorageFailed(true);
        setError(e instanceof Error ? e.message : 'لم تتأكد نتيجة الحفظ.');
      }
    } finally { running.current = false; if (active.current) setBusy(false); }
  }
  async function recover() {
    if (!pending || running.current) return;
    running.current = true; setBusy(true); setError('');
    try {
      const original = pending;
      const result = await recoverContent(original);
      if (!active.current) return;
      if (!['confirmed', 'absent_final'].includes(result.status)) throw new Error('النتيجة ما زالت معلقة.');
      sessionStorage.removeItem(journal); setPending(null);
      setNotice(result.status === 'confirmed' ? 'استعيدت نتيجة الحفظ الأصلية.' : 'لم يُنفذ الحفظ السابق. راجع البيانات قبل حفظ جديد.');
      const target = schemas.find(value => value.kind === original.kind)!;
      await load(target, 1, result.receipt?.id ?? original.identity);
    } catch (e) {if (active.current) setError(e instanceof Error ? e.message : 'تعذر استرجاع نتيجة الحفظ.');}
    finally {running.current = false; if (active.current) setBusy(false);}
  }
  const disabled = busy || loading || pending !== null || storageFailed;
  return <>
    <Header title="محتوى التطبيق والإعدادات" />
    <section dir="rtl" className="mx-auto w-full max-w-6xl space-y-6 p-4 sm:p-6">

    <p>تحديث المحتوى والكتالوجات المعتمدة. تُحفظ النسخ السابقة في سجل التغيير.</p>
    {schemas.length > 0 && <AdminLink className="inline-block underline" href="/roles">إدارة الأدوار والصلاحيات</AdminLink>}
    {error && <p role="alert" className="rounded-lg border border-red-400 p-3">{error}</p>}
    {notice && <p role="status">{notice}</p>}
    {!canEdit && blockingReason && <p role="status">{blockingReason} <AdminLink className="underline" href="/security">أمان الحساب</AdminLink></p>}
    {pending && <section className="space-y-3 rounded-xl border p-4"><p>هناك عملية حفظ لم تتأكد نتيجتها. استعلم عنها قبل تعديل آخر.</p><button className={button} disabled={busy} onClick={() => void recover()}>استعادة نتيجة الحفظ</button></section>}
    <nav aria-label="مجموعات المحتوى" className="flex flex-wrap gap-2">{schemas.map(target => <button key={target.kind} className={button} aria-pressed={kind === target.kind} disabled={disabled} onClick={() => {if (mayLeaveForm()) {setNotice(''); void load(target);}}}>{target.label}</button>)}</nav>
    {loading && <p role="status">جارٍ تحميل المحتوى…</p>}
    {schema && page && <div className="grid min-w-0 gap-6 lg:grid-cols-[240px_minmax(0,1fr)]">
      <aside className="min-w-0 space-y-3">
        <h2 className="text-lg font-bold">{schema.label} ({page.count})</h2>
        <div className="flex flex-wrap gap-2">
        <button className={button} disabled={disabled || !canEdit || schema.allow_create === false} onClick={() => {if (mayLeaveForm()) {setItem(null); setValues(formValues(schema, null)); setReason(''); setNotice('');}}}>إضافة محتوى</button>
        <button className={button} disabled={busy} onClick={() => {if (mayLeaveForm()) void load(schema, page.page, item?.id ?? null);}}>تحديث القائمة</button>
        </div>
        {!page.results.length && <p>لا يوجد محتوى في هذه المجموعة.</p>}
        <ul className="space-y-2">{page.results.map(row => <li key={row.id}><button className={`${button} w-full break-words text-start`} disabled={disabled} aria-pressed={item?.id === row.id} onClick={() => {if (mayLeaveForm()) void load(schema, page.page, row.id);}}>{contentTitle(row)}{(row.values.active === false || row.values.is_active === false) && ' — متوقف'}<span className="block text-xs opacity-70" dir="ltr">{row.id}</span></button></li>)}</ul>
        <div className="flex flex-wrap gap-2"><button className={button} disabled={disabled || page.page <= 1} onClick={() => {if (mayLeaveForm()) void load(schema, page.page - 1);}}>السابق</button><button className={button} disabled={disabled || page.page >= page.total_pages} onClick={() => {if (mayLeaveForm()) void load(schema, page.page + 1);}}>التالي</button></div>
      </aside>
      <section className="min-w-0 space-y-5 rounded-xl border p-4">
        <h2 className="break-words text-lg font-bold">{item ? `${contentTitle(item)} — النسخة ${item.revision}` : 'محتوى جديد'}</h2>
        {schema.guidance && <p className="whitespace-pre-wrap">{schema.guidance}</p>}
        <form onSubmit={save} className="min-w-0 space-y-4">
          <ContentFields fields={schema.fields} values={values} labels={item?.relation_labels} existing={item !== null} disabled={disabled || !canEdit || !item && schema.allow_create === false} change={(name, value) => setValues(old => ({...old, [name]: value}))} />
          <label className="block space-y-2"><span>سبب التغيير</span><textarea className="block w-full rounded-lg border bg-transparent p-3" required maxLength={500} disabled={disabled} value={reason} onChange={e => setReason(e.target.value)} /></label>
          <button className={button} disabled={disabled || !canEdit || !reason.trim() || !item && schema.allow_create === false}>{busy ? 'جارٍ الحفظ…' : 'حفظ المحتوى'}</button>
        </form>
        {!!item?.history?.length && <section className="space-y-3"><h3 className="font-bold">سجل التغيير</h3>{item.history.map(event => <details key={event.revision} className="rounded-lg border p-3"><summary>النسخة {event.revision} — {event.reason}</summary><p>{new Date(event.created_at).toLocaleString('ar-EG')}</p><dl className="space-y-3">{schema.fields.filter(field => event.before.values?.[field.name] !== event.after.values[field.name]).map(field => <div key={field.name}><dt className="font-bold">{field.label}</dt><dd className="whitespace-pre-wrap break-words">قبل: {String(event.before.values?.[field.name] ?? '—')}<br />بعد: {String(event.after.values[field.name] ?? '—')}</dd></div>)}</dl></details>)}</section>}
      </section>
    </div>}
  </section></>;
}
