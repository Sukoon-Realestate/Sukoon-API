import { useState } from 'react';
import type { SupportAction, SupportCommand, SupportInformationRequest } from '../../lib/api/support';

const states = { requested: 'معلومات مطلوبة', answer_sent: 'أُرسلت الإجابة وتنتظر مراجعة الدعم', accepted: 'قبلها فريق الدعم', withdrawn: 'سُحب الطلب ولا تلزم إجابة' };
const control = 'rounded-lg border px-4 py-2 disabled:opacity-50';

export default function SupportInformationPanel({ requests, actions, disabled, onCommand }: {
  requests: SupportInformationRequest[]; actions: Record<SupportAction, boolean>; disabled: boolean;
  onCommand: (action: SupportAction, fields?: Partial<SupportCommand>) => Promise<void>;
}) {
  const [prompt, setPrompt] = useState('');
  const [reason, setReason] = useState('');
  return <section className="space-y-3 rounded-xl border p-4">
    <h2 className="text-lg font-bold">المعلومات المطلوبة من صاحب التذكرة</h2>
    <p>إرسال إجابة أو مرفق لا يعني قبوله ولا يغلق التذكرة. راجع الإجابة ثم سجّل قرار المراجعة.</p>
    {requests.map(item => <article key={item.id} className="space-y-2 rounded-lg border p-3">
      <p className="whitespace-pre-wrap break-words">{item.prompt}</p><p role="status">{states[item.status]}</p>
      {item.answer_message_id && <p>مرجع الإجابة في المحادثة: {item.answer_message_id}</p>}
      {!!item.evidence_requirement?.min_attachments && <p>يلزم من صاحب التذكرة مرفق واحد على الأقل وفق سياسة الملفات الخاصة بالدعم.</p>}
      {(item.evidence_versions ?? []).map(version => <div key={version.id} className="rounded border p-2">
        <p>نسخة الدليل {version.version} · {({submitted: 'أُرسلت وتنتظر المراجعة', accepted: 'مقبولة', correction: 'تحتاج تصحيحًا', conflicting: 'متعارضة'} as Record<string, string>)[version.review_status] ?? 'حالة غير معروفة'}</p>
        <p>{version.review_reason}</p>{version.files.some(file => !file.available) && <p role="status">تغيّرت صلاحية بعض الملفات. راجع توفرها قبل اعتماد الدليل.</p>}
      </div>)}
      <div className="flex flex-wrap gap-2">
        {item.status === 'answer_sent' && <>
          {!!item.evidence_requirement?.min_attachments && <button className={control} disabled={disabled || !actions.mark_evidence_conflicting || !reason.trim()} onClick={() => void onCommand('mark_evidence_conflicting', { information_request_id: item.id, information_revision: item.revision, reason: reason.trim() })}>تسجيل تعارض مع الاحتفاظ بالنسخ</button>}
          <button className={control} disabled={disabled || !actions.accept_information} onClick={() => void onCommand('accept_information', { information_request_id: item.id, information_revision: item.revision, reason: reason.trim() || 'قُبلت المعلومات المطلوبة.' })}>قبول الإجابة</button>
          <button className={control} disabled={disabled || !actions.return_information || !reason.trim()} onClick={() => void onCommand('return_information', { information_request_id: item.id, information_revision: item.revision, reason: reason.trim() })}>طلب تصحيح الإجابة</button>
        </>}
        {item.status !== 'withdrawn' && <button className={control} disabled={disabled || !actions.withdraw_information || !reason.trim()} onClick={() => void onCommand('withdraw_information', { information_request_id: item.id, information_revision: item.revision, reason: reason.trim() })}>سحب الطلب</button>}
      </div>
      <details><summary>سجل الطلب والمراجعة</summary>{item.history.map(row => <p key={row.id} className="break-words">{new Date(row.created_at).toLocaleString('ar')} · {row.reason}</p>)}</details>
    </article>)}
    {actions.request_information && <>
      <label className="block">المعلومات المطلوبة<textarea className="w-full rounded border p-3" maxLength={2000} value={prompt} disabled={disabled} onChange={event => setPrompt(event.target.value)} /></label>
      <button className={control} disabled={disabled || !prompt.trim()} onClick={() => void onCommand('request_information', { prompt: prompt.trim(), reason: reason.trim() || 'طلب معلومات إضافية من صاحب التذكرة.' })}>إرسال طلب المعلومات</button>
      {actions.request_evidence && <button className={control} disabled={disabled || !prompt.trim()} onClick={() => void onCommand('request_evidence', { prompt: prompt.trim(), reason: reason.trim() || 'طلب دليل خاص بهذه التذكرة.' })}>طلب دليل من صاحب التذكرة</button>}
    </>}
    {requests.length > 0 && <label className="block">سبب المراجعة أو التصحيح أو السحب<textarea className="w-full rounded border p-3" maxLength={1000} value={reason} disabled={disabled} onChange={event => setReason(event.target.value)} /></label>}
  </section>;
}
