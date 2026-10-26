'use client';

import { useEffect, useState } from 'react';
import {
  beginIdentityReview, documentStaffIdentity, fetchStaffIdentities, verifyReview,
  type Challenge, type StaffIdentity, type StaffIdentityBody,
} from '../../lib/api/security';

const initialBody: StaffIdentityBody = {
  person_reference: '', evidence_reference: '', known_channel_reference: '',
  verification_method: 'known_channel_video', identity_matched: false,
};

export function StaffIdentitySetup({ enabled }: { enabled: boolean }) {
  const [items, setItems] = useState<StaffIdentity[]>([]);
  const [selected, setSelected] = useState('');
  const [body, setBody] = useState(initialBody);
  const [challenge, setChallenge] = useState<Challenge | null>(null);
  const [code, setCode] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [loaded, setLoaded] = useState(false);
  async function refresh(signal?: AbortSignal) {
    const result = await fetchStaffIdentities(signal);
    if (signal?.aborted) return;
    setItems(result.results); setLoaded(true);
  }
  useEffect(() => {
    const controller = new AbortController();
    void refresh(controller.signal).catch(failure => {
      if (!controller.signal.aborted) setError(failure instanceof Error ? failure.message : 'تعذّر تحميل حالة الموظفين.');
    });
    return () => controller.abort();
  }, []);
  const item = items.find(value => value.user_id === selected);
  function change(update: Partial<StaffIdentityBody>) {
    setBody(value => ({ ...value, ...update })); setChallenge(null); setCode('');
  }
  async function submit(event: React.FormEvent) {
    event.preventDefault();
    if (busy || !enabled || !item || item.documented || item.recovery_pending) return;
    setBusy(true); setError('');
    try {
      if (!challenge) setChallenge(await beginIdentityReview(item.user_id, body));
      else {
        if (Date.parse(challenge.expires_at) <= Date.now()) throw new Error('انتهى إذن التحقق. راجع البيانات وابدأ التحقق مجددًا.');
        const proof = await verifyReview(challenge.id, code);
        setCode('');
        await documentStaffIdentity(item.user_id, body, proof.proof);
        setChallenge(null); setBody(initialBody);
        await refresh();
      }
    } catch (failure) {
      setError(failure instanceof Error ? failure.message : 'تعذّر تأكيد الحفظ. حدّث الحالة قبل إعادة المحاولة.');
      setCode(''); setChallenge(null);
    } finally { setBusy(false); }
  }
  return <section className="space-y-4 rounded-xl border p-4">
    <h2 className="text-xl font-bold">توثيق هوية الموظف قبل الربط الأول</h2>
    <p>سجّل مرجع المقابلة المستقلة ومطابقة الهوية وقناتها المعروفة. الموظف يضيف عامل التحقق بنفسه من حسابه. لا تمنح هذه الخطوة دورًا أو صلاحية استعادة المالك.</p>
    {!enabled && <p role="status">أكمل إعداد عامل حسابك وارفع مانع الإجراءات الحساسة من مساره قبل توثيق موظف آخر.</p>}
    {error && <p role="alert">{error}</p>}
    <button type="button" className="rounded border px-4 py-2" disabled={busy} onClick={() => {
      setBusy(true); setError('');
      void refresh().catch(failure => setError(failure instanceof Error ? failure.message : 'تعذّر التحديث.')).finally(() => setBusy(false));
    }}>تحديث حالات الموظفين</button>
    {!loaded ? <p role="status">جارٍ تحميل الحالات…</p> : items.length === 0 ? <p>لا توجد حسابات موظفين أخرى متاحة.</p> : <form onSubmit={submit} className="space-y-3">
      <label className="block">الموظف<select required className="block w-full rounded border p-2" value={selected} disabled={busy} onChange={event => {
        setSelected(event.target.value); setBody(initialBody); setCode(''); setChallenge(null); setError('');
      }}><option value="">اختر حساب الموظف</option>{items.map(value => <option key={value.user_id} value={value.user_id}>{value.name || value.email} — {value.email}</option>)}</select></label>
      {item?.documented && <div role="status"><p>{item.configured ? 'الهوية موثقة والعامل مربوط.' : 'الهوية موثقة؛ يبدأ الموظف الربط من أمان حسابه.'}</p><p>مرجع الهوية: {item.identity_reference}</p><p>القناة المعروفة: {item.known_channel_reference}</p></div>}
      {item?.recovery_pending && <p role="status">يوجد طلب استعادة قائم. تُراجع حالته من قائمة الاستعادة المستقلة.</p>}
      {item && !item.documented && !item.recovery_pending && <fieldset disabled={busy || !enabled} className="space-y-3">
        <label className="block">مرجع الشخص في سجل الهوية الموثّق<input required maxLength={128} className="block w-full rounded border p-2" value={body.person_reference} onChange={event => change({ person_reference: event.target.value })} /></label>
        <label className="block">مرجع دليل التحقق<input required maxLength={200} className="block w-full rounded border p-2" value={body.evidence_reference} onChange={event => change({ evidence_reference: event.target.value })} /></label>
        <label className="block">مرجع قناة الاتصال المعروفة مسبقًا<input required maxLength={200} className="block w-full rounded border p-2" value={body.known_channel_reference} onChange={event => change({ known_channel_reference: event.target.value })} /></label>
        <label className="block">وسيلة التحقق<select className="block w-full rounded border p-2" value={body.verification_method} onChange={event => change({ verification_method: event.target.value as StaffIdentityBody['verification_method'] })}><option value="known_channel_video">اتصال مرئي بالقناة المعروفة</option><option value="in_person">مقابلة مباشرة</option></select></label>
        <label className="flex gap-2"><input required type="checkbox" checked={body.identity_matched} onChange={event => change({ identity_matched: event.target.checked })} />أؤكد مطابقة الهوية بمراجعة مستقلة وأن الحساب لا يخصني.</label>
        {challenge && <label className="block">رمز تطبيق التحقق للمراجع<input required inputMode="numeric" autoComplete="one-time-code" pattern="[0-9]{6}" maxLength={6} className="block w-full rounded border p-2" value={code} onChange={event => setCode(event.target.value)} /></label>}
        <button className="rounded border px-4 py-2" type="submit">{challenge ? 'تأكيد توثيق الهوية' : 'التحقق من توثيق الهوية'}</button>
      </fieldset>}
    </form>}
  </section>;
}
