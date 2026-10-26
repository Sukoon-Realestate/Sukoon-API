'use client';
import { useEffect, useState } from 'react';
import { ContentItem, ContentPage, contentDetail, contentList, contentTitle } from '../../lib/api/content';

export default function CatalogRelation({ id, kind, value, label, disabled, required, onChange }: {
  id: string; kind: string; value: string; label?: string; disabled: boolean; required: boolean; onChange: (id: string) => void;
}) {
  const [search, setSearch] = useState('');
  const [pageNumber, setPageNumber] = useState(1);
  const [result, setResult] = useState<ContentPage | null>(null);
  const [selected, setSelected] = useState<ContentItem | null>(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  useEffect(() => {
    if (disabled && label) return;
    const controller = new AbortController();
    const timer = setTimeout(() => {
      setLoading(true); setError('');
      void Promise.all([contentList(kind, pageNumber, controller.signal, search), value ? contentDetail(kind, value, controller.signal) : Promise.resolve(null)])
        .then(([list, item]) => {if (!controller.signal.aborted) {setResult(list); setSelected(item);}})
        .catch(e => {if (!controller.signal.aborted) setError(e instanceof Error ? e.message : 'تعذر تحميل الخيارات.');})
        .finally(() => {if (!controller.signal.aborted) setLoading(false);});
    }, 200);
    return () => {clearTimeout(timer); controller.abort();};
  }, [kind, pageNumber, search, value, disabled, label]);
  const rows = result?.results ?? [];
  const inactive = (row: ContentItem) => row.selection_available === false || row.values.active === false || row.values.is_active === false;
  return <div className="space-y-2">
    {!disabled && <input className="block w-full rounded-lg border bg-transparent p-2" aria-label="ابحث في خيارات الكتالوج" value={search} onChange={event => {setSearch(event.target.value); setPageNumber(1);}} />}
    <select id={id} className="block w-full min-w-0 rounded-lg border bg-transparent p-3 disabled:opacity-60" value={value} required={required} disabled={disabled || loading || !!error} onChange={event => onChange(event.target.value)}>
      <option value="">اختر</option>
      {value && !rows.some(row => row.id === value) && <option value={value}>{label || (selected ? contentTitle(selected) : 'جارٍ تحميل الاسم…')}</option>}
      {rows.map(row => <option key={row.id} value={row.id} disabled={inactive(row) && row.id !== value}>{contentTitle(row)}{inactive(row) && ' — متوقف'} · {row.id.slice(0, 8)}</option>)}
    </select>
    {loading && <p role="status">جارٍ تحميل الخيارات…</p>}
    {error && <p role="alert">{error}</p>}
    {!disabled && result && result.total_pages > 1 && <div className="flex gap-3"><button type="button" disabled={loading || pageNumber <= 1} onClick={() => setPageNumber(pageNumber - 1)}>الخيارات السابقة</button><span>{pageNumber} / {result.total_pages}</span><button type="button" disabled={loading || pageNumber >= result.total_pages} onClick={() => setPageNumber(pageNumber + 1)}>الخيارات التالية</button></div>}
  </div>;
}
