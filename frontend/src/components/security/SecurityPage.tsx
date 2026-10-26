'use client';

import { Header } from '@/components/layout/Header';

import { useCallback, useEffect, useState } from 'react';
import { apiClient } from '../../lib/api/client';
import { fetchSecurity, fetchRecoveryQueue, requestRecovery, respondRecovery, enrollFactor, beginInitialEnrollment, confirmFactor, SecurityStatus, Enrollment, RecoveryRequest } from '../../lib/api/security';
import { RecoveryReview } from './RecoveryReview';
import { StaffIdentitySetup } from './StaffIdentitySetup';

const statuses: Record<string, string> = { pending: 'بانتظار المراجعة المستقلة', approved: 'بانتظار ربط العامل الجديد', rejected: 'مرفوض؛ الإجراءات الحساسة ما زالت موقوفة', information_requested: 'معلومات مطلوبة للمراجعة', completed: 'اكتمل ربط العامل الجديد' };

export default function SecurityPage() {
  const [status, setStatus] = useState<SecurityStatus | null>(null);
  const [queue, setQueue] = useState<RecoveryRequest[]>([]);
  const [canReview, setCanReview] = useState(false);
  const [reason, setReason] = useState('');
  const [enrollment, setEnrollment] = useState<Enrollment | null>(null);
  const [code, setCode] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const load = useCallback((signal?: AbortSignal) =>
    Promise.all([fetchSecurity(signal), apiClient<{ role: string }>('/api/v1/admin/session/', { signal })]).then(async ([value, session]) => {
      const review = ['system_owner', 'security_recovery_reviewer'].includes(session.role);
      const items = review ? await fetchRecoveryQueue(signal) : { results: [] };
      if (signal?.aborted) return;
      setStatus(value); setCanReview(review); setQueue(items.results);
      if (value.configured || (value.recovery && value.recovery.status !== 'approved')) { setEnrollment(null); setCode(''); }
    }), []);
  useEffect(() => {
    const controller = new AbortController();
    void load(controller.signal).catch(failure => { if (!controller.signal.aborted) setError(failure instanceof Error ? failure.message : 'تعذّر تحميل أمان الحساب.'); });
    return () => controller.abort();
  }, [load]);
  useEffect(() => {
    if (!enrollment) return;
    const timer = window.setTimeout(() => {
      setEnrollment(null); setCode('');
      setError('انتهت مهلة الربط. حدّث الحالة ثم اطلب إذن الربط مجددًا.');
    }, Math.max(0, Date.parse(enrollment.expires_at) - Date.now()));
    return () => window.clearTimeout(timer);
  }, [enrollment]);
  const perform = async (command: () => Promise<unknown>) => {
    if (busy) return; setBusy(true); setError('');
    try { await command(); await load(); }
    catch (failure) { setError(failure instanceof Error ? failure.message : 'تعذّر تأكيد النتيجة. حدّث الحالة قبل المتابعة.'); }
    finally { setBusy(false); }
  };
  const recovery = status?.recovery;
  return <>
    <Header title="أمان الحساب والتحقق للموظفين" />
    <section dir="rtl" className="mx-auto w-full max-w-3xl space-y-6 p-4 sm:p-8">

    <p>تتوقف الإجراءات الحساسة أثناء الاستعادة. تبقى السجلات والمتابعة متاحة، ولا يؤدي الربط الجديد إلى تنفيذ عملية مالية معلّقة.</p>
    {error && <p role="alert">{error}</p>}
    <button className="border rounded px-4 py-2" disabled={busy} onClick={() => void perform(() => load())}>تحديث الحالة</button>
    {!status ? <p role="status">جارٍ تحميل حالة الأمان…</p> : <>
      <p>{status.configured ? 'عامل التحقق مربوط' : 'عامل التحقق يحتاج إلى ربط'}</p>
      {!status.configured && !status.initial_setup.requires_recovery && <section className="space-y-3 rounded-xl border p-4">
        <h2 className="font-bold">الربط الأول لتطبيق التحقق</h2>
        <p>{status.initial_setup.identity_documented ? 'تم تسجيل التحقق المستقل من هويتك. أضف العامل إلى تطبيقك ثم أكّد رمزه خلال خمس دقائق.' : 'يلزم توثيق هويتك من مالك نظام مخوّل عبر مقابلة مستقلة قبل الربط. بيانات الدخول والبريد وحدهما لا يكفيان.'}</p>
        {!enrollment && <button className="rounded border px-4 py-2" disabled={busy || !status.initial_setup.available} onClick={() => void perform(async () => setEnrollment(await beginInitialEnrollment()))}>بدء أو استعادة الربط الأول</button>}
      </section>}
      {status.restricted && <p role="status">الإجراءات الحساسة موقوفة. الإيقاف الإداري والصلاحيات تُراجع بصورة مستقلة.</p>}
      {recovery && recovery.status !== 'completed' && recovery.review_available === false && <p role="status">لا يتوفر مراجع مستقل مجهّز لهذا الطلب حاليًا. يبقى الطلب معلقًا والإجراء الحساس متوقفًا حتى تتوفر المراجعة المخوّلة.</p>}
      {recovery && <section className="space-y-2 rounded-xl border p-4"><h2 className="font-bold">طلب الاستعادة</h2><p>{statuses[recovery.status] || recovery.status}</p><p>{recovery.decision_reason}</p><ol>{recovery.decisions.map(decision => <li key={decision.revision}>{decision.reason} — {new Date(decision.created_at).toLocaleString('ar')}</li>)}</ol></section>}
      {(status.configured || status.initial_setup.requires_recovery) && (!recovery || ['completed', 'rejected', 'information_requested'].includes(recovery.status)) && <form className="space-y-3" onSubmit={event => { event.preventDefault(); void perform(() => recovery && recovery.status !== 'completed' ? respondRecovery(recovery, reason) : requestRecovery(reason)); }}>
        <label className="block">سبب طلب استعادة العامل<textarea required maxLength={1000} className="block w-full border rounded p-3" value={reason} onChange={e => setReason(e.target.value)} /></label>
        <p>يتطلب الطلب تحققًا بشريًا مستقلًا. ستتوقف الأذونات السابقة والإجراءات الحساسة فور تسجيله.</p>
        <button className="border rounded px-4 py-2" disabled={busy}>{recovery && recovery.status !== 'completed' ? 'إرسال المعلومات للمراجعة' : 'تسجيل طلب الاستعادة'}</button>
      </form>}
      {recovery?.status === 'approved' && !enrollment && <button className="border rounded px-4 py-2" disabled={busy} onClick={() => void perform(async () => setEnrollment(await enrollFactor(recovery.id)))}>ربط تطبيق التحقق بنفسي</button>}
      {enrollment && <form className="space-y-3 rounded-xl border p-4" onSubmit={event => { event.preventDefault(); void perform(async () => { await confirmFactor(enrollment.id, code); setCode(''); setEnrollment(null); }); }}>
        <p>أضف المفتاح إلى تطبيق التحقق الخاص بك، ثم أدخل رمزه. لا تشارك المفتاح مع المراجع.</p>
        <p dir="ltr" className="break-all font-mono select-all">{enrollment.secret}</p>
        <p>صالح حتى {new Date(enrollment.expires_at).toLocaleTimeString('ar')}</p>
        <label className="block">رمز العامل الجديد<input required inputMode="numeric" autoComplete="one-time-code" minLength={6} maxLength={6} className="block w-full border rounded p-3" value={code} onChange={e => setCode(e.target.value)} /></label>
        <button className="border rounded px-4 py-2" disabled={busy}>تأكيد الربط</button>
      </form>}
      {canReview && <section className="space-y-4"><h2 className="text-xl font-bold">طلبات المراجعة المستقلة</h2>{queue.length === 0 && <p>لا توجد طلبات متاحة لك للمراجعة.</p>}{queue.map(item => <RecoveryReview key={`${item.id}:${item.revision}`} item={item} onSaved={() => load()} />)}</section>}
      {status.can_document_staff_identity && <StaffIdentitySetup enabled={status.configured && !status.restricted} />}
    </>}
  </section></>;
}
