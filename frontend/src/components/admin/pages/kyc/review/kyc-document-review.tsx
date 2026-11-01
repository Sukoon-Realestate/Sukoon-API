'use client';

import { KycDocumentDecisions, KycDocumentField } from '@/lib/api/types';

const labels: Record<KycDocumentField, string> = {
  national_id: 'الرقم القومي', front_id_image: 'وجه الهوية',
  back_id_image: 'ظهر الهوية', selfie_image: 'الصورة الشخصية',
};

export function KycDocumentReview({ fields, value, disabled, onChange }: {
  fields: KycDocumentField[];
  value: KycDocumentDecisions;
  disabled: boolean;
  onChange: (value: KycDocumentDecisions) => void;
}) {
  return <fieldset disabled={disabled} className="space-y-4">
    <legend className="font-bold mb-2">المستندات المطلوب تصحيحها</legend>
    <p className="text-sm">عند الرفض يرفع المستخدم المستندات المرفوضة فقط. يحتفظ النظام بالمستندات المقبولة وبنسخة المراجعة السابقة.</p>
    {fields.map(field => <div key={field} className="space-y-2">
      <label className="flex flex-wrap items-center gap-3">
        <span>{labels[field]}</span>
        <select className="min-h-12 border rounded-lg px-3 bg-[var(--input-bg)]" value={value[field]?.status ?? ''} onChange={event => {
          const status = event.target.value;
          if (status === 'approved' || status === 'rejected') onChange({ ...value, [field]: { status, reason: status === 'rejected' ? value[field]?.reason ?? '' : '' } });
        }}>
          <option value="" disabled>اختر قرار المستند</option>
          <option value="approved">مقبول</option>
          <option value="rejected">يحتاج تصحيحًا</option>
        </select>
      </label>
      {value[field]?.status === 'rejected' && <label className="block">
        <span>سبب تصحيح {labels[field]}</span>
        <textarea className="w-full p-3 border rounded-lg bg-[var(--input-bg)]" maxLength={2000} value={value[field]?.reason ?? ''}
          onChange={event => onChange({ ...value, [field]: { status: 'rejected', reason: event.target.value } })} />
      </label>}
    </div>)}
  </fieldset>;
}
