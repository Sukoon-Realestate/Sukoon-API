'use client';
import { ContentField, ContentValues, ContentValue } from '../../lib/api/content';

import CatalogRelation from './CatalogRelation';

const control = 'block w-full min-w-0 rounded-lg border bg-transparent p-3 disabled:opacity-60';
export default function ContentFields({ fields, values, labels, existing, disabled, change }: {
  fields: ContentField[]; values: ContentValues; existing: boolean; disabled: boolean;
  labels?: Record<string, string>;
  change: (name: string, value: ContentValue) => void;
}) {
  return <div className="grid min-w-0 gap-4 md:grid-cols-2">{fields.map(field => {
    const locked = disabled || existing && field.fixed;
    const value = values[field.name];
    const id = `content-field-${field.name}`;
    return <div key={field.name} className={`block min-w-0 space-y-2 ${field.type === 'multiline' ? 'md:col-span-2' : ''}`}>
      <label htmlFor={id} className="font-bold">{field.label}{existing && field.fixed && ' (ثابت)'}</label>
      {field.type === 'relation' ? <CatalogRelation key={`${field.name}:${existing}`} id={id} kind={field.relation!} label={labels?.[field.name]} value={String(value ?? '')} required={field.required} disabled={locked} onChange={value => change(field.name, value)} /> : field.type === 'boolean' ? <input id={id} type="checkbox" className="ms-3 h-6 w-6" checked={value === true} disabled={locked} onChange={e => change(field.name, e.target.checked)} />
        : field.type === 'choice' ? <select id={id} className={control} value={String(value ?? '')} required={field.required} disabled={locked} onChange={e => change(field.name, e.target.value)}>
          <option value="">اختر</option>{field.choices.map(option => <option key={option.value} value={option.value}>{option.label}</option>)}
        </select>
          : field.type === 'multiline' ? <textarea id={id} className={control} dir={field.name.endsWith('_en') ? 'ltr' : 'rtl'} rows={6} value={String(value ?? '')} required={field.required} disabled={locked} maxLength={field.max_length ?? undefined} onChange={e => change(field.name, e.target.value)} />
            : <input id={id} className={control} dir={field.name.endsWith('_en') || ['email', 'datetime'].includes(field.type) ? 'ltr' : undefined}
              type={['integer', 'decimal'].includes(field.type) ? 'number' : field.type === 'datetime' ? 'datetime-local' : field.type === 'email' ? 'email' : field.type === 'date' ? 'date' : 'text'}
              step={field.type === 'decimal' ? 'any' : undefined} min={field.type === 'integer' ? 0 : undefined} value={String(value ?? '')} required={field.required} disabled={locked} maxLength={field.max_length ?? undefined}
              onChange={e => change(field.name, field.type === 'integer' ? (e.target.value === '' ? '' : Number(e.target.value)) : e.target.value || (field.type === 'datetime' ? null : ''))} />}
    </div>;
  })}</div>;
}
